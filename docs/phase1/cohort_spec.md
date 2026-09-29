# Prediction Cohort Specification

Status: **working point-in-time proposal — not locked**.

## Unit of analysis

One registered clinical trial, keyed by `nct_id`.

## Primary population

Primary working population: **interventional ClinicalTrials.gov studies**.

Reason: observational studies and interventional trials have materially different operational processes and design fields. Observational studies can later be evaluated as a separate sensitivity/generalization population rather than silently mixed into the primary cohort.

Do not exclude phase `N/A` by default; interventional device/behavioral studies may legitimately have no drug-development phase.

## Prediction occasion

The model should simulate a decision made from a historical registry snapshot before the trial starts.

Working forward-selection rule:

1. Traverse selected historical snapshots in chronological order.
2. Trial exists in the snapshot and is interventional.
3. Snapshot contains `start_date_type = 'Anticipated'`.
4. The snapshot-recorded start date is later than the snapshot date.
5. The snapshot-recorded start date is within the candidate prediction window.
6. Choose the **first** snapshot satisfying the rule for that `nct_id`.

Candidate prediction windows to audit: 30, 60, and 90 days. The snapshot date, not the later realized start date, is the model's prediction timestamp.

Trials registered only after starting, or without an eligible pre-start version, are not silently repaired from the current record; they are excluded from the primary cohort and counted.

## Initial exploratory outcome

From a frozen later AACT snapshot:

- `Completed` -> 0
- `Terminated` -> 1

Other statuses remain separate and are not recoded into the binary endpoint without justification.

This resolved-outcome comparison is useful for feasibility but does not automatically estimate termination probability for every newly registered trial. We must quantify selection from unresolved studies and follow-up time before locking the estimand.

## Candidate outcome cutoff

Working candidate: **2026-09-01 AACT monthly snapshot**.

## Follow-up

Minimum follow-up is not yet locked. Phase 1 must report unresolved-status prevalence versus time since prediction. A fixed-horizon or time-to-event/competing-event formulation remains open if resolved-outcome selection is material.

## Required exclusion accounting

The cohort-construction report must separately count:
- non-interventional records;
- retrospective/late registration;
- no historical pre-start snapshot;
- missing/invalid anticipated start date;
- never enters the predeclared prediction window;
- insufficient follow-up;
- unresolved/other status at ascertainment cutoff;
- schema/data-quality failures.

## Prohibited baseline information

Final status, `why_stopped`, actual completion information, realized enrollment, results data, and post-prediction registry updates cannot enter baseline predictors.

## Decisions still required before lock

- 30 vs 60 vs 90-day prediction window;
- study years included;
- minimum follow-up;
- binary resolved-outcome versus fixed-horizon/time-to-event primary estimand;
- handling of status corrections;
- exact status vocabulary across historical schema eras.
