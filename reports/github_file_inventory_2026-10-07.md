# GitHub repository file inventory — 7 October 2026

Pinned commit: `a0f2fd9183197b16340de9f3834f7bb3a6ab43e0`. All 117 tracked files are listed. Every retrieved file matched its Git blob hash.

This inventory lists the tracked files at commit a0f2fd9183197b16340de9f3834f7bb3a6ab43e0 and records their repository role and audit disposition. File-level descriptions are based on the repository review; raw data and model artifacts are excluded from Git and were not available for independent execution.

| File | Bytes | Purpose and coverage |
|---|---:|---|
| `.dockerignore` | 115 | Container packaging; full execution not repeated. |
| `.env.example` | 224 | Configuration template; non-placeholder credentials found. Values omitted from audit prose. |
| `.github/workflows/tests.yml` | 395 | Remote test workflow; current pinned run failed during collection. |
| `.gitignore` | 386 | Repository exclusions; data/ also excludes the required source package. |
| `Dockerfile` | 628 | Container packaging; full execution not repeated. |
| `README.md` | 4,609 | Entry point, scope, claims and run instructions. |
| `configs/analysis_protocol.json` | 1,651 | Machine-readable source, experiment or release definitions; JSON parsed where applicable. |
| `configs/chia_source.json` | 620 | Machine-readable source, experiment or release definitions; JSON parsed where applicable. |
| `configs/cohort_phase1.yaml` | 1,344 | Machine-readable source, experiment or release definitions; JSON parsed where applicable. |
| `configs/extraction_release.json` | 831 | Machine-readable source, experiment or release definitions; JSON parsed where applicable. |
| `configs/pretrained.json` | 786 | Machine-readable source, experiment or release definitions; JSON parsed where applicable. |
| `configs/report_release.json` | 638 | Machine-readable source, experiment or release definitions; JSON parsed where applicable. |
| `configs/snapshots.json` | 33,481 | Machine-readable source, experiment or release definitions; JSON parsed where applicable. |
| `docs/annotation_manual.md` | 4,225 | Research definition, reference material, limitations or reproduction documentation. |
| `docs/feature_dictionary.md` | 4,872 | Research definition, reference material, limitations or reproduction documentation. |
| `docs/learning_guide.md` | 3,068 | Research definition, reference material, limitations or reproduction documentation. |
| `docs/limitations.md` | 3,069 | Research definition, reference material, limitations or reproduction documentation. |
| `docs/phase1/README.md` | 2,907 | Historical schema/cohort planning; reconcile with active research protocol. |
| `docs/phase1/cohort_spec.md` | 4,683 | Historical schema/cohort planning; reconcile with active research protocol. |
| `docs/phase1/data_source_strategy.md` | 5,644 | Historical schema/cohort planning; reconcile with active research protocol. |
| `docs/phase1/feature_availability_dictionary.md` | 1,032 | Historical schema/cohort planning; reconcile with active research protocol. |
| `docs/phase1/leakage_register.md` | 1,206 | Historical schema/cohort planning; reconcile with active research protocol. |
| `docs/phase1/schema_notes.md` | 3,829 | Historical schema/cohort planning; reconcile with active research protocol. |
| `docs/phase1/snapshot_audit.md` | 14,898 | Historical schema/cohort planning; reconcile with active research protocol. |
| `docs/project_status.md` | 2,367 | Research definition, reference material, limitations or reproduction documentation. |
| `docs/report_review_rubric.md` | 2,277 | Research definition, reference material, limitations or reproduction documentation. |
| `docs/reproducibility.md` | 5,434 | Research definition, reference material, limitations or reproduction documentation. |
| `docs/research_protocol.md` | 7,471 | Research definition, reference material, limitations or reproduction documentation. |
| `prompts/extract_v1.txt` | 1,157 | Versioned model instruction text; assessed as project data. |
| `prompts/extract_v2.txt` | 1,650 | Versioned model instruction text; assessed as project data. |
| `prompts/report_v1.txt` | 986 | Versioned model instruction text; assessed as project data. |
| `pyproject.toml` | 988 | Dependencies and packaging; current CI installed successfully. |
| `reports/cohort/audit.json` | 12,131 | Saved cohort counts, checks and output hashes; counts reconciled, raw rows unavailable. |
| `reports/cohort/executed_pipeline.py` | 10,387 | Hash-matched archived execution source; current importable package is absent. |
| `reports/cohort/temporal_checks.json` | 143 | Saved cohort counts, checks and output hashes; counts reconciled, raw rows unavailable. |
| `reports/environment.json` | 1,576 | Saved output or verification claim; read as historical evidence, not a fresh execution. |
| `reports/evaluation/holdout.json` | 144,102 | Saved holdout metrics; counts, bins and top-K arithmetic checked; predictions unavailable. |
| `reports/example_baseline_report.md` | 1,753 | Saved output or verification claim; read as historical evidence, not a fresh execution. |
| `reports/extraction/development.json` | 3,901 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/development_errors.json` | 91,056 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/development_large_model.json` | 3,958 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/development_large_model_errors.json` | 84,261 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/development_small_model.json` | 3,848 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/development_small_model_errors.json` | 91,600 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/error_analysis.json` | 11,518 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/release_decision.json` | 252 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/test.json` | 3,960 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/extraction/test_errors.json` | 281,226 | Saved extraction scores and diagnostic rows; error totals and scoring arithmetic checked. |
| `reports/figures/calibration.png` | 56,521 | Saved result figure; visually inspected against result summaries. |
| `reports/figures/model_comparison.png` | 48,906 | Saved result figure; visually inspected against result summaries. |
| `reports/figures/outcome_selection.png` | 30,172 | Saved result figure; visually inspected against result summaries. |
| `reports/generation/blinded_review.json` | 222,222 | Saved generated cases, checks and unfilled review forms; case/summary consistency checked. |
| `reports/generation/cases.json` | 161,206 | Saved generated cases, checks and unfilled review forms; case/summary consistency checked. |
| `reports/generation/evaluation.json` | 1,208 | Saved generated cases, checks and unfilled review forms; case/summary consistency checked. |
| `reports/generation/review_key.json` | 2,434 | Saved generated cases, checks and unfilled review forms; case/summary consistency checked. |
| `reports/models/no_facilities/structured_logistic.json` | 841 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/no_facilities/structured_tfidf.json` | 835 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/possible_date_interval/structured_logistic.json` | 852 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/possible_date_interval/structured_tfidf.json` | 847 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/primary/structured_boosting.json` | 1,102 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/primary/structured_counts.json` | 836 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/primary/structured_embeddings.json` | 835 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/primary/structured_llm.json` | 832 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/primary/structured_logistic.json` | 837 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/primary/structured_tfidf.json` | 830 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/withdrawal/structured_logistic.json` | 838 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/withdrawal/structured_tfidf.json` | 833 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/zero_imputation/structured_logistic.json` | 839 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/models/zero_imputation/structured_tfidf.json` | 837 | Saved candidate scores, calibration and input counts; selection/protocol consistency checked. |
| `reports/phase1/schema_audit_2026-09-29/audit_results.json` | 36,043 | Saved live-schema audit evidence and SQL/report utilities; database not queried anew. |
| `reports/phase1/schema_audit_2026-09-29/build_report.py` | 17,597 | Saved live-schema audit evidence and SQL/report utilities; database not queried anew. |
| `reports/phase1/schema_audit_2026-09-29/collect_audit.py` | 4,953 | Saved live-schema audit evidence and SQL/report utilities; database not queried anew. |
| `reports/phase1/schema_audit_2026-09-29/executed_audit.sql` | 15,025 | Saved live-schema audit evidence and SQL/report utilities; database not queried anew. |
| `reports/phase1/schema_audit_2026-09-29/schema_audit_original.sql` | 4,461 | Saved live-schema audit evidence and SQL/report utilities; database not queried anew. |
| `reports/phase1/schema_audit_2026-09-29/schema_audit_report.md` | 23,023 | Saved live-schema audit evidence and SQL/report utilities; database not queried anew. |
| `reports/report_invariants.json` | 321 | Saved output or verification claim; read as historical evidence, not a fresh execution. |
| `reports/research_report.md` | 9,477 | Saved output or verification claim; read as historical evidence, not a fresh execution. |
| `reports/serving_measurements.json` | 577 | Saved output or verification claim; read as historical evidence, not a fresh execution. |
| `reports/text/embeddings.json` | 567 | Saved output or verification claim; read as historical evidence, not a fresh execution. |
| `reports/verification.json` | 2,244 | Saved output or verification claim; read as historical evidence, not a fresh execution. |
| `requirements-core.lock` | 738 | Dependencies and packaging; current CI installed successfully. |
| `requirements-linux.lock` | 763 | Dependencies and packaging; current CI installed successfully. |
| `requirements-macos.lock` | 1,198 | Dependencies and packaging; current CI installed successfully. |
| `scripts/analyze_extraction.py` | 3,978 | Preparation, inspection or report helper; code reviewed and syntax parsed. |
| `scripts/audit_snapshot.py` | 16,794 | Preparation, inspection or report helper; code reviewed and syntax parsed. |
| `scripts/build_research_report.py` | 14,780 | Preparation, inspection or report helper; code reviewed and syntax parsed. |
| `scripts/download_text_resources.py` | 1,122 | Preparation, inspection or report helper; code reviewed and syntax parsed. |
| `scripts/lock_environment.py` | 1,080 | Preparation, inspection or report helper; code reviewed and syntax parsed. |
| `scripts/prepare_release.py` | 1,544 | Preparation, inspection or report helper; code reviewed and syntax parsed. |
| `scripts/prepare_sources.py` | 840 | Preparation, inspection or report helper; code reviewed and syntax parsed. |
| `sql/phase1/schema_audit.sql` | 13,236 | Read-only schema audit queries; no database rerun. |
| `sql/phase2/trial_features.sql` | 2,686 | Trial-level aggregation; joins and approved baseline fields reviewed. |
| `src/clinical_trial_risk/__init__.py` | 73 | Python package marker; syntax parsed. |
| `src/clinical_trial_risk/api/__init__.py` | 0 | Python package marker; syntax parsed. |
| `src/clinical_trial_risk/api/app.py` | 2,353 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/api/index.html` | 6,166 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/evaluation/__init__.py` | 0 | Python package marker; syntax parsed. |
| `src/clinical_trial_risk/evaluation/prediction.py` | 11,190 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/features/__init__.py` | 0 | Python package marker; syntax parsed. |
| `src/clinical_trial_risk/features/build.py` | 3,689 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/features/embeddings.py` | 2,145 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/llm/__init__.py` | 0 | Python package marker; syntax parsed. |
| `src/clinical_trial_risk/llm/benchmark.py` | 5,880 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/llm/extract.py` | 7,619 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/models/__init__.py` | 0 | Python package marker; syntax parsed. |
| `src/clinical_trial_risk/models/train.py` | 7,975 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/reporting/__init__.py` | 0 | Python package marker; syntax parsed. |
| `src/clinical_trial_risk/reporting/evaluate.py` | 7,358 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `src/clinical_trial_risk/reporting/packets.py` | 9,910 | Workflow implementation; reviewed in its input/output context and syntax checked for Python. |
| `tests/test_api.py` | 532 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
| `tests/test_cohort.py` | 1,637 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
| `tests/test_evaluation.py` | 695 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
| `tests/test_extraction.py` | 882 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
| `tests/test_features.py` | 549 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
| `tests/test_integration.py` | 1,938 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
| `tests/test_reporting.py` | 1,420 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
| `tests/test_sql.py` | 1,364 | Project test definition reviewed; seven collection failures confirmed in GitHub CI. |
