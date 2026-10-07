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

Research results and local verification records are available. The
[repository audit](reports/github_repository_audit_2026-10-07.md) identifies
unresolved clean-checkout reproduction blockers, including a missing data package
and a failed GitHub Actions run. Historical local test results are not evidence
that the current checkout passes. See [project status](docs/project_status.md)
for release gates and outstanding work.

The LLM extractor failed its release thresholds. Free-form report generation is
withheld; the local application uses deterministic evidence reports. Independent
semantic review and analyst-usefulness review remain incomplete.

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
container workflow. Resolve the documented reproduction blockers before expecting
a clean checkout to run end to end. Raw archives and fitted artifacts are external
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
provide provenance. The missing `clinical_trial_risk.data` source package and its
ignore-rule conflict are tracked in the repository audit.

This is an independent research project. Clinical validation, causal effects,
prospective deployment and operational cost savings have not been established.
