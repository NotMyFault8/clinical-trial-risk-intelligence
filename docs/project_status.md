# Project status and remaining gates

The local research implementation and automated evaluation are complete. The full
original release standard is **not** met: failed LLM components are withheld and
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

All 632 portfolio report packets passed attribution reconstruction, typed-score
and exact-evidence checks. Thirty API requests were measured in-process. Browser
visual review was blocked because the tool could not verify its admin policy;
the dashboard script passed syntax checks. Remote GitHub Actions was not run.

The local app runs at http://127.0.0.1:8000 with access logs disabled. Changes are
local and uncommitted; nothing was pushed or publicly deployed. Earlier user
changes and synced references were preserved. Raw data, weights, caches and the
virtual environment remain ignored by Git. No execution date/time was added to
new project manifests.

Start with reports/research_report.md, docs/reproducibility.md and
 docs/learning_guide.md. The remaining human work is described in
 docs/report_review_rubric.md. A new generator/extractor would need development
work and a fresh held-out benchmark, not repeated tuning on these published tests.
