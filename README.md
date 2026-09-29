# Clinical Trial Feasibility & Early-Termination Risk Intelligence Platform

Applied clinical data science project using AACT / ClinicalTrials.gov public registry data.

## Current status

**Phase 1 — Data and problem definition.** No model training is allowed yet.

Current deliverables:
- AACT / ClinicalTrials.gov schema notes
- prediction cohort proposal
- prediction timestamp definition
- label and follow-up rules
- historical snapshot coverage audit
- leakage register
- feature-availability dictionary
- repository skeleton

## Primary research question

Can we identify clinical trials at elevated risk of early termination using only information that would have been available at or near study start, and explain the factors associated with the predicted risk?

## Phase-1 rule

Do not begin model training until the data source, cohort, prediction timestamp, labels, follow-up rules, and leakage controls are documented and judged feasible.

## Data policy

Large AACT snapshots, raw data, derived datasets, credentials, and local artifacts are not committed to Git.
