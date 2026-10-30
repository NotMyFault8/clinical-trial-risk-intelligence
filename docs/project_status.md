# Project status and remaining gates

Saved local research results are available. The missing source package and root
ignore-rule conflict in the [historical audit](../reports/github_repository_audit_2026-10-07.md)
were repaired by `4cb6985`; main CI passed at `62f5407` on 2026-10-08.
End-to-end reproduction still requires external archives/models and verification
of the remaining audit findings.
The full release standard is **not** met: failed LLM components are withheld and
independent report review remains unperformed. No clinical or prospective
validation is claimed.

| Phase | Evidence | Status |
|---|---|---|
| 1. Sources and problem definition | Eight pinned archives; conservative 90-day interval rule; five-year matched status sources; explicit conditional estimand | Feasible for limited retrospective research |
| 2. Cohort and SQL | 5,703 primary trials; child aggregation before joins; unique keys, source-date checks and separate outcomes | Passed measured data checks |
| 3. Predictive comparisons | Six families, fixed temporal splits, calibration, cluster intervals and sensitivities | Evaluated; no reliable TF-IDF AP gain established |
| 4. Extraction | Historical CHIA test and frozen 100-document V3 holdout; rules/NER/LLM comparisons; AI secondary review of 12 samples | Original-to-V3 F1 13.9% to 36.3% on the new holdout; below NER alone; semantic release failed |
| 5. Reports | Typed packets, deterministic templates, 40 generated-report test cases, review forms | Templates verified; free-form generation failed; human review pending |
| 6. Local packaging | API/dashboard, source/model checksums, container, dependency locks, CI configuration and monitoring | 24 local tests and 23 serving-container tests passed |

## Verification and repository readiness

Historical local records report 632 verified evidence packets, 24 local tests,
23 serving-container tests and 30 in-process API measurements. These records are
preserved in `reports/verification.json`; they are not a fresh verification of the
published checkout. The phase table above summarizes those saved results.

The 2026-10-30 extraction update passed 28 local non-integration tests (three
integration tests deselected). Frozen code/prediction hashes and independent exact
counts were checked in [V3 verification](../reports/extraction/llm_v3/verification.json).
[AI secondary review](../reports/extraction/llm_v3/ai_second_review.md) covers all
12 preselected samples. It does not establish independent clinical validity.

The repository audit of commit `a0f2fd9183197b16340de9f3834f7bb3a6ab43e0`
confirmed seven GitHub Actions test-collection failures caused by the missing
`clinical_trial_risk.data` package. That package and the ignore rule were repaired
on 2026-10-08. The subsequent [main-branch workflow](https://github.com/NotMyFault8/clinical-trial-risk-intelligence/actions/runs/37784370383)
passed. Other audit findings, including example-configuration credentials,
input-hash enforcement and the documented holdout-output workflow, require their
own verification; this extraction experiment does not claim to resolve them.

## Release gates

- Resolve the repository audit findings and verify a clean-checkout workflow.
- Complete independent semantic and analyst-usefulness review using
  [the report review rubric](report_review_rubric.md).
- Evaluate any revised extractor or generator on a fresh held-out benchmark after
  development; published tests must not become a repeated tuning target.
- Establish prospective validity before claiming deployment on new trials.

## Operational references

API v0.3.0 serves the saved V3 comparison, AI secondary review summaries, individual
case evidence and Markdown reports. The dashboard displays these results alongside
the historical portfolio. See [the API guide](api.md). Portfolio responses identify
their existing cohort extraction cache; V3 benchmark results are exposed separately.
The API update passed 37 non-integration tests and live HTTP checks against the
632-trial portfolio and saved extraction data. The [verification record](../reports/api/v0_3_verification.json)
also confirms the six V3 serving-bundle files and unchanged frozen inference hashes.

The local application is served at `http://127.0.0.1:8000` when its required
package and artifacts are available. Raw data, weights, caches and the virtual
environment are excluded from version control. No public deployment is established.

See the [research report](../reports/research_report.md) for measured results and
the [reproduction runbook](reproducibility.md) for environment and execution steps.
