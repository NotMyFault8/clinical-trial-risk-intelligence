# AACT schema audit report

**Phase 1 — current live database audit | 29 September 2026**

Measured at **2026-09-29T17:24:58.35717 America/Toronto** (2026-09-29T21:24:58.35717+00:00 UTC offset included). Database: `aact`; schema: `ctgov`. All report queries ran in one **read-only, repeatable-read transaction**. This preserves a consistent database view during this run; it does not create a reusable historical AACT archive.

## Findings at a glance

The database contains **604,729 study rows** and **604,729 distinct NCT IDs**, with **0 missing IDs** and **0 excess rows for repeated non-null IDs**. The measurements below describe the live database, not the final prediction cohort.

**Join findings:** the measured maximum rows per ID and missing-coverage counts in section 4 determine which joins preserve one row per trial. Section 6 checks whether each study has exactly one lead sponsor.

**Cohort-filter check:** the original anticipated-only filter yields 0 future-start trials. Including `estimated` yields 2,198 / 3,160 / 3,601 trials within 30 / 60 / 90 days in the current-date diagnostic. See section 5 for observed vocabulary. Historical source vocabularies must be verified before applying this mapping to archives.

| Audit section | Outcome |
| --- | --- |
| 1. Relation inventory | 71 visible relations inventoried |
| 2. Core column inventory | 123 columns across 7 present candidate tables |
| 3. Study ID uniqueness | PASS |
| 4. Related-table cardinality | Measured, including missing coverage and orphan IDs |
| 5. Type/status distributions | Measured; exact database vocabulary retained |
| 6. Lead-sponsor cardinality | Measured with all studies as the denominator |
| 7. Historical pre-start candidate counts | NOT MEASURED: historical snapshot/date not supplied; current-date diagnostic reported separately |
| 8. study_records | UNAVAILABLE in queried database catalog |

## 1. Table inventory

| Relation type | Count |
| --- | --- |
| BASE TABLE | 52 |
| VIEW | 19 |

The original `information_schema.tables` query includes visible tables and views. These counts describe schema objects, not trials. The complete relation list is in Appendix A.

## 2. Core columns and field types

| Candidate table | Visible columns |
| --- | --- |
| studies | 71 |
| designs | 14 |
| eligibilities | 14 |
| sponsors | 5 |
| conditions | 4 |
| interventions | 5 |
| facilities | 10 |
| study_records | Absent |

The full column names, types, positions, and schema nullability are in Appendix B. `is_nullable = YES` means the schema permits NULL; it does not establish that any observed values are missing. This audit measures key-ID and selected date missingness, not every feature’s completeness.

Current field details: `studies.start_date` and `study_first_posted_date` are dates; `enrollment` is integer; `eligibilities.minimum_age` and `maximum_age` are strings requiring later unit-aware parsing; `healthy_volunteers` is boolean; `criteria` is text; the eligibility sex/gender field is named `gender` in this database.

## 3. One row per study

| Metric | Measured value |
| --- | --- |
| total_rows | 604,729 |
| distinct_nct_ids | 604,729 |
| null_nct_ids | 0 |
| extra_nonnull_id_rows | 0 |
| original_duplicate_rows_metric | 0 |

The duplicate-ID listing returned **0 rows**. It lists only IDs satisfying `HAVING COUNT(*) > 1`; an empty result is expected when no IDs repeat. `LIMIT 100` caps the examples shown, not the number of groups checked.

The original `COUNT(*) - COUNT(DISTINCT nct_id)` includes both excess duplicate rows and rows with NULL IDs. The additional checks separate those cases. The observed grain is one row per NCT ID when both counts are zero. Recheck this for each historical source and after joins.

## 4. Related-table cardinality and join coverage

