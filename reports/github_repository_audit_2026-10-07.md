# Clinical Trial Risk Intelligence — GitHub Repository Audit

**Audit date:** 7 October 2026  
**Repository:** [NotMyFault8/clinical-trial-risk-intelligence](https://github.com/NotMyFault8/clinical-trial-risk-intelligence)  
**Branch and audited revision:** `main` at `a0f2fd9183197b16340de9f3834f7bb3a6ab43e0`  
**Overall disposition:** Research results are documented, but the published repository is not reproducible from a clean checkout and its latest GitHub Actions run failed.

## Executive summary

The repository contains a substantial research implementation, detailed protocol and cohort documentation, saved evaluation outputs, extraction experiments, a deterministic reporting path, and a local API. The reported results are appropriately qualified as retrospective and conditional on observed outcomes. Negative extraction and generation results are disclosed.

Two release-blocking repository issues were identified. First, the required `clinical_trial_risk.data` package is absent from the tracked source. The root `.gitignore` rule for `data/` also excludes a source directory at `src/clinical_trial_risk/data/`. The latest GitHub Actions run consequently failed during pytest collection with seven `ModuleNotFoundError` errors. Second, `.env.example` contains non-placeholder AACT credentials. Their validity was not tested; treat them as exposed, rotate or revoke them, and replace them with placeholders.

Saved cohort totals, selected model summaries, calibration-bin counts, top-K calculations, extraction error totals, and selected source hashes were internally consistent in the retrieved commit. This check covers saved evidence and tracked files. Raw AACT archives, processed Parquet files, fitted model objects, model weights, and caches are not tracked and were not available for independent end-to-end execution.

## Scope and method

The audit retrieved and inventoried all 117 tracked files in the pinned revision, totaling 1,644,228 bytes, and verified each retrieved file against its Git blob hash. All 34 Python files parsed successfully into syntax trees, and all 43 JSON files parsed. The principal cohort, SQL aggregation, feature, training, evaluation, extraction, reporting, API, configuration, test, and documentation paths were reviewed. The three saved result figures were visually inspected.

The GitHub Actions run on the audited commit installed dependencies and the package, then failed while collecting tests. Seven test modules could not import `clinical_trial_risk.data.cohort`; source compilation was skipped after collection failed. This audit did not rerun the project tests or execute the pipeline against raw inputs.

The snapshot manifest lists eight AACT ZIP archives totaling 12,752,745,942 bytes (about 12.75 GB). This is manifest metadata; the archive contents and hashes were not reverified during this audit. The repository's prior `reports/verification.json` records earlier local and container test results. Those are historical claims and do not override the observed failure of the current GitHub Actions run.

## Findings

| Priority | Finding | Evidence and impact | Required disposition |
|---|---|---|---|
| P1 | Non-placeholder database credentials are committed | `.env.example` contains a specific account and password-like value. Validity was not tested. | Rotate or revoke the credential; replace committed values with placeholders; review repository history and access to copies. Credential values are omitted from this report. |
| P1 | Essential data package is absent and matched by a broad ignore rule | `.gitignore` line 16 ignores `data/` at any depth. The tracked tree lacks `src/clinical_trial_risk/data/`; 15 Python files import `clinical_trial_risk.data.cohort`. GitHub Actions failed with seven import errors. | Scope data exclusions to the repository-root data directory, recover and commit the actual source package, and obtain a passing clean-checkout workflow run. |
| P2 | Holdout reproduction stops at an existing-output guard | `src/clinical_trial_risk/evaluation/prediction.py` refuses to run when `reports/evaluation/holdout.json` exists. That report is already tracked, and the runbook does not give a complete separate-output reproduction procedure. | Preserve the frozen reference result and document an explicit reproduction destination with comparison against that reference. |
| P2 | Evaluation does not enforce all stored input hashes | Training records hashes for outcomes and supplementary feature files. Primary evaluation checks the protocol and baseline feature hashes, but not those stored outcome or supplementary hashes; sensitivity evaluation performs fewer provenance checks. | Validate a shared input manifest for all files used by each primary and sensitivity result. No actual input substitution was established by this audit. |
| P2 | Project status documentation is stale relative to GitHub | `docs/project_status.md` describes the work as uncommitted and says nothing was pushed; `reports/verification.json` says remote Actions were not run. The audited revision is committed, and its remote Actions run failed. | Keep the prior evidence as historical, and publish a current status tied to commit and workflow run. |

The archived copy at `reports/cohort/executed_pipeline.py` matches its recorded execution hash, but it does not restore the missing package by itself. It lacks `validate_aggregation`, which the current tests import, and its repository-root calculation reflects the archived file's former location. The Dockerfile also sets `CTR_PROJECT_ROOT`; the missing runtime package must be reconciled with that expected layout.

## Research design and saved results

The documented primary estimand is the distinction between reported Terminated and Completed status at a five-year snapshot, conditional on observing one of those two statuses among selected annual-landmark trials. It is not an estimate of termination probability for all newly starting trials. Unresolved, missing, withdrawn, suspended, and other statuses remain outside the primary binary comparison.

| Baseline snapshot | Eligible trials | Completed | Terminated | Other, unresolved, or missing | Included in binary analysis |
|---|---:|---:|---:|---:|---:|
| 2018-09-01 | 1,349 | 434 | 108 | 807 | 542 |
| 2019-09-01 | 1,365 | 456 | 109 | 800 | 565 |
| 2020-09-01 | 1,517 | 557 | 116 | 844 | 673 |
| 2021-09-01 | 1,472 | 516 | 116 | 840 | 632 |
| **Total** | **5,703** | **1,963** | **449** | **3,291** | **2,412** |

The primary test set contains 632 resolved records and 116 terminations. Training uses 1,107 resolved records from 2018–2019. The 2020 records are split by lead-sponsor hash into 332 tuning and 341 calibration records. The protocol allows sponsors to recur across years, so the design assesses future-cohort transfer rather than unseen-sponsor transfer.

The design has a further time limitation: the 2018–2019 training labels were ascertained in 2023–2024, after the 2021 test landmark. A chronological split of baseline snapshots does not make the experiment historically deployable. The report correctly describes the result as retrospective temporal generalization rather than pseudo-prospective or clinical validation.

The saved primary comparison reports a TF-IDF versus structured-logistic average-precision difference of approximately −0.014, with a paired sponsor-cluster 95% interval of [−0.047, 0.040]. The interval includes zero, so these results do not establish an incremental average-precision improvement from TF-IDF. The application model was selected by tuning performance, not by selecting the best holdout performer.

The LLM extraction component did not meet its release thresholds: saved test exact-span micro F1 is approximately 0.139 for the LLM versus 0.162 for the rules baseline. The generated-report evaluation produced zero schema-valid outputs among 40 cases. The repository withholds those components from semantic release and uses deterministic reports. Independent target-domain semantic review and analyst-usefulness review remain incomplete.

## Data and implementation boundaries

The intended pipeline is: historical AACT archives, point-in-time cohort selection, child-table aggregation, baseline features and separate outcome labels, temporal model fitting and evaluation, optional eligibility extraction, evidence packets, deterministic reports, and a read-only local API.

The Phase-2 SQL correctly aggregates one-to-many child tables before joining them to trial-level data. A direct join across two conditions, three interventions, and four facilities can yield 24 rows for one trial. Pre-aggregation protects the intended one-row-per-trial grain and avoids inflated counts or trial weights.

The feature builder uses an explicit feature allowlist and rejects named post-outcome fields. The SQL excludes outcomes from the feature query. The reporting packet uses computed model outputs and source passages and checks extraction spans against source text. These are meaningful design controls in the tracked implementation; the missing data package prevents clean-checkout verification that the published executable workflow applies them end to end.

The report directory does not contain raw AACT archives, processed trial tables, fitted estimators, or pretrained weights. The repository therefore separates source code and reviewable summaries from large inputs and generated artifacts, but a new checkout must obtain and verify those external materials before a full reproduction can be performed.

## Recommended remediation order

1. Revoke or rotate the committed AACT credential and replace the example configuration with placeholders.
2. Correct the `.gitignore` scope and restore the missing `clinical_trial_risk.data` source package.
3. Reconcile the restored package with the archived pipeline, Docker root configuration, and current imports.
4. Add a reproducible holdout output path and verify all recorded input hashes before primary and sensitivity evaluation.
5. Run the workflow from a clean checkout with verified source archives; update status and verification documentation with the resulting commit and CI evidence.

Until these items are addressed and independently verified, the repository's saved scientific results remain reviewable evidence, but the published GitHub workflow should be treated as unreproducible from a clean checkout.

## Audit artifacts

- [`README.md`](../README.md): project scope and entry point.
- [`docs/research_protocol.md`](../docs/research_protocol.md): population, estimand, splits, and analysis decisions.
- [`docs/reproducibility.md`](../docs/reproducibility.md): setup and reproduction instructions.
- [`reports/cohort/audit.json`](cohort/audit.json): saved cohort counts and input/output hashes.
- [`reports/evaluation/holdout.json`](evaluation/holdout.json): saved model comparisons and metrics.
- [`reports/verification.json`](verification.json): prior local verification claims.
- [`reports/github_file_inventory_2026-10-07.md`](github_file_inventory_2026-10-07.md): tracked-file inventory and review disposition.
