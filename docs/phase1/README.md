> Historical Phase-1 working notes. The audited cohort is now locked in [research_protocol.md](../research_protocol.md), with the approved [feature dictionary](../feature_dictionary.md). Earlier proposals below are retained as research history.

# Phase 1 — Data and Problem Definition

Phase 1 exists to determine whether a defensible historical prediction task can be constructed before any modeling begins.

## Exit deliverables

1. `schema_notes.md`
2. `cohort_spec.md`
3. `snapshot_audit.md`
4. `leakage_register.md`
5. `feature_availability_dictionary.md`
6. repository skeleton

## Exit question

Can we reconstruct, with sufficient fidelity, what information was available at the chosen prediction timestamp and then observe a sufficiently mature future outcome without contaminating predictors with post-outcome information?

## Current scope and audit workflow (2026-09-30)

`study_records` and `study_references` are outside scope. The seven core tables
are studies, designs, eligibilities, sponsors, conditions, interventions, and facilities.

The readable `sql/phase1/schema_audit.sql` is now the source of truth. Comments
of the form `-- query: name` identify individual result sets for the collector;
DBeaver ignores those comments and returns ordinary tables. Python reads these
same query blocks; it no longer holds a second copy of the audit SQL.

For manual use, replace the reference-date and source-kind placeholders before
running the provenance or prediction-window sections. Verify start-date-type
vocabulary in each source: the current database uses ESTIMATED; older snapshots
may use Anticipated. The two diagnostic filters make that difference visible.

For automated live collection, run from the repository root (use a fresh output
folder and the date matching the intended diagnostic):

```sh
python3 reports/phase1/schema_audit_2026-09-29/collect_audit.py \
  --credentials-file .env \
  --source-sql sql/phase1/schema_audit.sql \
  --reference-date 2026-09-30 \
  --source-kind current_live_database \
  --output-dir reports/generated/live_2026-09-30
```

Use your actual local connection-settings file for `--credentials-file`.
The collector refuses to overwrite a previous result bundle. Historical runs
also require the exact downloaded `--snapshot-id` and `--archive-sha256`; these
document provenance but do not independently verify which archive was restored.
Do not point historical runs at the live AACT server.

The report renderer accepts `--results-dir` for a saved live result bundle.
It deliberately stops on historical results because the old live-report prose
is not a valid interpretation of historical cohort feasibility.

The September 29 measured JSON, executed SQL, original SQL copy, and finished
report are preserved as evidence of that run. No new model or dataset is created
by this cleanup. Next: the small historical pilot in `snapshot_audit.md`.
