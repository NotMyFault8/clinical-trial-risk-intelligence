"""Render a post-evaluation AI review without changing predictions or gold.

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
LABELS = {"original_llm": "Original LLM", "llm_v3": "Revised LLM + NER"}
VERDICTS = {
    "exact": "exact type and full boundary match",
    "boundary_overlap": "same type overlaps, but boundary differs",
    "type_overlap": "overlaps an entity with another target type",
    "no_target_overlap": "no overlap with target gold",
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
    previous = json.loads((OUT / "ai_second_review.json").read_text())
    notes = json.loads((OUT / "ai_second_review_notes.json").read_text())
    note_map = {c["case_id"]: c for c in notes["cases"]}
    if len(note_map) != 12 or set(note_map) != {c["case_id"] for c in previous["cases"]}:
        raise ValueError("AI notes must cover all 12 preselected cases exactly once")
    freeze = json.loads((OUT / "freeze.json").read_text())
    evaluation = json.loads((OUT / "fresh_evaluation.json").read_text())
    archive_path = ROOT / "data/annotations/chia/chia_with_scope.zip"
    archive_hash = digest(archive_path)
    expected_archive_hash = json.loads((ROOT / "configs/chia_source.json").read_text())["sha256"]
    if archive_hash != expected_archive_hash:
        raise ValueError("CHIA archive hash differs from the pinned source manifest")
    for name, expected in freeze["code_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Frozen file changed: {name}")
    if digest(OUT / "fresh_predictions.json") != evaluation["predictions_sha256"]:
        raise ValueError("Frozen predictions changed")
    if digest(OUT / "freeze.json") != evaluation["freeze_sha256"]:
        raise ValueError("Freeze manifest changed")
    totals = {name: Counter() for name in LABELS}
    cases = []
    with zipfile.ZipFile(archive_path) as archive:
        for case in previous["cases"]:
            source = case["source"]
            if not archive.read(case["record_id"] + ".txt").decode().startswith(source):
                raise ValueError("AI review source differs from the archived source prefix")
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
            gold_keys = {entity_key(g) for g in gold}
            prior_gold_keys = {entity_key(g) for g in case["gold"]}
            if gold_keys != prior_gold_keys:
                raise ValueError(f"Gold annotations changed for {case['case_id']}")
            reviewed = {"case_id": case["case_id"], "record_id": case["record_id"],
                        "source": source, "gold": gold, "ai_notes": note}
            for label in ("A", "B"):
                prior = case[label]
                system = prior["system"]
                if system not in LABELS:
                    raise ValueError(f"Unexpected system mapping in {case['case_id']} {label}")
                items = [{"kind": item["kind"], "start": item["start"],
                          "end": item["end"], "evidence": item["evidence"]}
                         for item in prior["prediction_checks"]]
                result = score(items, gold, source, annotations)
                for metric in ("tp", "fp", "fn"):
                    if result["metrics"][metric] != prior["metrics"][metric]:
                        raise ValueError(f"Recomputed {metric} changed for {case['case_id']} {label}")
                reviewed[label] = {"system": system, **result}
                totals[system].update({k: result["metrics"][k] for k in ("tp", "fp", "fn")})
                totals[system]["exact_documents"] += result["exact_document"]
            cases.append(reviewed)
    aggregate = {system: {**metrics(c["tp"], c["fp"], c["fn"]),
                          "exact_documents": c["exact_documents"]}
                 for system, c in totals.items()}
    review = {"title": "AI secondary review: 12 frozen cases", "reviewer": "Codex (AI)",
              "reviewed_at": datetime.now(timezone.utc).isoformat(), "review_round": 2,
              "review_type": "AI_secondary_review", "reviewed_cases": len(cases),
              "method": notes["method"], "scope": "Frozen CHIA matched-prefix A/B outputs",
              "clinical_eligibility_logic_validated": False,
              "input_sha256": {p.name: digest(p) for p in [OUT / "ai_second_review_notes.json",
                                OUT / "freeze.json", OUT / "fresh_manifest.json", OUT / "fresh_evaluation.json",
                                OUT / "fresh_predictions.json", archive_path]},
              "verification": {"frozen_code_unchanged": True, "predictions_unchanged": True,
                               "ai_evidence_quotes_verified": sum(len(n["evidence_quotes"]) for n in note_map.values()),
                               "source_annotations_revalidated": True, "pinned_archive_hash_verified": True},
              "aggregate": aggregate, "cases": cases}
    lines = ["# AI Secondary Review: 12 Frozen Cases", "",
             "**Reviewer: Codex (AI). Cases reviewed: 12/12.**", "",
             "This report records an AI review of the source text, A/B outputs and CHIA annotations. System identities are disclosed. Type and boundary counts are recomputed from the existing gold by script; written interpretations are AI judgments and do not constitute independent clinical validation.", "",
             "The review used frozen predictions and did not change the model, prompts, gold or experiment scores.", "",
             "Markdown display normalizes line endings and trims trailing whitespace. Character offsets refer to the original text preserved in the JSON record.", "",
             "## Results for the 12 reviewed cases", "",
             "| System | Correct TP | False positives FP | Misses FN | Precision | Recall | Exact span F1 | Completely exact documents |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for system, m in aggregate.items():
        lines.append(f"| {LABELS[system]} | {m['tp']} | {m['fp']} | {m['fn']} | {m['precision']:.1%} | {m['recall']:.1%} | {m['f1']:.1%} | {m['exact_documents']}/12 |")
    lines += ["", "This prespecified 12-document subset does not replace the [100-document primary result](summary.md). A completely exact document must have an exact predicted entity set, including documents with no target gold. The scoring implementation assigns F1=0 when both gold and predictions are empty; the separate exact-document flag shows whether the empty sets match. All retained spans can be traced to the source, but quotation support does not establish semantic correctness.", "",
              "Main errors include disease or observation terms mislabeled as Measurement; truncated values, units and time windows; duplicate short and complete spans; and forcing labels outside the three target categories, such as Multiplier and Observation, into a target category. The revised system has lower exact F1 than the original on review-02 and review-10. Negation, AND/OR scope, exceptions and patient eligibility were not evaluated.", "",
              "[Machine-readable AI secondary review](ai_second_review.json)", ""]
    for case in cases:
        display_source = "\n".join(line.rstrip() for line in case["source"].splitlines())
        lines += [f"## {case['case_id']} — {case['record_id']}", "", "```text", display_source, "```", "",
                  "| Output | System | TP / FP / FN | Exact span F1 | Completely exact |",
                  "|---|---|---|---:|---|"]
        for label in ("A", "B"):
            result = case[label]; m = result["metrics"]
            lines.append(f"| {label} | {LABELS[result['system']]} | {m['tp']} / {m['fp']} / {m['fn']} | {m['f1']:.1%} | {'Yes' if result['exact_document'] else 'No'} |")
        note = case["ai_notes"]
        lines += ["", "**AI type review:** " + note["finding"], "",
                  "**Boundaries and omissions:** " + note["boundary_and_omissions"], "",
                  "**Context and limitations:** " + note["context"], ""]
        for label in ("A", "B"):
            result = case[label]
            lines += [f"### {label} span-by-span comparison", "", "| Type | Character offsets | Source text | Gold comparison |", "|---|---|---|---|"]
            for item in result["prediction_checks"]:
                verdict = VERDICTS[item["benchmark_verdict"]]
                if item["other_exact_annotation_types"]:
                    verdict += "; full annotation type: " + ", ".join(item["other_exact_annotation_types"])
                lines.append(f"| {item['kind']} | {item['start']}:{item['end']} | {shown(item['evidence'])} | {verdict} |")
            if not result["prediction_checks"]:
                lines.append("| — | — | No retained predictions | — |")
            lines += ["", "Missed target entities:", ""]
            lines += [f"- {g['kind']} {g['spans']}: {shown(g['source_fragments'])}" for g in result["missing_gold"]] or ["- None."]
            lines.append("")
    lines += ["## Recommended next steps (not yet run)", "",
              "1. Add label-exclusion rules and hard negative examples to development data. Distinguish Person, Condition, Observation and Multiplier from the three target labels instead of assigning every medical term or number to a target category. Record corpus disagreements without editing test gold after evaluation.",
              "2. Use NER on the same development folds as the baseline. Compare candidate reranking, type filtering and boundary correction to test whether the LLM contributes independently. The current union adds false positives and should not be selected by recall alone.",
              "3. On development data, evaluate complete unit/operator boundaries, duplicate short-span removal and rejection of substrings inside words. Also test constrained JSON output and an appropriate generation budget. Check rules against abbreviation and punctuation counterexamples instead of patching only these 12 cases.",
              "4. Annotate and evaluate negation, conditional relations, temporal comparisons and exceptions as separate tasks. Freeze a new protocol after development and evaluate it on a new unused sample.", "",
              "## Scope and sources", "",
              "Type comparisons follow the original CHIA annotations; disagreement with the corpus is not automatically a clinical error. Potential annotation issues and suspicious source units are retained, and test gold is not changed after review. Further development requires a new freeze and evaluation sample.", "",
              "Source text and gold annotations are from Kury et al., CHIA v2, CC BY 4.0: [paper](https://doi.org/10.1038/s41597-020-00620-0) · [dataset](https://doi.org/10.6084/m9.figshare.11855817.v2). AI interpretations, model predictions and this review are derived work."]
    (OUT / "ai_second_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
    (OUT / "ai_second_review.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"reviewed_cases": len(cases), "aggregate": aggregate, "verification": review["verification"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
