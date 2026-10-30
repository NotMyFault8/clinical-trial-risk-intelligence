"""Render measured extraction results and an unfilled human review worksheet."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/extraction/llm_v3"


def percent(value):
    return f"{value:.1%}"


def main():
    result = json.loads((OUT / "fresh_evaluation.json").read_text())
    protocol = json.loads((OUT / "freeze.json").read_text())
    manifest = json.loads((OUT / "fresh_manifest.json").read_text())
    review = json.loads((OUT / "human_review_packet.json").read_text())
    ai_path = OUT / "ai_second_review.json"
    ai_review = json.loads(ai_path.read_text()) if ai_path.exists() else None
    lines = ["# Local LLM extraction experiment — 2026-10-30", "",
             "**Research result; semantic release remains withheld. Real human review is pending.**", "",
             f"A new CHIA holdout contains {manifest['records']} documents / {manifest['trials']} trials / {manifest['groups']} near-duplicate groups, excluded from the historical 205 used trials. Selection used source text only. Model/prompt/code were frozen before opening these annotations. Both primary systems receive the same original 1,800-character maximum prefix.", "",
             f"Selected system: Qwen {result['model']}, `{result['mode']}` output mode, `{result['fusion']}` fusion; criterion-aware source windows, development-trained token NER and lexicon, numerical/temporal candidates, and two training-only retrieved examples. No LLM fine-tuning or hosted API calls. Model and LLM-only versus NER-union policy are selected by grouped five-fold development exact F1. The fresh holdout is evaluated once.", "",
             "## Same-input primary comparison", "",
             "| System | Document schema valid | Precision | Recall | Exact span F1 | Completely exact documents |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, label in (("original_llm", "Original Qwen 1.5B"), ("llm_v3", "New LLM pipeline"),
                        ("llm_only", "New LLM before optional NER union"), ("token_ner", "Token NER without LLM"), ("rules", "Regex rules")):
        score = result["scores"][name]["matched_prefix"]
        m = score["micro"]
        lines.append(f"| {label} | {percent(score['document_schema_valid_rate'])} | {percent(m['precision'])} | {percent(m['recall'])} | {percent(m['f1'])} | {score['exact_documents']}/{score['records']} |")
    operating = result["operating"]["matched_prefix"]
    lines += ["", f"Raw LLM request schema validity: {operating['valid_requests']}/{operating['requests']} ({percent(operating['raw_request_schema_valid_rate'])}). Unsupported quotes rejected: {operating['rejected_quote_count']}; accepted quote entries with repeated local occurrences: {operating['repeated_local_quote_count']}. A document passes format checks only when all its LLM requests pass.", "",
              "Schema validity checks output shape, not correct clinical meaning. Exact F1 requires both the correct entity type and every character boundary. Nested and discontinuous gold remain in the denominator. Completely exact documents require the whole predicted entity set to equal gold; empty-gold documents are included.", "",
              "The new quote protocol permits more than six entities per type. Repeated exact quotations map to all local source occurrences, then overlapping-window duplicates are removed. This can recover repeated mentions or introduce false positives. Unsupported quotes are rejected; valid JSON with a rejected quote remains schema-valid, matching the original metric definition. No schema repair is used. If union is selected, deterministic NER spans are explicitly included even for partial LLM failures; their inclusion never changes a failed document to schema-valid. The LLM-only and NER-only rows expose the contribution of each component.", "",
              "## Per-type primary results", "", "| Type | TP | FP | FN | Precision | Recall | Exact F1 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for kind, m in result["scores"]["llm_v3"]["matched_prefix"]["per_type"].items():
        lines.append(f"| {kind} | {m['tp']} | {m['fp']} | {m['fn']} | {percent(m['precision'])} | {percent(m['recall'])} | {percent(m['f1'])} |")
    lines += ["", "## Full-text secondary result", "",
              "| System | Schema valid | Precision | Recall | Exact F1 |", "|---|---:|---:|---:|---:|"]
    for name, label in (("original_llm", "Original, limited to prefix"), ("llm_v3", "New, full text"), ("token_ner", "Token NER, full text")):
        score = result["scores"][name]["full_text"]
        m = score["micro"]
        lines.append(f"| {label} | {percent(score['document_schema_valid_rate'])} | {percent(m['precision'])} | {percent(m['recall'])} | {percent(m['f1'])} |")
    discrepancies = sum(len(r["entities"]) for r in result.get("gold_offset_discrepancies", []))
    lines += ["", "This secondary comparison includes all source annotations. The original system still sees only its fixed prefix, so outside-prefix omissions count against it. The primary table is the controlled same-input comparison.", "",
              f"Fresh target-annotation text/offset discrepancies: {discrepancies}. Published offsets are retained; no gold corrections or exclusions were made after scoring.", "",
              "## Uncertainty and release", ""]
    for metric in ("precision", "f1"):
        low, high = result["paired_bootstrap"][metric]["delta_95_percentile_interval"]
        lines.append(f"- Paired {metric} difference, new minus original: 95% group-bootstrap interval [{low * 100:.2f}, {high * 100:.2f}] percentage points (2,000 resamples; 50 groups).")
    lines += ["", f"All three publication-improvement checks passed: **{result['improved_on_all_three']}**. Semantic release passed: **{result['semantic_release_passed']}**. These are different decisions: publishing measured research improvement does not authorize clinical use.", "",
              "Precision's interval includes zero, so its higher point estimate does not establish a reliable precision improvement. The selected LLM + NER union also falls below token NER alone on this fresh sample (36.3% versus 37.7% exact F1); completely exact documents decline from 8/100 for the original LLM to 7/100. Selection was frozen on development, so this result is not used to switch the reported winner after testing.", "",
              "Unchanged semantic thresholds: schema >=98%, precision >=90%, exact F1 >=65%, and target-cohort human semantic review. Gate results: `" + json.dumps(result["release_checks"]) + "`.", "",
              "## Development experiments and failure analysis", "",
              "| Variant | Schema valid | Precision | Exact F1 |", "|---|---:|---:|---:|"]
    for path in sorted(OUT.glob("development_*.json")):
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or "llm" not in data:
            continue
        score = data["llm"]["matched_prefix"]
        lines.append(f"| {path.stem} | {percent(score['document_schema_valid_rate'])} | {percent(score['micro']['precision'])} | {percent(score['micro']['f1'])} |")
    lines += ["", "The candidate-ID format produced invalid IDs, conflicting assignments and weak exact-boundary accuracy; the incomplete 7B ID pilot is retained but excluded from selection. Quoted strings were easier for the local models. Development-only annotation inspection also found 59 Person annotations and 2 context-dependent Value annotations among the checked age/sex descriptors, with no Measurement annotations. This exposed the original prompt's incorrect treatment of the word age as Measurement. Age bounds remain Value.", "",
              "Earlier full-development token NER OOF F1 was 31.5%; the three-epoch BiomedBERT baseline was 19.9%. Those earlier scores used all source gold, so they must not be directly compared with the prefix table. The token-NER row above is rerun on the same new sample and scope. Rule-parser and Boolean-link counts in earlier experiments were coverage measurements, not semantic accuracy.", "",
              "## Human review and AI inspection", "",
              f"Real human cases completed: **{review['completed_cases']}/{len(review['cases'])}**. Status: `{review['status']}`. The [worksheet](human_review.md) and [JSON score sheet](human_review_packet.json) contain 12 preselected trial documents with A/B outputs. Reviewer identity, expertise, timestamps and judgments remain blank until a person supplies them. A separate [key](human_review_key.json) reveals model assignment; consult it after scoring. Output differences may compromise blinding.", "",
              (f"**AI secondary review: {ai_review['reviewed_cases']}/12 cases completed by Codex (AI).** The [detailed review](ai_second_review.md) checks every A/B span and lists omissions, type/boundary errors and context limitations; [structured evidence](ai_second_review.json) includes exact counts and input hashes. This is an unblinded AI review, not a human or independent clinical sign-off. The human worksheet is retained and its score fields remain unfilled. Earlier limited inspection is retained in `ai_review.json`." if ai_review else "AI secondary review has not yet been recorded."), "",
              "Published CHIA expert annotations provide the benchmark gold; they are not a new human review of these model outputs. A CHIA review also does not satisfy the separate target-cohort clinical review gate. The AI review does not validate negation, Boolean scope or patient eligibility decisions, and does not modify the frozen predictions or gold.", "",
              "## Reproduction and evidence", "",
              "See [the protocol](../../../docs/extraction_v3_protocol.md), [freeze](freeze.json), [fresh manifest](fresh_manifest.json), [measured results](fresh_evaluation.json), [predictions](fresh_predictions.json), [errors](fresh_errors.json), and [development label audit](development_label_audit.json). Local raw model requests/responses stay in ignored `artifacts/extraction_v3_cache/`; predictions retain cache keys. The evaluation JSON records exact runtime versions, hashes, token counts and generation timings. Cached durations describe original generation, not a new latency benchmark.", "",
              "CHIA v2: Kury et al., [paper](https://doi.org/10.1038/s41597-020-00620-0), [dataset](https://doi.org/10.6084/m9.figshare.11855817.v2), CC BY 4.0. Source and annotation text in these review artifacts are attributed to this dataset; model predictions and selection are our derived annotations. Design reference: [Clinical-Trial-Parser](https://github.com/facebookresearch/Clinical-Trial-Parser/tree/03ea0d3f5efe7d1bee713d05bb026201230d9409).", "",
              "This is one finite public-corpus holdout. Pretraining contamination and paraphrase overlap cannot be excluded. It does not establish prospective generalization, correct normalized units, negation/Boolean scope, patient eligibility decisions, or target-cohort clinical validity."]
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    worksheet = ["# Human extraction review worksheet", "", "Status: pending. These are unfilled forms, not completed human judgments.", "",
                 "CHIA v2 source text: Kury et al., https://doi.org/10.6084/m9.figshare.11855817.v2, CC BY 4.0.", "",
                 "For display, this Markdown normalizes source line endings and trailing whitespace. Offsets refer to the unchanged original source in human_review_packet.json.", "",
                 "For each case, record your name/expertise/date, judge each A/B span's type and complete boundary, list missed entities, and check source context/negation. Avoid the separate key until scoring is frozen. Return scores in human_review_packet.json or as numbered notes.", ""]
    for case in review["cases"]:
        display_source = "\n".join(line.rstrip() for line in case["source"].splitlines())
        worksheet += [f"## {case['case_id']} — {case['record_id']}", "", "Source:", "", "```text", display_source, "```", ""]
        for label in ("A", "B"):
            worksheet += [f"### {label}", ""]
            worksheet += [f"- {item['kind']} [{item['start']}:{item['end']}]: {json.dumps(item['evidence'], ensure_ascii=False)}" for item in case[label]] or ["- No retained predictions."]
            worksheet.append("")
        worksheet += ["Reviewer: ____  Expertise: ____  Date: ____", "", "A: correct types ___ / total ___; correct boundaries ___ / total ___", "", "B: correct types ___ / total ___; correct boundaries ___ / total ___", "", "Misses/context errors/preference: ____", ""]
    (OUT / "human_review.md").write_text("\n".join(worksheet).rstrip() + "\n")
    print("Wrote summary.md and unfilled human_review.md")


if __name__ == "__main__":
    main()
