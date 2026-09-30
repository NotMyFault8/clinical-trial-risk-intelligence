-- Measured companion to schema_audit.sql. Current live audit only.

-- Reference date is diagnostic, not an archive date.

BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;

SET LOCAL statement_timeout='180s';

-- provenance
SELECT json_build_object('section','provenance','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT current_database() AS database,
    transaction_timestamp() AS observed_at_utc,
    transaction_timestamp() AT TIME ZONE 'America/Toronto' AS observed_at_toronto,
    current_setting('transaction_read_only') AS read_only,
    current_setting('transaction_isolation') AS isolation,
    DATE '2026-09-29' AS diagnostic_reference_date,
    'current_live_database_not_historical_snapshot' AS source_kind
) q;

-- table_inventory
SELECT json_build_object('section','table_inventory','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT table_name, table_type FROM information_schema.tables
    WHERE table_schema='ctgov' ORDER BY table_name
) q;

-- column_inventory
SELECT json_build_object('section','column_inventory','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT table_name, ordinal_position, column_name, data_type, is_nullable
    FROM information_schema.columns WHERE table_schema='ctgov' AND table_name IN
    ('studies','designs','eligibilities','sponsors','conditions','interventions','facilities','study_records')
    ORDER BY table_name, ordinal_position
) q;

-- study_records_presence
SELECT json_build_object('section','study_records_presence','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT n.nspname AS schema_name, c.relname AS relation_name,
    c.relkind AS relation_kind, has_table_privilege(c.oid, 'SELECT') AS can_select
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
    WHERE c.relname='study_records' ORDER BY n.nspname
) q;

-- studies_uniqueness
SELECT json_build_object('section','studies_uniqueness','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT nct_id) AS distinct_nct_ids,
    COUNT(*) FILTER (WHERE nct_id IS NULL) AS null_nct_ids,
    COUNT(nct_id)-COUNT(DISTINCT nct_id) AS extra_nonnull_id_rows,
    COUNT(*)-COUNT(DISTINCT nct_id) AS original_duplicate_rows_metric FROM ctgov.studies
) q;

-- studies_duplicate_ids
SELECT json_build_object('section','studies_duplicate_ids','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT nct_id, COUNT(*) AS n FROM ctgov.studies
    GROUP BY nct_id HAVING COUNT(*)>1 ORDER BY n DESC,nct_id LIMIT 100
) q;

-- cardinality_designs
SELECT json_build_object('section','cardinality_designs','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
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
        FROM grouped
) q;

-- cardinality_eligibilities
SELECT json_build_object('section','cardinality_eligibilities','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
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
        FROM grouped
) q;

-- cardinality_sponsors
SELECT json_build_object('section','cardinality_sponsors','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
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
        FROM grouped
) q;

-- cardinality_conditions
SELECT json_build_object('section','cardinality_conditions','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
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
        FROM grouped
) q;

-- cardinality_interventions
SELECT json_build_object('section','cardinality_interventions','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
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
        FROM grouped
) q;

-- cardinality_facilities
SELECT json_build_object('section','cardinality_facilities','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
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
        FROM grouped
) q;

-- distribution_study_type
SELECT json_build_object('section','distribution_study_type','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT study_type AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY study_type ORDER BY trials DESC, value NULLS LAST
) q;

-- distribution_start_date_type
SELECT json_build_object('section','distribution_start_date_type','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT start_date_type AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY start_date_type ORDER BY trials DESC, value NULLS LAST
) q;

-- distribution_enrollment_type
SELECT json_build_object('section','distribution_enrollment_type','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT enrollment_type AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY enrollment_type ORDER BY trials DESC, value NULLS LAST
) q;

-- distribution_overall_status
SELECT json_build_object('section','distribution_overall_status','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT overall_status AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY overall_status ORDER BY trials DESC, value NULLS LAST
) q;