| Table | Source rows | Distinct IDs | Max rows/ID | Mean rows/ID | IDs with >1 row | Studies without rows | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| designs | 599,938 | 599,938 | 1 | 1.0 | 0 | 4,791 | 99.21% |
| eligibilities | 603,748 | 603,748 | 1 | 1.0 | 0 | 981 | 99.84% |
| sponsors | 963,830 | 604,729 | 180 | 1.594 | 190,809 | 0 | 100.00% |
| conditions | 1,087,552 | 603,710 | 343 | 1.801 | 221,232 | 1,019 | 99.83% |
| interventions | 1,022,931 | 543,426 | 97 | 1.882 | 286,892 | 61,303 | 89.86% |
| facilities | 3,533,271 | 544,000 | 3,510 | 6.495 | 144,488 | 60,729 | 89.96% |

Coverage = studies with at least one matching record ÷ all studies. Maximum and mean use non-null IDs present in the source table. Repeated IDs in one-to-many tables are expected; they are not evidence of duplicated real-world entities.

| Table | Rows with NULL NCT ID | Orphan NCT IDs |
| --- | --- | --- |
| designs | 0 | 0 |
| eligibilities | 0 | 0 |
| sponsors | 0 | 0 |
| conditions | 0 | 0 |
| interventions | 0 | 0 |
| facilities | 0 | 0 |

An orphan ID appears in the related table without a matching `studies` row. Semantic duplicate sponsors, interventions, or facilities are not tested by these counts.

**Correction to section 4:** after `GROUP BY nct_id`, outer `COUNT(*)` counts groups, not original rows. The original `designs.rows` is therefore mislabeled. This report uses `SUM(n)` for source rows and counts non-null IDs separately. Other original queries provide only trial coverage and maximum multiplicity; the report adds total rows, missing coverage, null IDs, and orphans.

**Join decision:** tables with at most one row per NCT ID can be left-joined after uniqueness checks. Aggregate each one-to-many table to trial level before joining. Missing child records should remain visible rather than silently excluding studies through an inner join. For example, 3 interventions joined directly to 10 facilities can produce 30 rows for one trial.

## 5. Study type, date type, enrollment type, and status

### study_type

| Observed value | Trials | % of all studies |
| --- | --- | --- |
| INTERVENTIONAL | 461,518 | 76.32% |
| OBSERVATIONAL | 141,162 | 23.34% |
| EXPANDED_ACCESS | 1,068 | 0.18% |
| NULL | 981 | 0.16% |

### start_date_type

| Observed value | Trials | % of all studies |
| --- | --- | --- |
| ACTUAL | 356,016 | 58.87% |
| NULL | 186,225 | 30.79% |
| ESTIMATED | 62,488 | 10.33% |

### enrollment_type

| Observed value | Trials | % of all studies |
| --- | --- | --- |
| ACTUAL | 375,829 | 62.15% |
| ESTIMATED | 211,769 | 35.02% |
| NULL | 17,131 | 2.83% |

### overall_status

| Observed value | Trials | % of all studies |
| --- | --- | --- |
| COMPLETED | 330,415 | 54.64% |
| UNKNOWN | 96,829 | 16.01% |
| RECRUITING | 65,069 | 10.76% |
| TERMINATED | 34,387 | 5.69% |
| NOT_YET_RECRUITING | 29,967 | 4.96% |
| ACTIVE_NOT_RECRUITING | 22,146 | 3.66% |
| WITHDRAWN | 16,817 | 2.78% |
| ENROLLING_BY_INVITATION | 5,268 | 0.87% |
| SUSPENDED | 1,782 | 0.29% |
| WITHHELD | 981 | 0.16% |
| NO_LONGER_AVAILABLE | 536 | 0.09% |
| AVAILABLE | 254 | 0.04% |
| APPROVED_FOR_MARKETING | 242 | 0.04% |
| TEMPORARILY_NOT_AVAILABLE | 36 | 0.01% |

Each distribution uses all studies as its denominator, including NULL values. The literal values above should drive source-specific mappings; conceptual labels in the cohort specification may differ in case or spelling.

Missingness deserves follow-up: 186,225 studies (30.79%) have NULL start-date type. Overlap between missing fields, missing child records, and particular statuses has not been measured; equal counts alone do not establish overlap.

