"""Run the named queries from the readable SQL file and save measured results.

The SQL file is the source of truth. This collector contains no audit queries.
Use a fresh output directory; existing measurements are never overwritten.
"""
import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--credentials-file', type=Path, required=True)
parser.add_argument('--source-sql', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--reference-date', type=date.fromisoformat, required=True)
parser.add_argument('--source-kind', choices=['current_live_database', 'historical_snapshot'], required=True)
parser.add_argument('--snapshot-id', help='Exact downloaded archive filename for a historical source')
parser.add_argument('--archive-sha256', help='SHA-256 of that downloaded archive')
args = parser.parse_args()
if args.source_kind == 'historical_snapshot':
    if not args.snapshot_id or not re.fullmatch(r'[0-9a-fA-F]{64}', args.archive_sha256 or ''):
        parser.error('Historical runs require --snapshot-id and a valid --archive-sha256.')
out = args.output_dir
if any((out/name).exists() for name in ['executed_audit.sql','audit_results.json','schema_audit_original.sql']):
    parser.error('Use a fresh output directory to preserve earlier audit evidence.')

# Split only at our named comment markers, not at arbitrary SQL semicolons.
source_bytes = args.source_sql.read_bytes()
source_text = source_bytes.decode('utf-8')
sections = re.split(r'^-- query: ([a-z][a-z0-9_]*)[ \t]*$', source_text, flags=re.MULTILINE)
queries = []
seen_names = set()
for position in range(1, len(sections), 2):
    name = sections[position]
    query = sections[position+1].strip()
    # Remove separator comments attached to the end of the previous block.
    query = re.sub(r';\s*(?:--[^\n]*(?:\n|$)\s*)*$', '', query).strip()
    if name in seen_names or not query:
        parser.error('Query names must be unique and query bodies must be nonempty.')
    seen_names.add(name)
    query = query.replace("DATE 'YYYY-MM-DD'", "DATE '"+args.reference_date.isoformat()+"'")
    query = query.replace("'SOURCE_KIND'", "'"+args.source_kind+"'")
    queries.append((name, query))
if not queries:
    parser.error('The SQL source must contain -- query: name markers.')

settings = {}
for line in args.credentials_file.read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        settings[key.strip()] = value.strip().strip('"').strip("'")
environment = os.environ.copy()
for pg_name, setting_name in [('PGHOST','AACT_DB_HOST'), ('PGPORT','AACT_DB_PORT'),
                             ('PGDATABASE','AACT_DB_NAME'), ('PGUSER','AACT_DB_USER'),
                             ('PGPASSWORD','AACT_DB_PASSWORD')]:
    environment[pg_name] = settings.get(setting_name, '')
environment['PGCONNECT_TIMEOUT'] = '15'
environment['PGOPTIONS'] = '-c default_transaction_read_only=on -c statement_timeout=180000'

parts = ['-- Generated from the named queries in schema_audit.sql.',
         'BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;',
         "SET LOCAL statement_timeout='180s';"]
for name, query in queries:
    parts.append(f"-- {name}\nSELECT json_build_object('section','{name}','data',COALESCE(json_agg(row_to_json(q)),'[]'::json)) FROM (\n{query}\n) q;")
parts.append('COMMIT;')
sql = '\n\n'.join(parts)+'\n'
out.mkdir(parents=True, exist_ok=True)
(out/'schema_audit_original.sql').write_bytes(source_bytes)
(out/'executed_audit.sql').write_text(sql)
result = subprocess.run(['psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],
                        input=sql, env=environment, capture_output=True, text=True)
if result.returncode:
    print(result.stderr)
    raise SystemExit(result.returncode)
results = {}
for line in result.stdout.splitlines():
    if line.strip():
        section = json.loads(line)
        results[section['section']] = section['data']
if set(results) != seen_names:
    raise RuntimeError('Returned result sections do not match requested queries.')
results['manifest'] = {
    'original_sql_sha256':hashlib.sha256(source_bytes).hexdigest(),
    'executed_sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),
    'original_sql_name':args.source_sql.name,
    'reference_date':args.reference_date.isoformat(),
    'source_kind':args.source_kind,
    'snapshot_id':args.snapshot_id,
    'archive_sha256':args.archive_sha256,
    'excluded_tables':['study_records','study_references'],
    'note':'Source labels and hashes are supplied provenance; verify the connected database matches the loaded archive.',
}
(out/'audit_results.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Saved {len(queries)} query results to {out}. No database records were changed.')
