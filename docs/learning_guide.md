# Learning the implemented project

Start with the question and the source data, then follow one trial through the
pipeline. Avoid starting with the machine-learning library calls.

1. **SQL and cardinality.** Revisit `sql/phase1/schema_audit.sql`. An empty duplicate
   query means no ID groups satisfy `COUNT(*) > 1`, not that the table is empty.
   Then read `sql/phase2/trial_features.sql`: each repeated child is aggregated
   before joining. The SQL test deliberately uses multiple conditions,
   interventions and sites to show how an unaggregated join would inflate counts.
2. **Snapshot and cohort.** Read `data/cohort.py` and the research protocol. Compare
   a day-specific start with a month interval. Distinguish when a record was
   available, when a trial planned to start and when its status was observed.
   Explain why a current registry row cannot reconstruct historical features.
3. **Storage choices.** JSON holds named audit results, settings, manifests and
   nested evidence. Parquet holds typed rectangular trial tables. ZIPs preserve
   original source files. Joblib stores fitted estimators. JSON is convenient for
   small structured messages; it is not a rule that every SQL result must become
   JSON. Python automates the same logical queries and validations reproducibly.
4. **Features.** Read `features/build.py` with the feature dictionary. Separate
   planned from actual enrollment, an unlisted site from zero sites, raw words
   from inferred clinical concepts and metadata used for grouping from predictors.
5. **Training and evaluation.** Read `models/train.py`, then
   `evaluation/prediction.py`. Explain what each split is allowed to influence.
   Compare discrimination with calibration. Work through AP, Brier and top-K
   counts on a tiny example before interpreting the research figures.
6. **Extraction.** Read `llm/extract.py` and `llm/benchmark.py`. A valid JSON object
   is not necessarily true. Exact source support is not necessarily the correct
   clinical entity type. Review a false positive, false negative, invalid schema,
   ambiguous repeated span and truncated criterion from the error report.
7. **Reporting.** Read `reporting/packets.py`. Verify that base log-odds plus all
   contributions reproduces the calibrated probability. A positive contribution
   is an association in the model, not proof changing that feature improves a
   trial. Read the generation tests that deliberately invent a score or source.
8. **Serving.** Read `api/app.py`, inspect the browser API documentation, then
   inspect `scripts/prepare_release.py`. The serving bundle contains no outcome
   table or credentials. Serving a frozen historical portfolio is different from
   validating an online model on future trials.

For each component, answer: why it exists, what it assumes, what can fail, how it
was checked, what the measured result was and what claim the evidence does not
support. Use the saved negative results as part of the explanation. Do not turn
planned, withheld or unreviewed components into resume claims.
