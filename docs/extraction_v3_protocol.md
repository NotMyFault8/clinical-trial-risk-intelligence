# Candidate-guided local LLM extraction experiment

This is a research experiment. It does not change the extractor used by the API,
the downstream risk model, or the original release thresholds.

## Method and references

The pipeline uses criterion boundaries and overlapping source windows, a token
NER model fitted on development labels, a development-only phrase lexicon,
numeric/temporal grammar candidates, and a local Qwen LLM. Two output formats are
developed: selecting candidate IDs, and directly quoting spans with candidates as
fallible hints. Two similar labeled examples are retrieved exclusively from each
fold's training groups. The ID pilot is retained despite its poor results. The
quote variant can add spans missing from candidates and uses the original
string-array JSON contract, without the six-entity cap. Invalid JSON is a format
failure; a well-formed but unsupported quote is rejected as an evidence error,
exactly as in the original extractor. There is no schema repair.
Valid requests from a partially failed document remain visible, while the document
itself fails the schema metric.

Two fusion policies are compared on the same development OOF predictions:
LLM-only outputs, and their exact-span union with the supervised token NER.
Union can improve recall while lowering precision. It never changes an LLM
schema failure into a pass. The selected policy and both single-component
ablations are reported, so an improvement cannot be attributed to the LLM when
it comes from deterministic NER additions.

For the quote variant, each accepted string maps to all exact occurrences inside
its source window. Overlapping windows are deduplicated by type and absolute
offset. This avoids silently losing repeated quotations, but may incorrectly
assign a type to another repeated occurrence: such mistakes count as false
positives. Source text is never normalized or fuzzy-matched. Schema success is
reported separately from evidence rejection, exact F1, and complete-document
exact-match rate. The prompt distinguishes CHIA's Person-labeled word `age` from
Value-labeled age bounds, based only on the development annotation audit.

The design draws on [Clinical-Trial-Parser's architecture](https://github.com/facebookresearch/Clinical-Trial-Parser/blob/03ea0d3f5efe7d1bee713d05bb026201230d9409/doc/architecture.md)
and [criterion processing](https://github.com/facebookresearch/Clinical-Trial-Parser/blob/03ea0d3f5efe7d1bee713d05bb026201230d9409/src/ct/criteria/parse_criteria.go).
The implementation is new Python code; upstream Go/PyText code and pretrained
weights were not copied. Its separation of NER and numerical grammar informs the
candidate generator. Unlike its text normalization, this experiment preserves
original characters for exact-offset evaluation. The earlier Boolean/cardinality
experiment informed the instruction to distinguish measurement values from counts;
its lexical AND/OR links are not treated as validated clinical logic.

The previous lightweight token NER and BiomedBERT development experiments remain
recorded as separate baselines. BiomedBERT's three-epoch small-data run performed
worse than token NER, so that checkpoint is not added to this ensemble. This does
not establish that biomedical encoders are generally inferior. Candidate spans
can overlap, but discontinuous entities remain unrepresentable and count as misses.

## Data separation and model selection

CHIA v2 is public, expert-annotated data by Kury et al., licensed CC BY 4.0:
[paper](https://doi.org/10.1038/s41597-020-00620-0),
[data](https://doi.org/10.6084/m9.figshare.11855817.v2).
The archive SHA256 is checked against `configs/chia_source.json`.

- Development: the existing 50 trial groups / 100 documents, five grouped folds.
  Token fitting, dictionary construction and retrieval examples exclude the held
  fold. The historical benchmark JSON contains test rows too; filtering prevents
  their use in fitting/scoring rather than claiming those bytes were never read.
- New holdout: 50 previously unused components / 100 documents. Text-only character
  4–5 gram hashing and cosine >=0.9 components exclude every historically used
  trial and its near duplicates. The first 50 unused groups by
  `SHA256("llm-v3-fresh-2026-10-30:" + group)` are fixed in `fresh_manifest.json`.
  Preparation does not open annotation files. Approximate grouping does not exclude
  every paraphrase; pretrained-model contamination of this public corpus is unknown.
- Qwen 1.5B and 7B local 4-bit models and the two fusion policies are compared on
  grouped development exact F1. The highest F1 is selected before new holdout annotations are opened. The freeze
  records code, prompt, manifest and development-report hashes and the unchanged
  release thresholds. Outputs are saved before annotation scoring. Evaluation
  refuses to overwrite an existing new holdout result.

## Metrics

The primary comparison supplies both original and candidate-guided LLMs with the
identical original `visible_text` prefix (at most 1,800 characters). Both gold and
predictions are restricted to that scope. Secondary evaluation runs the new
pipeline on full text and compares against all annotations, including nested and
discontinuous gold. No normalization, boundary tolerance or partial-match credit
is applied. The new system has no per-type six-span limit; this change is explicit.

Report document schema validity, raw request schema validity, micro and per-type
precision/recall/exact F1, errors, token counts, and the token-NER ablation. Candidate
pool recall is a diagnostic of available boundaries, not a validated extractor.
Source-offset validity checks quotation fidelity, not semantic correctness.
Paired 95% percentile intervals resample 50 trial groups 2,000 times with seed
31030. They condition on the trained system and do not include training uncertainty.

The user-authorized publication condition is improvement over the original LLM
on all three primary measures: document schema rate, precision and exact F1.
Publication of a research result does not grant semantic release. The unchanged
numeric extraction thresholds require schema >=98%, precision >=90%, and F1
>=65%. The V3 system fails every numeric threshold; benchmark span extraction alone does not
establish clinical validity or patient-eligibility logic.

## AI secondary review

All 12 selected cases have a separate **AI secondary review**, authored by Codex
(AI) after evaluation. It is unblinded and pairs
qualitative type/boundary/context findings with exact gold-match counts and
verified source quotes. The [review](../reports/extraction/llm_v3/ai_second_review.md)
and its JSON record retain omissions and regressions. It does not change any
frozen code, prompts, predictions or gold.

## Local commands

Use the repository Python environment, local CHIA archive, and pinned model paths
in `configs/pretrained.json`. This experiment requires Apple Silicon MLX. The
saved evaluation records exact runtime package versions and local weight hashes.
Model calls use no hosted API. Raw prompts/responses and weights stay in ignored
`artifacts/`; metrics, predictions, manifests, error sets and AI review records are
versioned under `reports/extraction/llm_v3/`.

```sh
.venv/bin/python scripts/experiment_llm_v3.py prepare
.venv/bin/python scripts/experiment_llm_v3.py develop --model 1.5b
.venv/bin/python scripts/experiment_llm_v3.py develop --model 1.5b --mode quotes
.venv/bin/python scripts/experiment_llm_v3.py develop --model 7b --mode quotes
.venv/bin/python scripts/experiment_llm_v3.py ablate
.venv/bin/python scripts/experiment_llm_v3.py freeze
.venv/bin/python scripts/experiment_llm_v3.py evaluate
.venv/bin/python scripts/review_llm_v3_outputs.py
.venv/bin/python scripts/summarize_llm_v3.py
.venv/bin/python -m pytest -m 'not integration' -q
```

For an independent reproduction, use a separate output copy and compare hashes.
Preserve the published freeze and results. A code/prompt revision requires another
protocol and holdout rather than optimization against this new result.
