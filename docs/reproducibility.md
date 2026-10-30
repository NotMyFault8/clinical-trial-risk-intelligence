# Reproducing the local research project

**Repository readiness:** the missing data package and ignore-rule conflict in
the [historical audit](../reports/github_repository_audit_2026-10-07.md) were fixed
in `4cb6985`, and main CI passed at `62f5407`. External data/model artifacts and
remaining audit checks are still required for full end-to-end reproduction.

Use Python 3.12. The measured environment is pinned in `requirements-macos.lock`;
the tested container has its separate Linux lock. Mac text generation uses Apple
Silicon and MLX. The serving container uses cached features and needs no GPU.
Source dates and measured duration/latency remain part of the evidence. The
[V3 extraction protocol](extraction_v3_protocol.md) additionally records execution
and freeze timestamps to establish that selection preceded held-out scoring.

## Environment and sources

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos.lock
.venv/bin/python -m pip install --no-deps -e .
```

Sign in to the official AACT download catalog, download the eight URLs listed in
`configs/snapshots.json`, and keep their original archive filenames. The account
is only needed to obtain archives; no database password is needed by this pipeline.
Then verify/copy them into the expected ignored data paths:

```sh
.venv/bin/python scripts/prepare_sources.py --downloads ~/Downloads
.venv/bin/python -m clinical_trial_risk.data.cohort
```

The cohort builder streams ZIP members, checks keys and references, stores the
selected child tables, runs the SQL aggregation and writes three separate Parquet
tables: baseline features, cohort metadata and outcomes. It records checksums and
counts in `reports/cohort/audit.json`. It does not materialize a full PostgreSQL
database. Earlier live PostgreSQL/DBeaver schema audits remain Phase-1 evidence;
the reproducible historical aggregation runs that relational SQL in DuckDB.

## Text resources and models

```sh
.venv/bin/python scripts/download_text_resources.py
.venv/bin/python -m clinical_trial_risk.features.embeddings
.venv/bin/python -m clinical_trial_risk.llm.benchmark --split development
.venv/bin/python -m clinical_trial_risk.llm.benchmark --split test
.venv/bin/python -m clinical_trial_risk.llm.extract
.venv/bin/python -m clinical_trial_risk.models.train --families structured_logistic structured_counts structured_tfidf structured_boosting structured_embeddings structured_llm
```

The final extractor selection/prompt is already frozen. Reproduction is not
permission to repeatedly inspect the benchmark test while tuning. Development
pilots are recorded separately. No trial text is uploaded to a hosted model;
downloads retrieve public weights only. CPU embeddings and local GPU extraction
may take several minutes. Cached extraction keys include input, model revision,
prompt, schema and decoding configuration. Failures remain in the cohort.

Fit the four secondary analyses with the same settings:

```sh
for variant in possible_date_interval withdrawal no_facilities zero_imputation; do
  .venv/bin/python -m clinical_trial_risk.models.train --variant "$variant" --families structured_logistic structured_tfidf
done
```

Only after all models and release thresholds are frozen:

```sh
.venv/bin/python -m clinical_trial_risk.evaluation.prediction
.venv/bin/python scripts/prepare_release.py
.venv/bin/python -m clinical_trial_risk.reporting.evaluate
.venv/bin/python scripts/build_research_report.py
.venv/bin/python -m pytest -q
```

The holdout evaluator refuses to overwrite an existing final result. A faithful
reproduction should run in a separate checkout/output copy, compare source and
protocol hashes, and preserve the original report. Changing research decisions
requires a new protocol and a new prospective evaluation cohort, not repeated
optimization against the same published holdout. Numerical results can vary
slightly across BLAS/CPU/GPU platforms even with fixed seeds and weights.

## Serve locally

```sh
.venv/bin/python -m uvicorn clinical_trial_risk.api.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

The dashboard serves the frozen held-out research portfolio by NCT ID. It does
not accept arbitrary live trial records, retrain automatically, claim online
generalization, or access the live AACT database. Only deterministic evidence
reports are served. Model-selection, feature, source and calibration provenance
are included in each packet.

```sh
docker build -t clinical-trial-risk:local .
docker run --rm --name clinical-trial-risk-demo -p 127.0.0.1:8000:8000 \
  -v "$PWD/artifacts/release_bundle/data:/app/data:ro" \
  -v "$PWD/artifacts/release_bundle/artifacts:/app/artifacts:ro" \
  -v "$PWD/artifacts/release_bundle/reports:/app/reports:ro" \
  clinical-trial-risk:local
```

`prepare_release.py` excludes the outcome table, holdout labels, credentials and
raw archives. Container build context also excludes these. The container runs as
a non-root user. Publish neither model artifacts nor source data unintentionally.
This project has no cloud deployment or paid API dependency.

## Monitoring and maintenance

`/monitoring` reports in-memory request/error counts and latency quantiles without
persisting request bodies or trial identifiers. `/evaluation` exposes measured
historical drift, selection and subgroup results. A new source, label definition,
model or prompt needs explicit versioning and evaluation. Proposed triggers:
investigate missingness shifts >10 percentage points, categorical total variation
>0.2, schema failures, checksum mismatches and attribution reconstruction failures.
These are operational review thresholds, not validated guarantees. Outcome
performance/calibration requires delayed labels and must not be inferred solely
from feature drift. There is no autonomous retraining or unmeasured cost claim.
