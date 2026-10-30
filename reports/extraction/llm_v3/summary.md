# Local LLM extraction experiment — 2026-10-30

**Research result; semantic release remains withheld. AI secondary review: 12/12 cases complete.**

A new CHIA holdout contains 100 documents / 50 trials / 50 near-duplicate groups, excluded from the historical 205 used trials. Selection used source text only. Model/prompt/code were frozen before opening these annotations. Both primary systems receive the same original 1,800-character maximum prefix.

Selected system: Qwen 1.5b, `quotes` output mode, `union` fusion; criterion-aware source windows, development-trained token NER and lexicon, numerical/temporal candidates, and two training-only retrieved examples. No LLM fine-tuning or hosted API calls. Model and LLM-only versus NER-union policy are selected by grouped five-fold development exact F1. The fresh holdout is evaluated once.

## Same-input primary comparison

| System | Document schema valid | Precision | Recall | Exact span F1 | Completely exact documents |
|---|---:|---:|---:|---:|---:|
| Original Qwen 1.5B | 76.0% | 23.9% | 9.8% | 13.9% | 8/100 |
| New LLM pipeline | 88.0% | 27.5% | 53.5% | 36.3% | 7/100 |
| New LLM before optional NER union | 88.0% | 27.7% | 25.4% | 26.5% | 8/100 |
| Token NER without LLM | 100.0% | 32.9% | 44.2% | 37.7% | 12/100 |
| Regex rules | 100.0% | 24.4% | 12.7% | 16.7% | 17/100 |

Raw LLM request schema validity: 117/129 (90.7%). Unsupported quotes rejected: 83; accepted quote entries with repeated local occurrences: 33. A document passes format checks only when all its LLM requests pass.

Schema validity checks output shape, not correct clinical meaning. Exact F1 requires both the correct entity type and every character boundary. Nested and discontinuous gold remain in the denominator. Completely exact documents require the whole predicted entity set to equal gold; empty-gold documents are included.

The new quote protocol permits more than six entities per type. Repeated exact quotations map to all local source occurrences, then overlapping-window duplicates are removed. This can recover repeated mentions or introduce false positives. Unsupported quotes are rejected; valid JSON with a rejected quote remains schema-valid, matching the original metric definition. No schema repair is used. If union is selected, deterministic NER spans are explicitly included even for partial LLM failures; their inclusion never changes a failed document to schema-valid. The LLM-only and NER-only rows expose the contribution of each component.

## Per-type primary results

| Type | TP | FP | FN | Precision | Recall | Exact F1 |
|---|---:|---:|---:|---:|---:|---:|
| Measurement | 95 | 294 | 86 | 24.4% | 52.5% | 33.3% |
| Value | 127 | 257 | 101 | 33.1% | 55.7% | 41.5% |
| Temporal | 94 | 283 | 88 | 24.9% | 51.6% | 33.6% |

## Full-text secondary result

| System | Schema valid | Precision | Recall | Exact F1 |
|---|---:|---:|---:|---:|
| Original, limited to prefix | 76.0% | 23.9% | 8.7% | 12.8% |
| New, full text | 87.0% | 27.3% | 53.0% | 36.0% |
| Token NER, full text | 100.0% | 32.1% | 44.0% | 37.1% |

This secondary comparison includes all source annotations. The original system still sees only its fixed prefix, so outside-prefix omissions count against it. The primary table is the controlled same-input comparison.

Fresh target-annotation text/offset discrepancies: 0. Published offsets are retained; no gold corrections or exclusions were made after scoring.

## Uncertainty and release

- Paired precision difference, new minus original: 95% group-bootstrap interval [-3.52, 10.98] percentage points (2,000 resamples; 50 groups).
- Paired f1 difference, new minus original: 95% group-bootstrap interval [15.90, 28.26] percentage points (2,000 resamples; 50 groups).

All three publication-improvement checks passed: **True**. Semantic release passed: **False**. These are different decisions: publishing measured research improvement does not authorize clinical use.

Precision's interval includes zero, so its higher point estimate does not establish a reliable precision improvement. The selected LLM + NER union also falls below token NER alone on this fresh sample (36.3% versus 37.7% exact F1); completely exact documents decline from 8/100 for the original LLM to 7/100. Selection was frozen on development, so this result is not used to switch the reported winner after testing.

Unchanged numeric release thresholds: schema >=98%, precision >=90% and exact F1 >=65%. The new extractor fails each of these measured criteria. Clinical use also remains unsupported by this benchmark.

## Development experiments and failure analysis

| Variant | Schema valid | Precision | Exact F1 |
|---|---:|---:|---:|
| development_1.5b | 58.0% | 15.9% | 13.7% |
| development_1.5b_quotes | 88.0% | 30.0% | 27.0% |
| development_1.5b_quotes_initial | 85.0% | 28.5% | 25.2% |
| development_7b_quotes | 94.0% | 22.1% | 29.7% |

The candidate-ID format produced invalid IDs, conflicting assignments and weak exact-boundary accuracy; the incomplete 7B ID pilot is retained but excluded from selection. Quoted strings were easier for the local models. Development-only annotation inspection also found 59 Person annotations and 2 context-dependent Value annotations among the checked age/sex descriptors, with no Measurement annotations. This exposed the original prompt's incorrect treatment of the word age as Measurement. Age bounds remain Value.

Earlier full-development token NER OOF F1 was 31.5%; the three-epoch BiomedBERT baseline was 19.9%. Those earlier scores used all source gold, so they must not be directly compared with the prefix table. The token-NER row above is rerun on the same new sample and scope. Rule-parser and Boolean-link counts in earlier experiments were coverage measurements, not semantic accuracy.

## AI secondary review

Codex (AI) reviewed **12/12 cases** after evaluation. The [detailed review](ai_second_review.md) checks every A/B span and lists omissions, type/boundary errors and context limitations; [structured evidence](ai_second_review.json) includes exact counts and input hashes. It is an unblinded AI review of CHIA benchmark annotations, not an independent clinical validation.

The AI review does not validate negation, Boolean scope or patient eligibility decisions, and it does not modify the frozen predictions or gold.

## Reproduction and evidence

See [the protocol](../../../docs/extraction_v3_protocol.md), [freeze](freeze.json), [fresh manifest](fresh_manifest.json), [measured results](fresh_evaluation.json), [predictions](fresh_predictions.json), [errors](fresh_errors.json), and [development label audit](development_label_audit.json). Local raw model requests/responses stay in ignored `artifacts/extraction_v3_cache/`; predictions retain cache keys. The evaluation JSON records exact runtime versions, hashes, token counts and generation timings. Cached durations describe original generation, not a new latency benchmark.

CHIA v2: Kury et al., [paper](https://doi.org/10.1038/s41597-020-00620-0), [dataset](https://doi.org/10.6084/m9.figshare.11855817.v2), CC BY 4.0. Source and annotation text in these review artifacts are attributed to this dataset; model predictions and selection are our derived annotations. Design reference: [Clinical-Trial-Parser](https://github.com/facebookresearch/Clinical-Trial-Parser/tree/03ea0d3f5efe7d1bee713d05bb026201230d9409).

This is one finite public-corpus holdout. Pretraining contamination and paraphrase overlap cannot be excluded. It does not establish prospective generalization, correct normalized units, negation/Boolean scope, patient eligibility decisions, or target-cohort clinical validity.