Across all study types, Completed + Terminated contains **364,802 records (60.32%)**; Terminated represents **9.43%** of this restricted group. The remaining **239,927 records (39.68%)** have other statuses. These descriptive figures are not the termination probability of newly starting trials.

### Additional check: interventional studies only

| Status | Interventional trials | % of interventional studies |
| --- | --- | --- |
| COMPLETED | 258,624 | 56.04% |
| UNKNOWN | 66,971 | 14.51% |
| RECRUITING | 47,520 | 10.30% |
| TERMINATED | 29,850 | 6.47% |
| NOT_YET_RECRUITING | 22,615 | 4.90% |
| ACTIVE_NOT_RECRUITING | 17,177 | 3.72% |
| WITHDRAWN | 13,855 | 3.00% |
| ENROLLING_BY_INVITATION | 3,450 | 0.75% |
| SUSPENDED | 1,456 | 0.32% |

Completed-versus-Terminated analysis selects resolved outcomes. Other statuses require separate treatment, and historical follow-up maturity remains unmeasured. Do not turn every other status into a negative class.

## 6. Lead-sponsor cardinality

| Lead sponsor rows per trial | Trials (all studies) | Of these: no sponsor rows | % of all studies |
| --- | --- | --- | --- |
| 1 | 604,729 | 0 | 100.00% |

Lead rows are identified with `LOWER(COALESCE(lead_or_collaborator, '')) = 'lead'`. This checks lead-row count, not independent organizational identity.

| Raw sponsor role | Sponsor rows |
| --- | --- |
| lead | 604,729 |
| collaborator | 359,101 |

For comparison, the original query starts from `sponsors` and omits studies without sponsor records:

| Lead count | Trials in original grouped query |
| --- | --- |
| 1 | 604,729 |

The all-studies left join is needed to detect zero-coverage trials. If the two distributions agree, the correction has no numerical effect for this database version, but still makes the audit robust.

## 7. Prediction-window diagnostic — current records only

**Historical cohort result: not available.** The original query contains `DATE 'YYYY-MM-DD'`, which is a placeholder, not a valid date. A valid historical result requires that archive’s actual data and date. Substituting an old date into today’s live database does not reconstruct what was known then.

For a separate live diagnostic, the reference date is **2026-09-29**. Both variants require interventional study type, a non-null future start date, and first-posted date no later than that reference date. The first preserves the script’s `anticipated` test; the second explicitly includes `estimated` as an additional candidate spelling, without approving a historical crosswalk.

| Start-date-type filter | Within 30 days | Within 60 days | Within 90 days | All future planned starts |
| --- | --- | --- | --- | --- |
| anticipated only (original) | 0 | 0 | 0 | 0 |
| anticipated or estimated (diagnostic) | 2,198 | 3,160 | 3,601 | 5,035 |

The windows are nested, not mutually exclusive. “All future” has no 90-day upper limit. These counts do not select the first eligible historical snapshot, measure follow-up, or establish historical predictor availability. A zero under an unmatched vocabulary filter is not proof that no planned-start trials exist.

| Additional current-record date audit | Value |
| --- | --- |
| interventional_trials | 461,518 |
| missing_start_date | 2,889 |
| missing_first_posted_date | 0 |
| date_comparable_trials | 458,629 |
| first_posted_after_current_start_date | 222,903 |
| minimum_first_posted | 1999-09-20 |
| maximum_first_posted | 2026-09-28 |

The current-record first-posted-after-start comparison is **48.60%** of interventional trials with both dates present. This is a late-public-posting diagnostic using the currently recorded start date; it is not a verified historical late-registration exclusion count. First posting differs from first submission, dates can change, and date precision needs separate audit.

## 8. study_records availability

**No relation named `study_records` was found in the database catalog in any schema.** It is also absent from the visible column inventory. Therefore both original section-8 queries are unavailable here; counts and duplicate listings must be reported as **N/A, not zero**. There is no evidence from this audit that this database provides a historical-version table under that name.

