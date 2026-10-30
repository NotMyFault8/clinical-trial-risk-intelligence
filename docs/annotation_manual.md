# Extraction annotation and release manual

## Scope

The implemented task extracts **Measurement, Value and Temporal entity spans**.
These are auditable components of eligibility constraints, not a complete logical
representation. Neither clinical negation scope, measurement/value relations,
age-bound normalization, units normalization nor patient eligibility is validated.
Do not substitute entity counts for a faithful executable eligibility rule.

The external gold standard is Kury et al., *Chia, a large annotated corpus of
clinical trial eligibility criteria*, Scientific Data (2020),
https://doi.org/10.1038/s41597-020-00620-0. The pinned dataset is version 2,
https://doi.org/10.6084/m9.figshare.11855817.v2, CC BY 4.0. It contains expert
annotations published by its authors. This project did not hire annotators or
claim a new independent clinical review. Dataset and archive hashes are retained
under `data/annotations/chia/source.json` (large/raw data are untracked).

## Sampling and isolation

The sampling and output-cap details below describe the historical v1 benchmark.
The [2026-10-30 V3 protocol](extraction_v3_protocol.md) separately freezes 50
unused groups / 100 documents, permits more than six quotations per category,
maps repeated local quotations to every exact occurrence, and reports a NER-union
ablation. It preserves the same exact type/offset metric and release gates. V3
uses development-only retrieved examples; the original prompt uses synthetic
examples. Its [12-case AI secondary review](../reports/extraction/llm_v3/ai_second_review.md)
is an AI review of the benchmark outputs and does not establish clinical validity.

Group inclusion and exclusion files by NCT ID. Before partitioning, connect trial
texts with >=0.9 cosine similarity of fixed hashed character 4–5 grams. Keep each
connected component in one split. Sort groups by SHA256 of `chia-v1:<group ID>`.
The first 50 groups are development; the next 150 are final test. The rest are
unused. This yields 50 development trials and 155 test trials because some test
groups contain near-duplicates. Near-duplicate detection is approximate and does
not rule out all paraphrase overlap or pretrained-model contamination.

Only development annotations guide model/prompt decisions. The predictive 2021
holdout is a different evaluation: CHIA scores do not measure risk discrimination.
Prompt examples are synthetic. NCT IDs and outcome labels never enter prompts.

## Boundary rules

- Measurement is the label of a test, characteristic or clinical scale, excluding
  its value. A diagnosis is not automatically a measurement.
- Value includes a numerical or categorical result/cutoff attached to a
  measurement. Copy operators and units if present; do not invent them. An age
  range is Value, not a temporal washout window.
- Temporal covers durations and relative timing. Preserve words such as “before”,
  “after”, and “prior to” where they are in the annotated span.
- Preserve source characters and offsets, including original line endings.
  Whitespace normalization can invalidate the published offsets.
- Model output contains at most six strings of each type from a maximum 1,800-
  character prefix. Every valid span must occur exactly once in that prefix.
  Repeated ambiguous strings, unsupported strings, extra/duplicate JSON keys and
  invalid types are rejected. Partial results and failures remain explicit.
- The prefix budget and six-span cap limit recall. Report gold beyond the prefix
  separately. Include discontinuous gold within the prefix in the recall
  denominator: a contiguous-only extractor cannot silently omit hard cases.

## Metrics and interpretation

Primary extraction metric: exact entity type plus complete character-offset match,
micro and per-type precision/recall/F1. Exact boundary scoring is intentionally
strict. Report invalid schema, rejected evidence, abstention/failure, token usage,
amortized batch throughput and latency. Retained exact source spans establish
quotation support, not correct clinical meaning or entity type. Published entity
labels are not normalized operator/unit reference labels; no such accuracy claim.

Compare with a deterministic regex extractor on the same visible text and gold.
The small 1.5B development pilot is preserved, including its poor results. A
larger 7B model and revised prompt are evaluated on development before freezing.
No fine-tuning, no paid API calls, no sending trial text to a hosted model.

Final-test release thresholds are recorded in `configs/extraction_release.json`
after development and before test scoring. Research feature comparisons may
report failed-gate extractors, but analyst-facing semantic extraction must not be
described as released or clinically reliable when those gates fail. Full semantic
adjudication on the target cohort remains unperformed.
