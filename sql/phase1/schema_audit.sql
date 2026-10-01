-- Phase 1 AACT schema audit: the readable source used by collect_audit.py.
-- Run each SELECT/WITH block in DBeaver to see ordinary result tables.
-- The -- query: comments name results for Python; they are ignored by PostgreSQL.
-- Before running provenance or section 7 manually, replace YYYY-MM-DD with the
-- source-matched reference date and SOURCE_KIND with current_live_database or
-- historical_snapshot. Python supplies these through explicit arguments.
-- An old reference date against today's live database is NOT a historical audit.
-- study_records and study_references are outside the current project scope.
-- Recorded live finding on 2026-09-29: 604,729 unique, non-null NCT IDs.


-- 0. Record when and where this measurement was made.

-- query: provenance
SELECT current_database() AS database,
    transaction_timestamp() AS observed_at_utc,
    transaction_timestamp() AT TIME ZONE 'America/Toronto' AS observed_at_toronto,
    current_setting('transaction_read_only') AS read_only,
    current_setting('transaction_isolation') AS isolation,
    DATE 'YYYY-MM-DD' AS diagnostic_reference_date,
    'SOURCE_KIND' AS source_kind;

-- 1. Inventory tables and views.

-- query: table_inventory
SELECT table_name, table_type FROM information_schema.tables
    WHERE table_schema='ctgov' ORDER BY table_name;

-- 2. Inventory columns for the seven core tables.

-- query: column_inventory
SELECT table_name, ordinal_position, column_name, data_type, is_nullable
    FROM information_schema.columns WHERE table_schema='ctgov' AND table_name IN
    ('studies','designs','eligibilities','sponsors','conditions','interventions','facilities')
    ORDER BY table_name, ordinal_position;

-- 3. Check one row per NCT ID; separate NULL IDs from extra duplicate rows.

-- query: studies_uniqueness
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT nct_id) AS distinct_nct_ids,
    COUNT(*) FILTER (WHERE nct_id IS NULL) AS null_nct_ids,
    COUNT(nct_id)-COUNT(DISTINCT nct_id) AS extra_nonnull_id_rows,
    COUNT(*)-COUNT(DISTINCT nct_id) AS original_duplicate_rows_metric FROM ctgov.studies;

-- query: studies_duplicate_ids
SELECT nct_id, COUNT(*) AS n FROM ctgov.studies
    GROUP BY nct_id HAVING COUNT(*)>1 ORDER BY n DESC,nct_id LIMIT 100;

-- 4. Measure child-table grain, coverage, NULL IDs, and orphan IDs.
-- SUM(n) counts source rows; COUNT(nct_id) counts non-null ID groups.

-- query: cardinality_designs
WITH grouped AS (
        SELECT nct_id, COUNT(*) AS n FROM ctgov.designs GROUP BY nct_id)
        SELECT 'designs' AS table_name, COALESCE(SUM(n),0)::bigint AS source_rows,
        COUNT(nct_id) AS distinct_trial_ids,
        COALESCE(SUM(n) FILTER (WHERE nct_id IS NULL),0)::bigint AS null_id_rows,
        MIN(n) FILTER (WHERE nct_id IS NOT NULL) AS min_rows_per_present_trial,
        MAX(n) FILTER (WHERE nct_id IS NOT NULL) AS max_rows_per_present_trial,
        ROUND(AVG(n) FILTER (WHERE nct_id IS NOT NULL),3) AS mean_rows_per_present_trial,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND n>1) AS ids_with_multiple_rows,
        (SELECT COUNT(*) FROM ctgov.studies s WHERE NOT EXISTS
          (SELECT 1 FROM grouped g WHERE g.nct_id=s.nct_id)) AS studies_without_rows,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM ctgov.studies s WHERE s.nct_id=grouped.nct_id)) AS orphan_trial_ids
        FROM grouped;

-- query: cardinality_eligibilities
WITH grouped AS (
        SELECT nct_id, COUNT(*) AS n FROM ctgov.eligibilities GROUP BY nct_id)
        SELECT 'eligibilities' AS table_name, COALESCE(SUM(n),0)::bigint AS source_rows,
        COUNT(nct_id) AS distinct_trial_ids,
        COALESCE(SUM(n) FILTER (WHERE nct_id IS NULL),0)::bigint AS null_id_rows,
        MIN(n) FILTER (WHERE nct_id IS NOT NULL) AS min_rows_per_present_trial,
        MAX(n) FILTER (WHERE nct_id IS NOT NULL) AS max_rows_per_present_trial,
        ROUND(AVG(n) FILTER (WHERE nct_id IS NOT NULL),3) AS mean_rows_per_present_trial,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND n>1) AS ids_with_multiple_rows,
        (SELECT COUNT(*) FROM ctgov.studies s WHERE NOT EXISTS
          (SELECT 1 FROM grouped g WHERE g.nct_id=s.nct_id)) AS studies_without_rows,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM ctgov.studies s WHERE s.nct_id=grouped.nct_id)) AS orphan_trial_ids
        FROM grouped;

