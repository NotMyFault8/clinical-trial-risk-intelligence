# AACT / ClinicalTrials.gov Schema Notes

Status: **initial live-database audit complete (2026-09-29); historical snapshot audit still required**.

## Database structure

AACT is a PostgreSQL relational representation of ClinicalTrials.gov with 40+ connected tables. The final analytical cohort will have one row per `nct_id`, but most source entities are not trial-level and therefore must be aggregated before joining.

AACT documentation explicitly describes `studies.txt` as one record per study with `nct_id` as the unique identifier. All other cardinalities below remain subject to direct SQL verification on the snapshots we actually use.

## Core candidate tables

| Table | Important fields / role | Cardinality expectation |
|---|---|---|
| `studies` | `nct_id`, study type, overall status, phase, enrollment, enrollment type, first-posted/submitted dates, start date/type, completion fields, number of arms, why stopped | one per trial |
| `designs` | allocation, masking, intervention model, observational model, primary purpose, time perspective | verify uniqueness by `nct_id` |
| `eligibilities` | criteria text, minimum/maximum age, sex/gender field, healthy volunteers | verify uniqueness by `nct_id` |
| `sponsors` | sponsor name/class and lead-versus-collaborator role | one-to-many |
| `conditions` | condition names | one-to-many |
| `interventions` | intervention name/type | one-to-many |
| `facilities` | facility, city/state/country, latitude/longitude, site status | one-to-many |

The live audit found one row per study, at most one design and eligibility row per NCT ID, and one-to-many sponsor/condition/intervention/facility tables. See the dated report for measured coverage. Historical sources must be checked independently. `study_records` was absent from the live database; both it and `study_references` are outside scope following the 2026-09-30 project decision.

## Fields already confirmed in the current AACT data dictionary

- `studies.study_first_posted_date`
- `studies.study_first_submitted_date`
- `studies.start_date`
- `studies.start_date_type`
- `studies.completion_date`
- `studies.enrollment`
- `studies.enrollment_type`
- `studies.why_stopped`
- `designs.primary_purpose`
- masking-role fields in `designs`
- `eligibilities.minimum_age`
- `eligibilities.maximum_age`
- eligibility sex/gender field
- `eligibilities.healthy_volunteers`
- `sponsors.agency_class`
- `sponsors.lead_or_collaborator`
- `interventions.name`
- `interventions.intervention_type`
- `facilities.country`

## Point-in-time warning

A field being conceptually 'baseline' does **not** prove the current value was available before study start. Planned enrollment, eligibility text, facilities, sponsors, interventions, dates, and design fields can be revised. Their predictor values must come from the selected historical snapshot itself.

`studies.created_at` and `updated_at` are AACT/database timestamps and must not be assumed to represent ClinicalTrials.gov field-level availability without validation.

## Schema-audit questions

1. Is `studies.nct_id` unique in every selected historical snapshot?
2. Are `designs` and `eligibilities` actually one row per trial in every schema era?
3. Which one-to-many tables contain duplicate semantic entities?
4. Is exactly one lead sponsor normally present?
5. How do field names/types change between 2018-2026 archives?
6. Which planned-enrollment vocabulary (Anticipated or ESTIMATED) appears in each source era?
7. How often is `start_date_type` planned (source-specific Anticipated/ESTIMATED), actual, or missing in candidate snapshots?
8. Which fields disappear, appear, or change coding across the ClinicalTrials.gov modernization period?

No field is approved for modeling until its availability time and historical-snapshot representation are documented.
