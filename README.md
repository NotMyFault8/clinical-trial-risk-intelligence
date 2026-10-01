# Clinical Trial Risk Intelligence — local research demonstrator

A reproducible public-data research project studying whether historical trial
metadata and eligibility text distinguish **reported Terminated versus Completed
status at five years**. It includes relational SQL, leakage controls, temporal
model comparisons, calibration, extraction benchmarks, evidence reports and a
read-only local dashboard.

**This is a conditional retrospective research task.** Most eligible trials are
excluded from the two-status comparison. Scores are not termination probabilities
for all newly starting trials. Training labels matured after the historical test
landmark; no historically deployable, prospective or clinical validation is claimed.

## Status and evidence

The pipeline and local application are implemented. Completed automated verification
is recorded in `reports/verification.json` (24 local tests, 23 container tests,
and 632 checked report packets). The LLM extractor failed
its release thresholds; free-form generation requires independent semantic and
usefulness review and is not served. Negative experiments are part of the result.

- [Research report](reports/research_report.md): measured comparisons and limits.
- [Locked protocol](docs/research_protocol.md): population, labels and temporal splits.
- [Reproduction runbook](docs/reproducibility.md): commands from archives to app.
- [Feature dictionary](docs/feature_dictionary.md): sources, transformations and leakage risks.
- [Annotation manual](docs/annotation_manual.md): external human-labeled benchmark.
- [Limitations](docs/limitations.md): unresolved validation and unsupported claims.
- [Learning guide](docs/learning_guide.md): a route through the implemented code.

## Local application

From the project directory, after reproducing or retaining the local artifacts:

```sh
.venv/bin/python -m uvicorn clinical_trial_risk.api.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open `http://127.0.0.1:8000`. The app serves the frozen 2021 resolved-outcome
portfolio. Select a trial to inspect its baseline source, conditional score,
verified model contributions and missing fields. The app does not accept live
clinical records or make trial-management decisions. `/docs` describes its read-
only API. The Docker recipe and data-free image are covered in the runbook.

## What is implemented

1. Eight pinned AACT ZIP snapshots: four baseline years and matched five-year
   outcome sources. Strict parsing, unique keys, child references, CRC checking
   of consumed members, checksums and source-specific schema manifests.
2. Conservative interval-based pre-start cohort; SQL aggregates each child table
   before joining. Outcomes are stored separately from approved baseline fields.
3. Structured logistic regression, XGBoost, simple counts, TF-IDF, frozen MiniLM
   embeddings and an explicitly experimental LLM-feature comparison. Train/tune/
   calibration/test separation, paired sponsor-cluster intervals, calibration,
   top-K prioritization, drift/subgroups and prespecified sensitivity analyses.
4. Rules and local pretrained extraction tested against published CHIA annotations.
   Exact evidence checks, cache/version provenance, error analysis and failed
   release decisions. No fine-tuning or hosted LLM API calls.
5. Typed evidence packets, additive attribution checks, deterministic reports and
   a separate experimental generation/fidelity evaluation. Independent review
   forms are prepared; unperformed human reviews are not claimed.
6. A local FastAPI dashboard, model registry, reproducible commands, dependency
   locks, a non-root container, tests, CI configuration and basic monitoring.

## File map and data policy

`src/clinical_trial_risk/` contains reusable Python modules. `sql/phase2/` contains
the trial aggregation. `configs/`, `prompts/`, `tests/`, `docs/` and `reports/`
hold the reviewable research definitions and evidence. Earlier DBeaver/PostgreSQL
schema-audit work remains under `sql/phase1/` and `reports/phase1/`.

Large `data/`, local `artifacts/` and `.venv/` are ignored by Git. The environment
contains third-party libraries; raw ZIPs contain the source data; neither is
handwritten project code. No new execution dates/times are added to manifests.
Historical snapshot dates, model revisions, hashes and measured durations remain
necessary for reproducibility. Synced ChatGPT `sources/` files are read-only.

No claim of Caidya employment, clinical validation, causal impact, production
deployment, cost savings, RAG or fine-tuning is made by this independent project.