-- query: cardinality_sponsors
WITH grouped AS (
        SELECT nct_id, COUNT(*) AS n FROM ctgov.sponsors GROUP BY nct_id)
        SELECT 'sponsors' AS table_name, COALESCE(SUM(n),0)::bigint AS source_rows,
        COUNT(nct_id) AS distinct_trial_ids,
        COALESCE(SUM(n) FILTER (WHERE nct_id IS NULL),0)::bigint AS null_id_rows,
        MIN(n) FILTER (WHERE nct_id IS NOT NULL) AS min_rows_per_present_trial,
        MAX(n) FILTER (WHERE nct_id IS NOT NULL) AS max_rows_per_present_trial,
        ROUND(AVG(n) FILTER (WHERE nct_id IS NOT NULL),3) AS mean_rows_per_present_trial,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND n>1) AS ids_with_multiple_rows,
        (SELECT COUNT(*) FROM ctgov.studies s WHERE NOT EXISTS
          (SELECT 1 FROM grouped g WHERE g.nct_id=s.nct_id)) AS studies_without_rows,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM ctgov.studies s WHERE s.nct_id=grouped.nct_id)) AS orphan_trial_ids
        FROM grouped;

-- query: cardinality_conditions
WITH grouped AS (
        SELECT nct_id, COUNT(*) AS n FROM ctgov.conditions GROUP BY nct_id)
        SELECT 'conditions' AS table_name, COALESCE(SUM(n),0)::bigint AS source_rows,
        COUNT(nct_id) AS distinct_trial_ids,
        COALESCE(SUM(n) FILTER (WHERE nct_id IS NULL),0)::bigint AS null_id_rows,
        MIN(n) FILTER (WHERE nct_id IS NOT NULL) AS min_rows_per_present_trial,
        MAX(n) FILTER (WHERE nct_id IS NOT NULL) AS max_rows_per_present_trial,
        ROUND(AVG(n) FILTER (WHERE nct_id IS NOT NULL),3) AS mean_rows_per_present_trial,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND n>1) AS ids_with_multiple_rows,
        (SELECT COUNT(*) FROM ctgov.studies s WHERE NOT EXISTS
          (SELECT 1 FROM grouped g WHERE g.nct_id=s.nct_id)) AS studies_without_rows,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM ctgov.studies s WHERE s.nct_id=grouped.nct_id)) AS orphan_trial_ids
        FROM grouped;

-- query: cardinality_interventions
WITH grouped AS (
        SELECT nct_id, COUNT(*) AS n FROM ctgov.interventions GROUP BY nct_id)
        SELECT 'interventions' AS table_name, COALESCE(SUM(n),0)::bigint AS source_rows,
        COUNT(nct_id) AS distinct_trial_ids,
        COALESCE(SUM(n) FILTER (WHERE nct_id IS NULL),0)::bigint AS null_id_rows,
        MIN(n) FILTER (WHERE nct_id IS NOT NULL) AS min_rows_per_present_trial,
        MAX(n) FILTER (WHERE nct_id IS NOT NULL) AS max_rows_per_present_trial,
        ROUND(AVG(n) FILTER (WHERE nct_id IS NOT NULL),3) AS mean_rows_per_present_trial,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND n>1) AS ids_with_multiple_rows,
        (SELECT COUNT(*) FROM ctgov.studies s WHERE NOT EXISTS
          (SELECT 1 FROM grouped g WHERE g.nct_id=s.nct_id)) AS studies_without_rows,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM ctgov.studies s WHERE s.nct_id=grouped.nct_id)) AS orphan_trial_ids
        FROM grouped;

-- query: cardinality_facilities
WITH grouped AS (
        SELECT nct_id, COUNT(*) AS n FROM ctgov.facilities GROUP BY nct_id)
        SELECT 'facilities' AS table_name, COALESCE(SUM(n),0)::bigint AS source_rows,
        COUNT(nct_id) AS distinct_trial_ids,
        COALESCE(SUM(n) FILTER (WHERE nct_id IS NULL),0)::bigint AS null_id_rows,
        MIN(n) FILTER (WHERE nct_id IS NOT NULL) AS min_rows_per_present_trial,
        MAX(n) FILTER (WHERE nct_id IS NOT NULL) AS max_rows_per_present_trial,
        ROUND(AVG(n) FILTER (WHERE nct_id IS NOT NULL),3) AS mean_rows_per_present_trial,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND n>1) AS ids_with_multiple_rows,
        (SELECT COUNT(*) FROM ctgov.studies s WHERE NOT EXISTS
          (SELECT 1 FROM grouped g WHERE g.nct_id=s.nct_id)) AS studies_without_rows,
        COUNT(*) FILTER (WHERE nct_id IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM ctgov.studies s WHERE s.nct_id=grouped.nct_id)) AS orphan_trial_ids
        FROM grouped;