-- interventional_status_distribution
SELECT json_build_object('section','interventional_status_distribution','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT overall_status AS value, COUNT(*) AS trials,
    ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_interventional
    FROM ctgov.studies WHERE LOWER(study_type)='interventional'
    GROUP BY overall_status ORDER BY trials DESC,value NULLS LAST
) q;

-- lead_sponsor_original
SELECT json_build_object('section','lead_sponsor_original','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT lead_count, COUNT(*) AS trials FROM (
    SELECT nct_id,COUNT(*) FILTER (WHERE LOWER(COALESCE(lead_or_collaborator,''))='lead') AS lead_count
    FROM ctgov.sponsors GROUP BY nct_id) x GROUP BY lead_count ORDER BY lead_count
) q;

-- lead_sponsor_all_studies
SELECT json_build_object('section','lead_sponsor_all_studies','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
WITH counts AS (
    SELECT nct_id, COUNT(*) AS sponsor_rows,
    COUNT(*) FILTER (WHERE LOWER(COALESCE(lead_or_collaborator,''))='lead') AS lead_count
    FROM ctgov.sponsors GROUP BY nct_id)
    SELECT COALESCE(c.lead_count,0) AS lead_count, COUNT(*) AS trials,
    COUNT(*) FILTER (WHERE c.nct_id IS NULL) AS trials_without_any_sponsor_rows
    FROM ctgov.studies s LEFT JOIN counts c ON s.nct_id=c.nct_id
    GROUP BY COALESCE(c.lead_count,0) ORDER BY lead_count
) q;

-- sponsor_role_distribution
SELECT json_build_object('section','sponsor_role_distribution','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT lead_or_collaborator AS value,COUNT(*) AS rows
    FROM ctgov.sponsors GROUP BY lead_or_collaborator ORDER BY rows DESC
) q;

-- current_candidate_original_anticipated
SELECT json_build_object('section','current_candidate_original_anticipated','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
WITH candidate AS (
        SELECT nct_id, start_date-DATE '2026-09-29' AS days_to_planned_start
        FROM ctgov.studies WHERE LOWER(study_type)='interventional'
        AND start_date IS NOT NULL AND LOWER(COALESCE(start_date_type,''))='anticipated'
        AND study_first_posted_date<=DATE '2026-09-29' AND start_date>DATE '2026-09-29')
        SELECT COUNT(*) FILTER (WHERE days_to_planned_start<=30) AS within_30d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=60) AS within_60d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=90) AS within_90d,
        COUNT(*) AS all_future_planned FROM candidate
) q;

-- current_candidate_anticipated_or_estimated
SELECT json_build_object('section','current_candidate_anticipated_or_estimated','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
WITH candidate AS (
        SELECT nct_id, start_date-DATE '2026-09-29' AS days_to_planned_start
        FROM ctgov.studies WHERE LOWER(study_type)='interventional'
        AND start_date IS NOT NULL AND LOWER(COALESCE(start_date_type,'')) IN ('anticipated','estimated')
        AND study_first_posted_date<=DATE '2026-09-29' AND start_date>DATE '2026-09-29')
        SELECT COUNT(*) FILTER (WHERE days_to_planned_start<=30) AS within_30d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=60) AS within_60d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=90) AS within_90d,
        COUNT(*) AS all_future_planned FROM candidate
) q;

-- date_completeness_current
SELECT json_build_object('section','date_completeness_current','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (
SELECT COUNT(*) AS interventional_trials,
    COUNT(*) FILTER (WHERE start_date IS NULL) AS missing_start_date,
    COUNT(*) FILTER (WHERE study_first_posted_date IS NULL) AS missing_first_posted_date,
    COUNT(*) FILTER (WHERE start_date IS NOT NULL AND study_first_posted_date IS NOT NULL) AS date_comparable_trials,
    COUNT(*) FILTER (WHERE study_first_posted_date>start_date) AS first_posted_after_current_start_date,
    MIN(study_first_posted_date) AS minimum_first_posted,
    MAX(study_first_posted_date) AS maximum_first_posted
    FROM ctgov.studies WHERE LOWER(study_type)='interventional'
) q;

COMMIT;
