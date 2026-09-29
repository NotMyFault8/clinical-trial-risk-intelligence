# Prediction Cohort Specification

Status: **proposal only — not locked**.

## Unit of analysis

One registered clinical trial, keyed by `nct_id`.

## Primary question

Predict elevated risk of early termination using information available at or near study start.

## Initial exploratory binary outcome

- `Completed` -> 0
- `Terminated` -> 1

This is not automatically the final population-risk estimand. Restricting analysis to trials with these observed outcomes conditions on outcome ascertainment and may induce selection issues.

## Decisions required before lock

- exact study types / phases / eras included
- prediction timestamp
- minimum follow-up
- outcome ascertainment cutoff
- handling of ongoing / unresolved studies
- handling of retrospective registration
- handling of reporting delay
- whether a fixed-horizon or time-to-event estimand is preferable
- exact status vocabulary and snapshot-specific mappings
