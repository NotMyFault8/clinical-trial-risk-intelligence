# Clinical Trial Risk Intelligence

A public-data research system for studying early trial termination using historical
AACT / ClinicalTrials.gov metadata and eligibility text. The repository contains
relational data processing, temporal model comparisons, extraction experiments,
evidence reports, and a read-only FastAPI dashboard.

## Research scope

The primary analysis distinguishes **reported Terminated versus Completed status
at a five-year snapshot**, conditional on observing one of those statuses in the
selected cohort. Scores do not estimate termination probability for all newly
starting trials. Training outcomes matured after the historical test landmark;
the evaluation measures retrospective temporal generalization.

## Project status

Research results and local verification records are available. The missing data
package and its ignore-rule conflict reported in the
[2026-10-07 audit](reports/github_repository_audit_2026-10-07.md) were repaired in
commit `4cb6985`. Main-branch [Research checks passed at `62f5407`](https://github.com/NotMyFault8/clinical-trial-risk-intelligence/actions/runs/37784370383)
on 2026-10-08. The audit is historical evidence, not the current package/CI status.
Full end-to-end reproduction still requires external data and model artifacts;
remaining audit items and release gates are tracked in [project status](docs/project_status.md).

The LLM extractor failed its release thresholds. Free-form report generation is
withheld; the local application uses deterministic evidence reports. Independent
semantic review and analyst-usefulness review remain incomplete.

## Revised extraction experiment — 2026-10-30

A frozen local experiment evaluates 100 previously unused CHIA documents from
50 trial groups. Both primary systems see the same maximum 1,800-character
prefix. The candidate generator borrows the separation of entity recognition and
numerical grammar from
[Clinical-Trial-Parser](https://github.com/facebookresearch/Clinical-Trial-Parser/tree/03ea0d3f5efe7d1bee713d05bb026201230d9409),
then combines it with source windows, retrieved examples and quotation checks.
Grouped development folds selected Qwen 1.5B quoted output combined with token
NER; no LLM fine-tuning or hosted API was used.

| System | Format-valid documents | Precision | Exact span F1 |
|---|---:|---:|---:|
| Original LLM | 76.0% | 23.9% | 13.9% |
| Revised LLM + NER | 88.0% | 27.5% | 36.3% |
| Revised LLM alone | 88.0% | 27.7% | 26.5% |
| Token NER alone | 100.0% | 32.9% | 37.7% |

All three primary point estimates improve over the original LLM, meeting the
condition for publishing this research update. **Semantic release still fails**
(required: 98% format validity, 90% precision and 65% exact F1, plus target-cohort
human review). The revised combination does not outperform NER alone. Its
precision improvement is uncertain: the paired 95% interval is -3.52 to +10.98
percentage points. Only 7/100 documents have a completely correct entity set,
versus 8/100 for the original. Exact copied text does not establish correct labels.

**AI secondary review: 12/12 cases completed by Codex (AI).**
[Per-case findings](reports/extraction/llm_v3/ai_second_review.md) identify type
confusion, truncated boundaries, duplicate spans and omissions. This is an
unblinded AI review. Human review remains **0/12**, with its worksheet retained;
neither clinical sign-off nor patient eligibility logic is established.
See the [measured report](reports/extraction/llm_v3/summary.md),
[frozen protocol](docs/extraction_v3_protocol.md) and
[raw results](reports/extraction/llm_v3/fresh_evaluation.json).

## System architecture

```text
Historical AACT archives
  -> source validation and trial-level SQL aggregation
  -> baseline features + separate outcome tables
  -> temporal model fitting, calibration and evaluation
  -> verified evidence packets and deterministic reports
  -> read-only local API and dashboard
```

- **Data:** eight pinned archives, source manifests, interval-based pre-start
  selection, child-table aggregation, and separate baseline/outcome interfaces.
- **Prediction:** logistic regression, XGBoost, simple text counts, TF-IDF,
  frozen embeddings, and an experimental LLM-feature comparison.
- **Evaluation:** train/tune/calibration/test separation, sponsor-cluster
  intervals, top-K prioritization, subgroup analysis, drift, and sensitivities.
- **Extraction and reporting:** CHIA benchmark comparisons, evidence-span checks,
  versioned prompts, attribution checks, and explicit component release decisions.
- **Application:** local FastAPI dashboard, dependency locks, container packaging,
  test definitions, CI configuration, and basic monitoring.

## Setup and local operation

The [reproduction runbook](docs/reproducibility.md) documents the Python 3.12
environment, pinned dependencies, archive preparation, research commands, and
container workflow. A clean checkout needs the documented external inputs to run
end to end. Raw archives and fitted artifacts are external
to Git and must be obtained or reproduced separately.

With the required package and local artifacts available:

```sh
.venv/bin/python -m uvicorn clinical_trial_risk.api.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open `http://127.0.0.1:8000`; API documentation is at `/docs`. The application
serves the frozen 2021 resolved-outcome portfolio, with baseline source evidence,
conditional scores, model contributions, and missing fields.

## Documentation

- [Research protocol](docs/research_protocol.md): population, labels and splits.
- [Research report](reports/research_report.md): measured comparisons and findings.
- [Feature dictionary](docs/feature_dictionary.md): sources and leakage controls.
- [Annotation manual](docs/annotation_manual.md): benchmark definitions.
- [Report review rubric](docs/report_review_rubric.md): outstanding review criteria.
- [Limitations](docs/limitations.md): validity and interpretation boundaries.

## Repository layout

| Path | Responsibility |
|---|---|
| `src/clinical_trial_risk/` | Feature, model, evaluation, extraction, reporting and API modules |
| `sql/` | Schema audits and trial-level aggregation |
| `configs/` | Cohort, source, model and release definitions |
| `prompts/` | Versioned extraction and report prompts |
| `scripts/` | Source preparation, release packaging and report utilities |
| `tests/` | Data, feature, evaluation, reporting and API checks |
| `docs/` | Research specifications, operational documentation and limitations |
| `reports/` | Saved research results, audits and release evidence |

Raw data, model weights, caches, credentials and local environments must remain
outside version control. Historical snapshot dates, hashes and model revisions
provide provenance. The `clinical_trial_risk.data` source package is tracked;
the root `/data/` ignore rule excludes raw data without excluding package source.

This is an independent research project. Clinical validation, causal effects,
prospective deployment and operational cost savings have not been established.