## Changes needed in the audit workflow

1. Correct the `designs` source-row count and distinguish null IDs from duplicate IDs.
2. Check related-table coverage and orphan IDs before joining.
3. Count lead sponsors from the full studies population.
4. Replace the section-7 placeholder only with an explicit, source-matched date; label live diagnostics separately.
5. Validate start-date-type vocabulary per source era before applying cohort filters.
6. Treat absent `study_records` as a schema mismatch and do not run those statements blindly.
7. Save measured outputs alongside the exact executed SQL and source manifest.

The original project SQL was not overwritten. `executed_audit.sql` is the corrected companion used for these measurements. It deliberately omits SELECTs against the absent relation and includes the explicit diagnostics above.

## Phase 1 conclusion and remaining gates

This run establishes current-schema structure, observed table grain, coverage, and status/type distributions. It supports designing trial-level aggregation. It does **not** establish historical point-in-time feasibility or authorize model training.

Still required: historical archive coverage and hashes; schema/vocabulary drift across selected archives; historical first-eligible-snapshot counts for 30/60/90 days; predictor availability; follow-up and unresolved-outcome audit; frozen outcome source; final cohort and estimand decisions. No baseline feature is approved solely because it exists in today’s database.

## Evidence and reproducibility

- `audit_results.json`: all measured query outputs and source/query hashes.
- `executed_audit.sql`: exact SQL used, including transaction settings.
- `schema_audit_original.sql`: read-only copy of the user’s audited script.
- `collect_audit.py`: collector; credentials supplied from a local file and never included in report outputs.
- `build_report.py`: report generation and reconciliation checks.

Original SQL SHA-256: `72cc7d8f8687c21aa3f5be99963aa900a4858494f6ccbf34db074c733715c372`.

Executed SQL SHA-256: `f33e5a732b63265ba4ad10d07bb211b7a6951549cd31f8959ac0b396c4b84814`.

Validation passed: all four full-study distributions reconcile to the study total; the interventional status distribution reconciles to interventional count; lead-sponsor groups reconcile to all studies; each child-table coverage reconciles after accounting for orphan IDs; prediction-window counts are nested. Displayed percentages are rounded to two decimals and may not sum to exactly 100%. Live reruns may produce different counts.

## Appendix A — complete visible relation inventory

| Relation | Type |
| --- | --- |
| all_browse_conditions | VIEW |
| all_browse_interventions | VIEW |
| all_cities | VIEW |
| all_conditions | VIEW |
| all_countries | VIEW |
| all_design_outcomes | VIEW |
| all_facilities | VIEW |
| all_group_types | VIEW |
| all_id_information | VIEW |
| all_intervention_types | VIEW |
| all_interventions | VIEW |
| all_keywords | VIEW |
| all_overall_official_affiliations | VIEW |
| all_overall_officials | VIEW |
| all_primary_outcome_measures | VIEW |
| all_secondary_outcome_measures | VIEW |
| all_sponsors | VIEW |
| all_states | VIEW |
| baseline_counts | BASE TABLE |
| baseline_measurements | BASE TABLE |
| brief_summaries | BASE TABLE |
| browse_conditions | BASE TABLE |
| browse_interventions | BASE TABLE |
| calculated_values | BASE TABLE |
| categories | VIEW |
| central_contacts | BASE TABLE |
| conditions | BASE TABLE |
| countries | BASE TABLE |
| design_group_interventions | BASE TABLE |
| design_groups | BASE TABLE |
| design_outcomes | BASE TABLE |
| designs | BASE TABLE |
| detailed_descriptions | BASE TABLE |
| documents | BASE TABLE |
| drop_withdrawals | BASE TABLE |
| eligibilities | BASE TABLE |
| facilities | BASE TABLE |
| facility_contacts | BASE TABLE |
| facility_investigators | BASE TABLE |
| id_information | BASE TABLE |
| intervention_other_names | BASE TABLE |
| interventions | BASE TABLE |
| ipd_information_types | BASE TABLE |
| keywords | BASE TABLE |
| links | BASE TABLE |
| mesh_headings | BASE TABLE |
| mesh_terms | BASE TABLE |
| milestones | BASE TABLE |
| outcome_analyses | BASE TABLE |
| outcome_analysis_groups | BASE TABLE |
| outcome_counts | BASE TABLE |
| outcome_measurements | BASE TABLE |
| outcomes | BASE TABLE |
| overall_officials | BASE TABLE |
| participant_flows | BASE TABLE |
| pending_results | BASE TABLE |
| provided_documents | BASE TABLE |
| reported_event_totals | BASE TABLE |
| reported_events | BASE TABLE |
| responsible_parties | BASE TABLE |
| result_agreements | BASE TABLE |
| result_contacts | BASE TABLE |
| result_groups | BASE TABLE |
| retractions | BASE TABLE |
| search_results | BASE TABLE |
| search_term_results | BASE TABLE |
| search_terms | BASE TABLE |
| sponsors | BASE TABLE |
| studies | BASE TABLE |
| study_references | BASE TABLE |
| study_searches | BASE TABLE |

