# Phase 1 Data-Source Strategy

Status: **working decision; requires empirical snapshot audit before lock**.

## Source roles

### AACT historical snapshots — predictor source

Use historical AACT snapshots to reconstruct what the registry contained at the prediction timestamp. Do not construct baseline predictors from the current AACT row and then filter by historical dates.

Prefer the downloadable flat-file snapshots for longitudinal staging because they can be loaded selectively into our own PostgreSQL schema with an explicit `snapshot_date`. PostgreSQL dumps remain useful for spot-checking the native AACT schema.

AACT currently exposes historical monthly archives back to 2017, with daily recent snapshots. Snapshot schemas can change over time, so each selected archive must be accompanied by a manifest and schema mapping.

### AACT current/live database — schema discovery only

Use the live database for:
- current schema/data-dictionary exploration;
- validating table meanings;
- exploratory counts that are explicitly labeled current.

Do not use current/live values as pre-start features.

### Frozen future snapshot — outcome ascertainment

Candidate frozen outcome source: **2026-09-01 AACT monthly snapshot**.

Use a frozen snapshot rather than a moving live database so labels are reproducible. This date is provisional until the cohort follow-up audit is complete.

## Primary data grain

Final analytical grain: one row per `nct_id`.

Raw/staging grain: one row per source entity per `snapshot_date`.

Every staged record must carry:
- `snapshot_date`;
- source archive name;
- source file/table;
- archive checksum;
- ingestion run ID.

## Point-in-time prediction rule

Primary working rule for an interventional study:

1. Scan historical snapshots chronologically.
2. The trial must already exist in the snapshot.
3. `study_type = 'Interventional'`.
4. The source-specific planned-start value is present: the live audit observed `ESTIMATED`; verify whether each historical archive uses `Anticipated` or `ESTIMATED` before mapping it.
5. The start date recorded in that snapshot must be in the future.
6. The then-recorded planned start must be within a predeclared window after the snapshot; candidate window: 90 days.
7. Select the **first** snapshot satisfying the rule. That snapshot date becomes the prediction timestamp for the trial.

This forward rule avoids selecting a feature version using knowledge from later registry updates. Trials first registered only after starting, or trials lacking an eligible pre-start snapshot, are excluded from the primary point-in-time cohort and counted explicitly.

The 90-day window is provisional. Audit 30/60/90-day alternatives before locking it.

## Initial feasibility download strategy

Do not download every historical archive immediately.

Phase-1 pilot:
- download approximately one archive per year from 2018 onward plus the frozen outcome snapshot;
- verify schema drift, table cardinality, field availability, and approximate eligible-trial counts;
- estimate storage and ingestion cost.

If feasibility passes, expand to the monthly snapshots needed for the final prediction-window rule. If monthly volume is unnecessarily expensive, evaluate a predeclared quarterly-landmark design rather than silently subsampling snapshots.

## Core tables for the first audit

| Table | Expected use | Expected grain |
|---|---|---|
| `studies` | status, study type, phase, planned enrollment, registration/start dates, number of arms | one row per NCT ID |
| `designs` | allocation, masking, intervention model, primary purpose | verify; expected trial-level design row |
| `eligibilities` | criteria text, age, sex, healthy-volunteer fields | verify; expected trial-level eligibility row |
| `sponsors` | lead sponsor and collaborator attributes | one-to-many |
| `conditions` | condition counts/names; later therapeutic-area mapping | one-to-many |
| `interventions` | intervention types/counts/names | one-to-many |
| `facilities` | site count and geography | one-to-many |

`study_records` and `study_references` are excluded from the current scope by the user’s 2026-09-30 decision. Historical provenance will come from verified archives and manifests.

Derived AACT tables such as calculated counts should not be preferred automatically when the same value can be reproduced transparently from source entity tables.

## Outcome fields and isolation

Post-outcome fields such as `overall_status`, `why_stopped`, actual completion information, realized enrollment, and later registry updates belong in a physically/logically separate outcome layer.

For the exploratory binary target:
- Completed -> 0
- Terminated -> 1
- all other statuses remain separate until justified.

Do not use `why_stopped` or any retrospective reason taxonomy as a predictor.

## Open gates before Phase 1 exit

The following still require measured evidence:
- eligible trial count under 30/60/90-day prediction windows;
- frequency of retrospective registration;
- distribution of `start_date_type`;
- schema compatibility across selected years;
- unresolved-outcome rate by prediction year;
- amount of follow-up required for a stable binary endpoint;
- whether a fixed-horizon or time-to-event formulation is preferable;
- whether monthly snapshots are operationally justified versus a landmark design.

## Public source references

- AACT: https://aact.ctti-clinicaltrials.org/
- AACT snapshots: https://aact.ctti-clinicaltrials.org/snapshots/flat
- AACT data dictionary: https://aact.ctti-clinicaltrials.org/documentation
- ClinicalTrials.gov: https://clinicaltrials.gov/
