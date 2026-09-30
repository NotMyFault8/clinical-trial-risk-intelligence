"""Read-only AACT audit. No credentials are written to outputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--credentials-file', type=Path, required=True)
parser.add_argument('--source-sql', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
args = parser.parse_args()
out = args.output_dir
out.mkdir(parents=True, exist_ok=True)
cfg = {}
for line in args.credentials_file.read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        cfg[key.strip()] = value.strip().strip('\"\'')
env = os.environ.copy()
for pg, key in [('PGHOST','AACT_DB_HOST'), ('PGPORT','AACT_DB_PORT'),
                ('PGDATABASE','AACT_DB_NAME'), ('PGUSER','AACT_DB_USER'),
                ('PGPASSWORD','AACT_DB_PASSWORD')]:
    env[pg] = cfg.get(key, '')
env['PGCONNECT_TIMEOUT'] = '15'
env['PGOPTIONS'] = '-c default_transaction_read_only=on -c statement_timeout=180000'
queries = []
def add(name, sql):
    queries.append((name, sql.strip().rstrip(';')))

add('provenance', """SELECT current_database() AS database,
    transaction_timestamp() AS observed_at_utc,
    transaction_timestamp() AT TIME ZONE 'America/Toronto' AS observed_at_toronto,
    current_setting('transaction_read_only') AS read_only,
    current_setting('transaction_isolation') AS isolation,
    DATE '2026-09-29' AS diagnostic_reference_date,
    'current_live_database_not_historical_snapshot' AS source_kind""")
add('table_inventory', """SELECT table_name, table_type FROM information_schema.tables
    WHERE table_schema='ctgov' ORDER BY table_name""")
add('column_inventory', """SELECT table_name, ordinal_position, column_name, data_type, is_nullable
    FROM information_schema.columns WHERE table_schema='ctgov' AND table_name IN
    ('studies','designs','eligibilities','sponsors','conditions','interventions','facilities','study_records')
    ORDER BY table_name, ordinal_position""")
add('study_records_presence', """SELECT n.nspname AS schema_name, c.relname AS relation_name,
    c.relkind AS relation_kind, has_table_privilege(c.oid, 'SELECT') AS can_select
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
    WHERE c.relname='study_records' ORDER BY n.nspname""")
add('studies_uniqueness', """SELECT COUNT(*) AS total_rows, COUNT(DISTINCT nct_id) AS distinct_nct_ids,
    COUNT(*) FILTER (WHERE nct_id IS NULL) AS null_nct_ids,
    COUNT(nct_id)-COUNT(DISTINCT nct_id) AS extra_nonnull_id_rows,
    COUNT(*)-COUNT(DISTINCT nct_id) AS original_duplicate_rows_metric FROM ctgov.studies""")
add('studies_duplicate_ids', """SELECT nct_id, COUNT(*) AS n FROM ctgov.studies
    GROUP BY nct_id HAVING COUNT(*)>1 ORDER BY n DESC,nct_id LIMIT 100""")
for table in ['designs','eligibilities','sponsors','conditions','interventions','facilities']:
    add('cardinality_'+table, f"""WITH grouped AS (
        SELECT nct_id, COUNT(*) AS n FROM ctgov.{table} GROUP BY nct_id)
        SELECT '{table}' AS table_name, COALESCE(SUM(n),0)::bigint AS source_rows,
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
        FROM grouped""")
for field in ['study_type','start_date_type','enrollment_type','overall_status']:
    add('distribution_'+field, f"""SELECT {field} AS value, COUNT(*) AS trials,
        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_all_studies
        FROM ctgov.studies GROUP BY {field} ORDER BY trials DESC, value NULLS LAST""")
add('interventional_status_distribution', """SELECT overall_status AS value, COUNT(*) AS trials,
    ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),4) AS percent_of_interventional
    FROM ctgov.studies WHERE LOWER(study_type)='interventional'
    GROUP BY overall_status ORDER BY trials DESC,value NULLS LAST""")
add('lead_sponsor_original', """SELECT lead_count, COUNT(*) AS trials FROM (
    SELECT nct_id,COUNT(*) FILTER (WHERE LOWER(COALESCE(lead_or_collaborator,''))='lead') AS lead_count
    FROM ctgov.sponsors GROUP BY nct_id) x GROUP BY lead_count ORDER BY lead_count""")
add('lead_sponsor_all_studies', """WITH counts AS (
    SELECT nct_id, COUNT(*) AS sponsor_rows,
    COUNT(*) FILTER (WHERE LOWER(COALESCE(lead_or_collaborator,''))='lead') AS lead_count
    FROM ctgov.sponsors GROUP BY nct_id)
    SELECT COALESCE(c.lead_count,0) AS lead_count, COUNT(*) AS trials,
    COUNT(*) FILTER (WHERE c.nct_id IS NULL) AS trials_without_any_sponsor_rows
    FROM ctgov.studies s LEFT JOIN counts c ON s.nct_id=c.nct_id
    GROUP BY COALESCE(c.lead_count,0) ORDER BY lead_count""")
add('sponsor_role_distribution', """SELECT lead_or_collaborator AS value,COUNT(*) AS rows
    FROM ctgov.sponsors GROUP BY lead_or_collaborator ORDER BY rows DESC""")
for name, condition in [('original_anticipated', "LOWER(COALESCE(start_date_type,''))='anticipated'"),
                        ('anticipated_or_estimated', "LOWER(COALESCE(start_date_type,'')) IN ('anticipated','estimated')")]:
    add('current_candidate_'+name, f"""WITH candidate AS (
        SELECT nct_id, start_date-DATE '2026-09-29' AS days_to_planned_start
        FROM ctgov.studies WHERE LOWER(study_type)='interventional'
        AND start_date IS NOT NULL AND {condition}
        AND study_first_posted_date<=DATE '2026-09-29' AND start_date>DATE '2026-09-29')
        SELECT COUNT(*) FILTER (WHERE days_to_planned_start<=30) AS within_30d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=60) AS within_60d,
        COUNT(*) FILTER (WHERE days_to_planned_start<=90) AS within_90d,
        COUNT(*) AS all_future_planned FROM candidate""")
add('date_completeness_current', """SELECT COUNT(*) AS interventional_trials,
    COUNT(*) FILTER (WHERE start_date IS NULL) AS missing_start_date,
    COUNT(*) FILTER (WHERE study_first_posted_date IS NULL) AS missing_first_posted_date,
    COUNT(*) FILTER (WHERE start_date IS NOT NULL AND study_first_posted_date IS NOT NULL) AS date_comparable_trials,
    COUNT(*) FILTER (WHERE study_first_posted_date>start_date) AS first_posted_after_current_start_date,
    MIN(study_first_posted_date) AS minimum_first_posted,
    MAX(study_first_posted_date) AS maximum_first_posted
    FROM ctgov.studies WHERE LOWER(study_type)='interventional'""")

parts = ['-- Measured companion to schema_audit.sql. Current live audit only.',
         '-- Reference date is diagnostic, not an archive date.',
         'BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;',
         "SET LOCAL statement_timeout='180s';"]
for name, query in queries:
    parts.append(f"-- {name}\nSELECT json_build_object('section','{name}','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (\n{query}\n) q;")
parts.append('COMMIT;')
sql = '\n\n'.join(parts)+'\n'
(out/'executed_audit.sql').write_text(sql)
r = subprocess.run(['psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],
                   input=sql,env=env,capture_output=True,text=True)
if r.returncode:
    print(r.stderr)
    raise SystemExit(r.returncode)
data = {}
for line in r.stdout.splitlines():
    if line.strip():
        item = json.loads(line)
        data[item['section']] = item['data']
data['manifest'] = {
    'original_sql_sha256':hashlib.sha256(args.source_sql.read_bytes()).hexdigest(),
    'executed_sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),
    'original_sql_name':args.source_sql.name,
    'section_7_historical_status':'not_measured_no_historical_snapshot_supplied',
    'section_8_status':'not_measured_if_relation_absent_see_study_records_presence',
}
(out/'audit_results.json').write_text(json.dumps(data,indent=2)+'\n')
for key,value in data.items():
    if key not in ['column_inventory','table_inventory']:
        print(key,json.dumps(value))
print('table_inventory_count',len(data['table_inventory']))
print('column_inventory_count',len(data['column_inventory']))
