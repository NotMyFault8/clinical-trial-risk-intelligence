-- Phase 1 AACT schema/cardinality audit.
-- Run separately for every selected historical snapshot after loading it into PostgreSQL.
-- Do not treat results from the current/live database as proof of historical availability.

-- 1. Inventory tables in the AACT ctgov schema.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'ctgov'
ORDER BY table_name;

-- 2. Inventory columns/types for the core candidate tables.
SELECT
    table_name,
    ordinal_position,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'ctgov'
  AND table_name IN (
      'studies',
      'designs',
      'eligibilities',
      'sponsors',
      'conditions',
      'interventions',
      'facilities',
      'study_records'
  )
ORDER BY table_name, ordinal_position;

-- 3. studies should be one row per NCT ID.
SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT nct_id) AS distinct_nct_ids,
    COUNT(*) - COUNT(DISTINCT nct_id) AS duplicate_rows
FROM ctgov.studies;

SELECT nct_id, COUNT(*) AS n
FROM ctgov.studies
GROUP BY nct_id
HAVING COUNT(*) > 1
ORDER BY n DESC, nct_id
LIMIT 100;

-- 4. Measure actual rows per trial in every candidate table.
-- Run each table explicitly so a missing historical table fails loudly.
SELECT 'designs' AS table_name,
       COUNT(*) AS rows,
       COUNT(DISTINCT nct_id) AS trials,
       MAX(n) AS max_rows_per_trial
FROM (
    SELECT nct_id, COUNT(*) AS n
    FROM ctgov.designs
    GROUP BY nct_id
) x;

SELECT 'eligibilities' AS table_name,
       COUNT(*) AS trials_with_rows,
       MAX(n) AS max_rows_per_trial
FROM (
    SELECT nct_id, COUNT(*) AS n
    FROM ctgov.eligibilities
    GROUP BY nct_id
) x;

SELECT 'sponsors' AS table_name,
       COUNT(*) AS trials_with_rows,
       MAX(n) AS max_rows_per_trial
FROM (
    SELECT nct_id, COUNT(*) AS n
    FROM ctgov.sponsors
    GROUP BY nct_id
) x;

SELECT 'conditions' AS table_name,
       COUNT(*) AS trials_with_rows,
       MAX(n) AS max_rows_per_trial
FROM (
    SELECT nct_id, COUNT(*) AS n
    FROM ctgov.conditions
    GROUP BY nct_id
) x;

SELECT 'interventions' AS table_name,
       COUNT(*) AS trials_with_rows,
       MAX(n) AS max_rows_per_trial
FROM (
    SELECT nct_id, COUNT(*) AS n
    FROM ctgov.interventions
    GROUP BY nct_id
) x;

SELECT 'facilities' AS table_name,
       COUNT(*) AS trials_with_rows,
       MAX(n) AS max_rows_per_trial
FROM (
    SELECT nct_id, COUNT(*) AS n
    FROM ctgov.facilities
    GROUP BY nct_id
) x;

-- 5. Key status/date/type distributions.
SELECT study_type, COUNT(*)
FROM ctgov.studies
GROUP BY study_type
ORDER BY COUNT(*) DESC;

SELECT start_date_type, COUNT(*)
FROM ctgov.studies
GROUP BY start_date_type
ORDER BY COUNT(*) DESC;

SELECT enrollment_type, COUNT(*)
FROM ctgov.studies
GROUP BY enrollment_type
ORDER BY COUNT(*) DESC;

SELECT overall_status, COUNT(*)
FROM ctgov.studies
GROUP BY overall_status
ORDER BY COUNT(*) DESC;

-- 6. Lead-sponsor cardinality.
SELECT
    lead_count,
    COUNT(*) AS trials
FROM (
    SELECT
        nct_id,
        COUNT(*) FILTER (
            WHERE LOWER(COALESCE(lead_or_collaborator, '')) = 'lead'
        ) AS lead_count
    FROM ctgov.sponsors
    GROUP BY nct_id
) x
GROUP BY lead_count
ORDER BY lead_count;

-- 7. Candidate point-in-time population for a supplied snapshot date.
-- Replace DATE 'YYYY-MM-DD' with the archive date.
WITH candidate AS (
    SELECT
        nct_id,
        study_first_posted_date,
        start_date,
        start_date_type,
        study_type,
        (start_date - DATE 'YYYY-MM-DD') AS days_to_planned_start
    FROM ctgov.studies
    WHERE LOWER(study_type) = 'interventional'
      AND start_date IS NOT NULL
      AND LOWER(COALESCE(start_date_type, '')) = 'anticipated'
      AND study_first_posted_date <= DATE 'YYYY-MM-DD'
      AND start_date > DATE 'YYYY-MM-DD'
)
SELECT
    COUNT(*) FILTER (WHERE days_to_planned_start <= 30) AS within_30d,
    COUNT(*) FILTER (WHERE days_to_planned_start <= 60) AS within_60d,
    COUNT(*) FILTER (WHERE days_to_planned_start <= 90) AS within_90d,
    COUNT(*) AS all_future_anticipated
FROM candidate;

-- 8. study_records semantics must be audited before use.
SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT nct_id) AS trials,
    COUNT(*) - COUNT(DISTINCT nct_id) AS extra_rows
FROM ctgov.study_records;

SELECT nct_id, COUNT(*) AS n
FROM ctgov.study_records
GROUP BY nct_id
HAVING COUNT(*) > 1
ORDER BY n DESC, nct_id
LIMIT 100;
