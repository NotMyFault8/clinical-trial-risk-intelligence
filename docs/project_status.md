# Project status and remaining gates

Saved local research results are available, but clean-checkout reproducibility is
blocked by the findings in the [repository audit](../reports/github_repository_audit_2026-10-07.md).
The full release standard is **not** met: failed LLM components are withheld and
independent report review remains unperformed. No clinical or prospective
validation is claimed.

| Phase | Evidence | Status |
|---|---|---|
| 1. Sources and problem definition | Eight pinned archives; conservative 90-day interval rule; five-year matched status sources; explicit conditional estimand | Feasible for limited retrospective research |
| 2. Cohort and SQL | 5,703 primary trials; child aggregation before joins; unique keys, source-date checks and separate outcomes | Passed measured data checks |
| 3. Predictive comparisons | Six families, fixed temporal splits, calibration, cluster intervals and sensitivities | Evaluated; no reliable TF-IDF AP gain established |
| 4. Extraction | External human-annotated CHIA test, rules comparison, error analysis and operating measurements | Research experiment complete; semantic release failed |
| 5. Reports | Typed packets, deterministic templates, 40 generated-report test cases, review forms | Templates verified; free-form generation failed; human review pending |
| 6. Local packaging | API/dashboard, source/model checksums, container, dependency locks, CI configuration and monitoring | 24 local tests and 23 serving-container tests passed |

## Verification and repository readiness

Historical local records report 632 verified evidence packets, 24 local tests,
23 serving-container tests and 30 in-process API measurements. These records are
preserved in `reports/verification.json`; they are not a fresh verification of the
published checkout. The phase table above summarizes those saved results.

The repository audit of commit `a0f2fd9183197b16340de9f3834f7bb3a6ab43e0`
confirmed seven GitHub Actions test-collection failures caused by the missing
`clinical_trial_risk.data` package. The root ignore rule also matches that source
directory. Other outstanding findings include non-placeholder credentials in the
example configuration, incomplete input-hash enforcement, and an existing-output
guard that blocks the documented holdout reproduction workflow. See the audit for
evidence and remediation details. This documentation update does not resolve those
implementation findings or establish passing CI.

## Release gates

- Resolve the repository audit findings and verify a clean-checkout workflow.
- Complete independent semantic and analyst-usefulness review using
  [the report review rubric](report_review_rubric.md).
- Evaluate any revised extractor or generator on a fresh held-out benchmark after
  development; published tests must not become a repeated tuning target.
- Establish prospective validity before claiming deployment on new trials.

## Operational references

The local application is served at `http://127.0.0.1:8000` when its required
package and artifacts are available. Raw data, weights, caches and the virtual
environment are excluded from version control. No public deployment is established.

See the [research report](../reports/research_report.md) for measured results and
the [reproduction runbook](reproducibility.md) for environment and execution steps.