## Appendix B — complete core column inventory

### conditions

| Position | Column | Data type | Nullable in schema |
| --- | --- | --- | --- |
| 1 | id | integer | NO |
| 2 | nct_id | character varying | YES |
| 3 | name | character varying | YES |
| 4 | downcase_name | character varying | YES |

### designs

| Position | Column | Data type | Nullable in schema |
| --- | --- | --- | --- |
| 1 | id | integer | NO |
| 2 | nct_id | character varying | YES |
| 3 | allocation | character varying | YES |
| 4 | intervention_model | character varying | YES |
| 5 | observational_model | character varying | YES |
| 6 | primary_purpose | character varying | YES |
| 7 | time_perspective | character varying | YES |
| 8 | masking | character varying | YES |
| 9 | masking_description | text | YES |
| 10 | intervention_model_description | text | YES |
| 11 | subject_masked | boolean | YES |
| 12 | caregiver_masked | boolean | YES |
| 13 | investigator_masked | boolean | YES |
| 14 | outcomes_assessor_masked | boolean | YES |

### eligibilities

| Position | Column | Data type | Nullable in schema |
| --- | --- | --- | --- |
| 1 | id | integer | NO |
| 2 | nct_id | character varying | YES |
| 3 | sampling_method | character varying | YES |
| 4 | gender | character varying | YES |
| 5 | minimum_age | character varying | YES |
| 6 | maximum_age | character varying | YES |
| 7 | healthy_volunteers | boolean | YES |
| 8 | population | text | YES |
| 9 | criteria | text | YES |
| 10 | gender_description | text | YES |
| 11 | gender_based | boolean | YES |
| 12 | adult | boolean | YES |
| 13 | child | boolean | YES |
| 14 | older_adult | boolean | YES |

### facilities

| Position | Column | Data type | Nullable in schema |
| --- | --- | --- | --- |
| 1 | id | integer | NO |
| 2 | nct_id | character varying | YES |
| 3 | status | character varying | YES |
| 4 | name | character varying | YES |
| 5 | city | character varying | YES |
| 6 | state | character varying | YES |
| 7 | zip | character varying | YES |
| 8 | country | character varying | YES |
| 9 | latitude | numeric | YES |
| 10 | longitude | numeric | YES |

### interventions

| Position | Column | Data type | Nullable in schema |
| --- | --- | --- | --- |
| 1 | id | integer | NO |
| 2 | nct_id | character varying | YES |
| 3 | intervention_type | character varying | YES |
| 4 | name | character varying | YES |
| 5 | description | text | YES |

### sponsors

| Position | Column | Data type | Nullable in schema |
| --- | --- | --- | --- |
| 1 | id | integer | NO |
| 2 | nct_id | character varying | YES |
| 3 | agency_class | character varying | YES |
| 4 | lead_or_collaborator | character varying | YES |
| 5 | name | character varying | YES |

