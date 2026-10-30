"""Render a post-evaluation AI review without changing predictions or human scores.

Qualitative judgments are authored separately by Codex in the notes JSON.
This script verifies their quoted evidence and recomputes exact-match counts;
it does not call a model, adjudicate clinical meaning, or modify the holdout.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/extraction/llm_v3"
KINDS = {"Measurement", "Value", "Temporal"}
LABELS = {"original_llm": "旧版 LLM", "llm_v3": "新版 LLM + NER"}
VERDICTS = {
    "exact": "类型及完整边界匹配",
    "boundary_overlap": "同类型重叠，边界不匹配",
    "type_overlap": "与其他目标类型重叠",
    "no_target_overlap": "未匹配目标金标准",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entity_key(entity):
    return entity["kind"], tuple(tuple(span) for span in entity["spans"])


def overlaps(prediction, gold):
    return any(max(prediction["start"], a) < min(prediction["end"], b)
               for a, b in gold["spans"])


def metrics(tp, fp, fn):
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}


def score(items, gold, source, annotations):
    expected = {entity_key(g) for g in gold}
    predicted = {(p["kind"], ((p["start"], p["end"]),)) for p in items}
    checks = []
    for p in items:
        if not (0 <= p["start"] < p["end"] <= len(source)):
            raise ValueError("Prediction extends beyond the reviewed source")
        if source[p["start"]:p["end"]] != p["evidence"]:
            raise ValueError("Prediction evidence does not match source")
        key = (p["kind"], ((p["start"], p["end"]),))
        near = [g for g in gold if overlaps(p, g)]
        if key in expected:
            verdict = "exact"
        elif any(g["kind"] == p["kind"] for g in near):
            verdict = "boundary_overlap"
        elif near:
            verdict = "type_overlap"
        else:
            verdict = "no_target_overlap"
        checks.append({**p, "source_quote_verified": True,
                       "benchmark_verdict": verdict, "overlapping_target_gold": near,
                       "other_exact_annotation_types": sorted({
                           g["kind"] for g in annotations
                           if tuple(tuple(s) for s in g["spans"]) == key[1]
                           and g["kind"] != p["kind"]})})
    return {"metrics": metrics(len(predicted & expected), len(predicted - expected),
                               len(expected - predicted)),
            "exact_document": expected == predicted,
            "error_patterns": dict(Counter(c["benchmark_verdict"] for c in checks)),
            "prediction_checks": checks,
            "missing_gold": [g for g in gold if entity_key(g) not in predicted]}


def shown(value):
    return json.dumps(value, ensure_ascii=False).replace("|", "\\|")


def main():
    packet_path = OUT / "human_review_packet.json"
    packet_hash = digest(packet_path)
    packet = json.loads(packet_path.read_text())
    notes = json.loads((OUT / "ai_second_review_notes.json").read_text())
    keys = {c["case_id"]: c for c in json.loads((OUT / "human_review_key.json").read_text())}
    note_map = {c["case_id"]: c for c in notes["cases"]}
    if len(note_map) != 12 or set(note_map) != {c["case_id"] for c in packet["cases"]}:
        raise ValueError("AI notes must cover all 12 preselected cases exactly once")
    freeze = json.loads((OUT / "freeze.json").read_text())
    evaluation = json.loads((OUT / "fresh_evaluation.json").read_text())
    for name, expected in freeze["code_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Frozen file changed: {name}")
    if digest(OUT / "fresh_predictions.json") != evaluation["predictions_sha256"]:
        raise ValueError("Frozen predictions changed")
    if digest(OUT / "freeze.json") != evaluation["freeze_sha256"]:
        raise ValueError("Freeze manifest changed")
    totals = {name: Counter() for name in LABELS}
    cases = []
    with zipfile.ZipFile(ROOT / "data/annotations/chia/chia_with_scope.zip") as archive:
        for case in packet["cases"]:
            source = case["source"]
            if not archive.read(case["record_id"] + ".txt").decode().startswith(source):
                raise ValueError("Review source differs from the archived source prefix")
            note = note_map[case["case_id"]]
            for quote in note["evidence_quotes"]:
                if quote not in source:
                    raise ValueError(f"Unsupported AI-review evidence: {case['case_id']} {quote!r}")
            annotations = []
            for line in archive.read(case["record_id"] + ".ann").decode().splitlines():
                if not line.startswith("T"):
                    continue
                fields = line.split("\t")
                kind, offsets = fields[1].split(" ", 1)
                spans = [list(map(int, part.split())) for part in offsets.split(";")]
                if max(b for _, b in spans) <= len(source):
                    annotations.append({"kind": kind, "spans": spans,
                                        "source_fragments": [source[a:b] for a, b in spans]})
            gold = [g for g in annotations if g["kind"] in KINDS]
            reviewed = {"case_id": case["case_id"], "record_id": case["record_id"],
                        "source": source, "gold": gold, "ai_notes": note}
            for label in ("A", "B"):
                system = keys[case["case_id"]][label]
                result = score(case[label], gold, source, annotations)
                reviewed[label] = {"system": system, **result}
                totals[system].update({k: result["metrics"][k] for k in ("tp", "fp", "fn")})
                totals[system]["exact_documents"] += result["exact_document"]
            cases.append(reviewed)
    aggregate = {system: {**metrics(c["tp"], c["fp"], c["fn"]),
                          "exact_documents": c["exact_documents"]}
                 for system, c in totals.items()}
    review = {"title": "AI 二次复核：12 份冻结样本", "reviewer": "Codex (AI)",
              "reviewed_at": datetime.now(timezone.utc).isoformat(), "review_round": 2,
              "review_type": "AI_secondary_review", "is_human_review": False,
              "reviewed_cases": len(cases), "blinded": False,
              "method": notes["method"], "scope": "Frozen CHIA matched-prefix A/B outputs",
              "human_review_completed_cases": packet["completed_cases"],
              "clinical_eligibility_logic_validated": False,
              "input_sha256": {p.name: digest(p) for p in [packet_path, OUT / "ai_second_review_notes.json",
                                OUT / "human_review_key.json", OUT / "fresh_evaluation.json", OUT / "fresh_predictions.json"]},
              "verification": {"frozen_code_unchanged": True, "predictions_unchanged": True,
                               "ai_evidence_quotes_verified": sum(len(n["evidence_quotes"]) for n in note_map.values()),
                               "human_packet_unchanged": digest(packet_path) == packet_hash},
              "aggregate": aggregate, "cases": cases}
    lines = ["# AI 二次复核：12 份冻结样本", "",
             "**复核者：Codex（AI）。已复核 12/12；真人审核仍为 0/12。**", "",
             "本报告保留人工审核流程，另行记录 AI 对原文、A/B 输出和 CHIA 标注的逐条复核。这里已揭示 A/B 系统身份，属于非盲法 AI 复核。类型和边界的数字是对既有金标准的脚本复算；文字解释是 AI 判断，不能当作真人或独立临床签核。", "",
             "复核只使用冻结后的预测，没有改动模型、提示词、金标准或实验分数。原人工审核表的身份、时间和评分字段保持原状。", "",
             "Markdown 展示统一换行并省略行尾空格；字符位置以 JSON 中保留的原始文本为准。", "",
             "## 这 12 份样本的核对结果", "",
             "| 系统 | 正确 TP | 误报 FP | 遗漏 FN | 精确率 | 召回率 | 精确片段 F1 | 完全匹配文档 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for system, m in aggregate.items():
        lines.append(f"| {LABELS[system]} | {m['tp']} | {m['fp']} | {m['fn']} | {m['precision']:.1%} | {m['recall']:.1%} | {m['f1']:.1%} | {m['exact_documents']}/12 |")
    lines += ["", "这是预先抽取的 12 份复核子集，不能代替 [100 份文档的主结果](summary.md)。完全匹配要求整个实体集合一致，包含无目标实体的文档。空金标准与空预测的 F1 按评分实现记为 0，另用完全匹配标志表示该文档成功。所有保留片段均能回溯到原文，但原文匹配不等于语义正确。", "",
              "主要问题：疾病/观察结果与 Measurement 混淆；数值、单位及时间窗截断；完整片段与短片段同时出现；Multiplier、Observation 等任务外标签被强制分配到三个目标类别。新版在 review-02、review-10 的精确 F1 低于旧版。否定、AND/OR、例外与患者资格没有得到验证。", "",
              "[保留的真人审核表](human_review.md) · [未填写的人类评分记录](human_review_packet.json) · [机器可读 AI 二次复核](ai_second_review.json)", ""]
    for case in cases:
        display_source = "\n".join(line.rstrip() for line in case["source"].splitlines())
        lines += [f"## {case['case_id']} — {case['record_id']}", "", "```text", display_source, "```", "",
                  "| 输出 | 系统 | TP / FP / FN | 精确片段 F1 | 完全匹配 |",
                  "|---|---|---|---:|---|"]
        for label in ("A", "B"):
            result = case[label]; m = result["metrics"]
            lines.append(f"| {label} | {LABELS[result['system']]} | {m['tp']} / {m['fp']} / {m['fn']} | {m['f1']:.1%} | {'是' if result['exact_document'] else '否'} |")
        note = case["ai_notes"]
        lines += ["", "**AI 类型复核：** " + note["finding"], "",
                  "**边界与遗漏：** " + note["boundary_and_omissions"], "",
                  "**上下文限制：** " + note["context"], ""]
        for label in ("A", "B"):
            result = case[label]
            lines += [f"### {label} 逐片段核对", "", "| 类型 | 字符位置 | 原文片段 | 金标准匹配 |", "|---|---|---|---|"]
            for item in result["prediction_checks"]:
                verdict = VERDICTS[item["benchmark_verdict"]]
                if item["other_exact_annotation_types"]:
                    verdict += "；完整标注类型：" + ", ".join(item["other_exact_annotation_types"])
                lines.append(f"| {item['kind']} | {item['start']}:{item['end']} | {shown(item['evidence'])} | {verdict} |")
            if not result["prediction_checks"]:
                lines.append("| — | — | 无保留输出 | — |")
            lines += ["", "遗漏的目标实体：", ""]
            lines += [f"- {g['kind']} {g['spans']}: {shown(g['source_fragments'])}" for g in result["missing_gold"]] or ["- 无。"]
            lines.append("")
    lines += ["## 后续改进顺序（尚未运行）", "",
              "1. 在开发集补充标签排除规则与困难反例，区分 Person、Condition、Observation、Multiplier 与三个目标标签，避免见到医学词或数字就强制分类。保留语料差异记录，不事后改测试金标准。",
              "2. 以同一开发集上的 NER 为基线，比较候选重排、按类型筛选和边界校正，检验 LLM 是否有独立增益。当前直接取并集增加了误报，不能因召回提高就默认采用。",
              "3. 在开发集验证完整单位/运算符边界、重复短片段去重及词内子串拒绝；另测受约束的 JSON 输出和更合理的生成预算。规则需检查缩写与标点反例，不能只针对这 12 份样本修补。",
              "4. 将否定、条件关系、时间比较与例外作为单独标注和评估的任务。完成开发后再冻结方案，用新的未使用样本评估，另行记录真实人工审核。", "",
              "## 范围与来源", "",
              "标签冲突依据原始 CHIA 标注记录，不把与语料不一致直接解释为临床事实错误。可能的标注不一致和可疑源单位保持原样，不在复核后修改测试答案。下一轮开发需要新的冻结方案与评估样本。", "",
              "原文和金标准来自 Kury et al., CHIA v2，CC BY 4.0：[论文](https://doi.org/10.1038/s41597-020-00620-0) · [数据](https://doi.org/10.6084/m9.figshare.11855817.v2)。AI 解释、模型预测和本复核表为派生成果。"]
    (OUT / "ai_second_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
    (OUT / "ai_second_review.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"reviewed_cases": len(cases), "aggregate": aggregate, "verification": review["verification"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
