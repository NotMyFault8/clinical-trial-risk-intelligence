# AACT / ClinicalTrials.gov Schema Notes

Status: **not yet audited**.

## Trial-level grain

The final analytical cohort is intended to have one row per ClinicalTrials.gov trial (`nct_id`). AACT is relational, so one-to-many tables must be aggregated carefully before trial-level joins.

## Candidate source entities to verify

- studies
- designs / design information
- eligibilities
- sponsors
- conditions
- interventions
- facilities
- countries / geographic information
- outcomes, only where temporally appropriate

## Schema-audit questions

- What is the primary key / grain of each table?
- Which tables contain repeated rows per `nct_id`?
- Which fields correspond to planned versus actual quantities?
- Which fields can be revised after study start?
- Which timestamps/version fields allow reconstruction of point-in-time state?
- Which current AACT fields differ from historical snapshot schemas?

No field is approved for modeling until its availability time is documented.