### studies

| Position | Column | Data type | Nullable in schema |
| --- | --- | --- | --- |
| 1 | nct_id | character varying | YES |
| 2 | nlm_download_date_description | character varying | YES |
| 3 | study_first_submitted_date | date | YES |
| 4 | results_first_submitted_date | date | YES |
| 5 | disposition_first_submitted_date | date | YES |
| 6 | last_update_submitted_date | date | YES |
| 7 | study_first_submitted_qc_date | date | YES |
| 8 | study_first_posted_date | date | YES |
| 9 | study_first_posted_date_type | character varying | YES |
| 10 | results_first_submitted_qc_date | date | YES |
| 11 | results_first_posted_date | date | YES |
| 12 | results_first_posted_date_type | character varying | YES |
| 13 | disposition_first_submitted_qc_date | date | YES |
| 14 | disposition_first_posted_date | date | YES |
| 15 | disposition_first_posted_date_type | character varying | YES |
| 16 | last_update_submitted_qc_date | date | YES |
| 17 | last_update_posted_date | date | YES |
| 18 | last_update_posted_date_type | character varying | YES |
| 19 | start_month_year | character varying | YES |
| 20 | start_date_type | character varying | YES |
| 21 | start_date | date | YES |
| 22 | verification_month_year | character varying | YES |
| 23 | verification_date | date | YES |
| 24 | completion_month_year | character varying | YES |
| 25 | completion_date_type | character varying | YES |
| 26 | completion_date | date | YES |
| 27 | primary_completion_month_year | character varying | YES |
| 28 | primary_completion_date_type | character varying | YES |
| 29 | primary_completion_date | date | YES |
| 30 | target_duration | character varying | YES |
| 31 | study_type | character varying | YES |
| 32 | acronym | character varying | YES |
| 33 | baseline_population | text | YES |
| 34 | brief_title | text | YES |
| 35 | official_title | text | YES |
| 36 | overall_status | character varying | YES |
| 37 | last_known_status | character varying | YES |
| 38 | phase | character varying | YES |
| 39 | enrollment | integer | YES |
| 40 | enrollment_type | character varying | YES |
| 41 | source | character varying | YES |
| 42 | limitations_and_caveats | character varying | YES |
| 43 | number_of_arms | integer | YES |
| 44 | number_of_groups | integer | YES |
| 45 | why_stopped | character varying | YES |
| 46 | has_expanded_access | boolean | YES |
| 47 | expanded_access_type_individual | boolean | YES |
| 48 | expanded_access_type_intermediate | boolean | YES |
| 49 | expanded_access_type_treatment | boolean | YES |
| 50 | has_dmc | boolean | YES |
| 51 | is_fda_regulated_drug | boolean | YES |
| 52 | is_fda_regulated_device | boolean | YES |
| 53 | is_unapproved_device | boolean | YES |
| 54 | is_ppsd | boolean | YES |
| 55 | is_us_export | boolean | YES |
| 56 | biospec_retention | character varying | YES |
| 57 | biospec_description | text | YES |
| 58 | ipd_time_frame | character varying | YES |
| 59 | ipd_access_criteria | character varying | YES |
| 60 | ipd_url | character varying | YES |
| 61 | plan_to_share_ipd | character varying | YES |
| 62 | plan_to_share_ipd_description | character varying | YES |
| 63 | created_at | timestamp without time zone | NO |
| 64 | updated_at | timestamp without time zone | NO |
| 65 | source_class | character varying | YES |
| 66 | delayed_posting | boolean | YES |
| 67 | expanded_access_nctid | character varying | YES |
| 68 | expanded_access_status_for_nctid | character varying | YES |
| 69 | fdaaa801_violation | boolean | YES |
| 70 | baseline_type_units_analyzed | character varying | YES |
| 71 | patient_registry | boolean | YES |