-- 5. Inspect exact source vocabulary and full-study distributions.

-- query: distribution_study_type
SELECT study_type AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY study_type ORDER BY trials DESC, value NULLS LAST;

-- query: distribution_start_date_type
SELECT start_date_type AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY start_date_type ORDER BY trials DESC, value NULLS LAST;

-- query: distribution_enrollment_type
SELECT enrollment_type AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY enrollment_type ORDER BY trials DESC, value NULLS LAST;

-- query: distribution_overall_status
SELECT overall_status AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY overall_status ORDER BY trials DESC, value NULLS LAST;

-- query: interventional_status_distribution
SELECT overall_status AS value, COUNT(*) AS trials,
    ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_interventional
    FROM ctgov.studies WHERE LOWER(study_type)='interventional'
    GROUP BY overall_status ORDER BY trials DESC,value NULLS LAST;

-- 6. Compare sponsor-only coverage with all-study coverage.

-- query: lead_sponsor_original
SELECT lead_count, COUNT(*) AS trials FROM (
    SELECT nct_id,COUNT(*) FILTER (WHERE LOWER(COALESCE(lead_or_collaborator,''))='lead') AS lead_count
    FROM ctgov.sponsors GROUP BY nct_id) x GROUP BY lead_count ORDER BY lead_count;

-- query: lead_sponsor_all_studies
WITH counts AS (
    SELECT nct_id, COUNT(*) AS sponsor_rows,
    COUNT(*) FILTER (WHERE LOWER(COALESCE(lead_or_collaborator,''))='lead') AS lead_count
    FROM ctgov.sponsors GROUP BY nct_id)
    SELECT COALESCE(c.lead_count,0) AS lead_count, COUNT(*) AS trials,
    COUNT(*) FILTER (WHERE c.nct_id IS NULL) AS trials_without_any_sponsor_rows
    FROM ctgov.studies s LEFT JOIN counts c ON s.nct_id=c.nct_id
    GROUP BY COALESCE(c.lead_count,0) ORDER BY lead_count;

-- query: sponsor_role_distribution
SELECT lead_or_collaborator AS value,COUNT(*) AS rows
    FROM ctgov.sponsors GROUP BY lead_or_collaborator ORDER BY rows DESC;

-- 7. Diagnostic candidate counts for the supplied reference date.
-- Compare the legacy anticipated spelling with anticipated/estimated.
-- The live source uses ESTIMATED. Verify vocabulary separately in each archive.
-- These are single-source diagnostics, not a final first-snapshot cohort.

-- query: current_candidate_original_anticipated
WITH candidate AS (
        SELECT nct_id, start_date-DATE 'YYYY-MM-DD' AS days_to_planned_start
        FROM ctgov.studies WHERE LOWER(study_type)='interventional'
        AND start_date IS NOT NULL AND LOWER(COALESCE(start_date_type,''))='anticipated'
        AND study_first_posted_date<=DATE 'YYYY-MM-DD' AND start_date>DATE 'YYYY-MM-DD')
        SELECT COUNT(*) FILTER (WHERE days_to_planned_start<=30) AS within_30d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=60) AS within_60d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=90) AS within_90d,
        COUNT(*) AS all_future_planned FROM candidate;

-- query: current_candidate_anticipated_or_estimated
WITH candidate AS (
        SELECT nct_id, start_date-DATE 'YYYY-MM-DD' AS days_to_planned_start
        FROM ctgov.studies WHERE LOWER(study_type)='interventional'
        AND start_date IS NOT NULL AND LOWER(COALESCE(start_date_type,'')) IN ('anticipated','estimated')
        AND study_first_posted_date<=DATE 'YYYY-MM-DD' AND start_date>DATE 'YYYY-MM-DD')
        SELECT COUNT(*) FILTER (WHERE days_to_planned_start<=30) AS within_30d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=60) AS within_60d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=90) AS within_90d,
        COUNT(*) AS all_future_planned FROM candidate;

-- Additional date checks: late public posting is not the same as late submission.

-- query: date_completeness_current
SELECT COUNT(*) AS interventional_trials,
    COUNT(*) FILTER (WHERE start_date IS NULL) AS missing_start_date,
    COUNT(*) FILTER (WHERE study_first_posted_date IS NULL) AS missing_first_posted_date,
    COUNT(*) FILTER (WHERE start_date IS NOT NULL AND study_first_posted_date IS NOT NULL) AS date_comparable_trials,
    COUNT(*) FILTER (WHERE study_first_posted_date>start_date) AS first_posted_after_current_start_date,
    MIN(study_first_posted_date) AS minimum_first_posted,
    MAX(study_first_posted_date) AS maximum_first_posted
    FROM ctgov.studies WHERE LOWER(study_type)='interventional';
