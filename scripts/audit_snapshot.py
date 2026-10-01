"""Inspect one AACT pipe-delimited ZIP without extracting it or using the live DB.

Only source snapshot dates are recorded; no execution date/time is added.
Outputs are measurements, not a final cohort or training dataset.
"""
import argparse
import calendar
from collections import Counter
import csv
from datetime import date, datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

CORE = ['studies', 'designs', 'eligibilities', 'sponsors', 'conditions', 'interventions', 'facilities']


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def records(archive, member):
    """Parse quoted pipe-delimited records and reject unexpected field counts."""
    with archive.open(member) as source:
        reader = csv.reader(io.TextIOWrapper(source, encoding='utf-8-sig', newline=''),
                            delimiter='|', strict=True)
        headers = next(reader)
        if len(headers) != len(set(headers)):
            raise ValueError(f'Duplicate column name in {member}')
        for number, values in enumerate(reader, start=2):
            if len(values) != len(headers):
                raise ValueError(f'{member} record {number}: expected {len(headers)} fields, got {len(values)}')
            yield dict(zip(headers, values))


def count_values(rows, field):
    return dict(Counter(row[field] or 'NULL' for row in rows))


def inspect(args):
    if args.output.exists():
        raise ValueError('Output already exists; choose a fresh path to preserve measurements.')
    csv.field_size_limit(20 * 1024 * 1024)
    results = {'source': {
        'snapshot_date': args.snapshot_date.isoformat(),
        'archive_filename': args.archive.name,
        'archive_bytes': args.archive.stat().st_size,
        'archive_sha256': sha256(args.archive),
        'catalog_url': args.catalog_url,
        'method': 'streamed pipe-delimited files directly from ZIP; no live database queried',
        'script_sha256': sha256(Path(__file__)),
    }}
    with zipfile.ZipFile(args.archive) as archive:
        members = archive.infolist()
        # Reading every member also verifies the internal ZIP CRCs.
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f'ZIP CRC failure: {bad_member}')
        print('ZIP integrity check passed.', flush=True)
        results['source']['zip_crc_check'] = 'passed_all_members'
        results['source']['uncompressed_bytes'] = sum(member.file_size for member in members)
        results['inventory'] = [{'file': member.filename, 'bytes': member.file_size} for member in members]
        results['headers'] = {}
        for table in CORE:
            with archive.open(table + '.txt') as source:
                results['headers'][table] = next(csv.reader(
                    io.TextIOWrapper(source, encoding='utf-8-sig', newline=''), delimiter='|'))

        ids = Counter()
        distributions = {field: Counter() for field in
                         ['study_type','start_date_type','enrollment_type','overall_status']}
        interventional_types = Counter()
        dates = Counter()
        # A mutually exclusive waterfall, in the order used below.
        waterfall = Counter({key: 0 for key in [
            'all_studies', 'excluded_non_interventional', 'interventional',
            'excluded_missing_or_invalid_start_date', 'valid_start_date',
            'excluded_start_type_not_planned', 'planned_start_type',
            'excluded_missing_or_invalid_first_posted_date',
            'excluded_first_posted_after_snapshot', 'posted_by_snapshot',
            'excluded_start_not_after_snapshot', 'future_planned_start',
            'excluded_start_beyond_90_days', 'within_90_days']})
        candidates = []
        untyped_future = Counter()
        precision = Counter()
        interval_counts = {str(days): {'definitely_in_window': 0, 'possibly_in_window': 0}
                           for days in [30,60,90]}
        month_date_conventions = Counter()
        unparsed_start_text = []
        source_posted_after_snapshot = 0
        min_posted = None
        max_posted = None
        def parsed(raw, field):
            if not raw:
                dates['missing_' + field] += 1
                return None
            try:
                return date.fromisoformat(raw)
            except ValueError:
                dates['invalid_' + field] += 1
                return None
        for row in records(archive, 'studies.txt'):
            ids[row['nct_id']] += 1
            for field in distributions:
                distributions[field][row[field] or 'NULL'] += 1
            waterfall['all_studies'] += 1
            # Audit source-wide posting bounds without changing cohort filters.
            try:
                posted_all = date.fromisoformat(row['study_first_posted_date'])
            except ValueError:
                posted_all = None
            if posted_all:
                min_posted = min(min_posted, posted_all) if min_posted else posted_all
                max_posted = max(max_posted, posted_all) if max_posted else posted_all
                source_posted_after_snapshot += posted_all > args.snapshot_date
            if row['study_type'].lower() != 'interventional':
                waterfall['excluded_non_interventional'] += 1
                continue
            waterfall['interventional'] += 1
            interventional_types[row['start_date_type'] or 'NULL'] += 1
            start = parsed(row['start_date'], 'start_date')
            posted = parsed(row['study_first_posted_date'], 'first_posted_date')
            if start and posted:
                dates['comparable_start_and_posted'] += 1
                dates['first_posted_after_recorded_start'] += posted > start
            if start and posted and posted <= args.snapshot_date and start > args.snapshot_date:
                untyped_future[row['start_date_type'] or 'NULL'] += 1
            if start is None:
                waterfall['excluded_missing_or_invalid_start_date'] += 1
                continue
            waterfall['valid_start_date'] += 1
            if row['start_date_type'].lower() not in ['anticipated', 'estimated']:
                waterfall['excluded_start_type_not_planned'] += 1
                continue
            waterfall['planned_start_type'] += 1
            if posted is None:
                waterfall['excluded_missing_or_invalid_first_posted_date'] += 1
                continue
            if posted > args.snapshot_date:
                waterfall['excluded_first_posted_after_snapshot'] += 1
                continue
            waterfall['posted_by_snapshot'] += 1
            # Sensitivity analysis: a month-only report represents an interval,
            # not a known event on the normalized start_date day.
            start_text = row['start_month_year']
            try:
                lower = upper = datetime.strptime(start_text, '%B %d, %Y').date()
            except ValueError:
                try:
                    lower = datetime.strptime(start_text, '%B %Y').date()
                    upper = lower.replace(day=calendar.monthrange(lower.year,lower.month)[1])
                    convention = 'last_day' if start==upper else ('first_day' if start==lower else 'other_day')
                    month_date_conventions[convention] += 1
                except ValueError:
                    lower = upper = None
                    if len(unparsed_start_text)<5:
                        unparsed_start_text.append(start_text)
            if lower is not None:
                for days in [30,60,90]:
                    cutoff = args.snapshot_date + timedelta(days=days)
                    interval_counts[str(days)]['definitely_in_window'] += lower>args.snapshot_date and upper<=cutoff
                    interval_counts[str(days)]['possibly_in_window'] += upper>args.snapshot_date and lower<=cutoff
            if start <= args.snapshot_date:
                waterfall['excluded_start_not_after_snapshot'] += 1
                continue
            waterfall['future_planned_start'] += 1
            days = (start - args.snapshot_date).days
            # A separate precision diagnostic; retain the original text.
            full_day = bool(re.fullmatch(r'[A-Za-z]+ \d{1,2}, \d{4}', row['start_month_year']))
            precision['full_day_text' if full_day else 'month_only_or_other_text'] += 1
            if days > 90:
                waterfall['excluded_start_beyond_90_days'] += 1
            else:
                waterfall['within_90_days'] += 1
            candidates.append({
                'nct_id': row['nct_id'], 'days_to_planned_start': days,
                'start_month_year': row['start_month_year'], 'start_date': row['start_date'],
                'study_first_posted_date': row['study_first_posted_date'],
                'start_date_type': row['start_date_type'], 'overall_status': row['overall_status'],
                'enrollment_type': row['enrollment_type'], 'enrollment': row['enrollment'],
            })
        results['studies'] = {
            'rows': sum(ids.values()), 'unique_nonempty_ids': len(ids)-int('' in ids),
            'missing_id_rows': ids.get('',0),
            'extra_nonempty_id_rows': sum(n-1 for key,n in ids.items() if key),
            'duplicate_id_examples': [key for key,n in ids.items() if n>1][:10],
            'minimum_first_posted': min_posted.isoformat() if min_posted else None,
            'maximum_first_posted': max_posted.isoformat() if max_posted else None,
            'first_posted_after_snapshot': source_posted_after_snapshot,
        }
        results['distributions'] = {field: dict(values) for field,values in distributions.items()}
        results['interventional_start_date_types'] = dict(interventional_types)
        results['interventional_date_checks'] = dict(dates)
        results['waterfall'] = dict(waterfall)
        results['future_start_without_type_filter'] = dict(untyped_future)
        results['future_planned_start_text_precision'] = dict(precision)
        results['date_precision_sensitivity'] = {
            'population': 'interventional, valid normalized start date, planned type, posted by snapshot',
            'method': 'full date -> exact day; month/year -> first through last day; compare to snapshot < start <= snapshot + window',
            'windows': interval_counts,
            'month_only_normalized_date_conventions': dict(month_date_conventions),
            'unparsed_start_text_examples': unparsed_start_text,
        }
        results['windows'] = {}
        for days in [30,60,90]:
            selected = [row for row in candidates if row['days_to_planned_start'] <= days]
            results['windows'][str(days)] = {
                'trials': len(selected),
                'statuses_at_snapshot': count_values(selected, 'overall_status'),
                'enrollment_types_at_snapshot': count_values(selected, 'enrollment_type'),
                'missing_enrollment': sum(not row['enrollment'] for row in selected),
                'start_text_month_only_or_other': sum(not re.fullmatch(r'[A-Za-z]+ \d{1,2}, \d{4}', row['start_month_year']) for row in selected),
            }
        results['all_future_planned'] = len(candidates)
        # Exact IDs make the pilot cohort membership inspectable; no outcomes are labeled.
        results['candidate_ids_by_window'] = {
            str(days): sorted(row['nct_id'] for row in candidates if row['days_to_planned_start']<=days)
            for days in [30,60,90]}
        results['candidate_examples'] = sorted(candidates,key=lambda row:(row['days_to_planned_start'],row['nct_id']))[:5]
        print('Study counts and candidate windows measured.', flush=True)

        study_ids = set(ids)-{''}
        candidate_ids = set(results['candidate_ids_by_window']['90'])
        results['core_table_cardinality'] = {}
        candidate_field_missing = {field: 0 for field in ['criteria','minimum_age','maximum_age','gender','healthy_volunteers']}
        age_na = Counter()
        leads = Counter()
        for table in CORE[1:]:
            counts = Counter()
            for row in records(archive, table+'.txt'):
                counts[row['nct_id']] += 1
                if table == 'sponsors' and row['lead_or_collaborator'].lower() == 'lead':
                    leads[row['nct_id']] += 1
                if table == 'eligibilities' and row['nct_id'] in candidate_ids:
                    for field in candidate_field_missing:
                        candidate_field_missing[field] += not row[field]
                    for field in ['minimum_age','maximum_age']:
                        age_na[field] += row[field].strip().upper() in ['N/A','NA']
            nonempty = set(counts)-{''}
            results['core_table_cardinality'][table] = {
                'rows': sum(counts.values()), 'distinct_nonempty_ids': len(nonempty),
                'null_id_rows': counts.get('',0), 'max_rows_per_id': max((counts[key] for key in nonempty), default=0),
                'ids_with_multiple_rows': sum(counts[key]>1 for key in nonempty),
                'studies_without_rows': len(study_ids-nonempty), 'orphan_ids': len(nonempty-study_ids),
                'candidate_90d_without_rows': len(candidate_ids-nonempty),
            }
            print('Measured '+table+'.', flush=True)
        results['lead_sponsor_counts_all_studies'] = dict(Counter(leads[key] for key in study_ids))
        results['lead_sponsor_counts_90d_candidates'] = dict(Counter(leads[key] for key in candidate_ids))
        results['candidate_eligibility_missing_fields_among_present_rows'] = candidate_field_missing
        results['candidate_eligibility_age_na_values'] = dict(age_na)

    if args.live_audit:
        baseline = json.loads(args.live_audit.read_text())
        results['comparison_source'] = {'file': args.live_audit.name, 'sha256': sha256(args.live_audit)}
        results['header_comparison'] = {}
        for table in CORE:
            current = {row['column_name'] for row in baseline['column_inventory'] if row['table_name']==table}
            historical = set(results['headers'][table])
            results['header_comparison'][table] = {
                'snapshot_columns': len(historical), 'live_audit_columns': len(current),
                'only_in_snapshot': sorted(historical-current), 'only_in_live_audit': sorted(current-historical),
            }
    # Explicit checks remain active even if Python is run with optimization.
    check = results['studies']
    if check['missing_id_rows'] or check['extra_nonempty_id_rows']:
        raise ValueError('Study IDs are not complete and unique; candidate counts require review.')
    if sum(results['distributions']['study_type'].values()) != check['rows']:
        raise ValueError('Study-type counts do not reconcile.')
    if not 0 <= results['windows']['30']['trials'] <= results['windows']['60']['trials'] <= results['windows']['90']['trials'] == waterfall['within_90_days'] <= len(candidates):
        raise ValueError('Candidate-window counts do not reconcile.')
    if sum(waterfall[key] for key in waterfall if key.startswith('excluded_')) + waterfall['within_90_days'] != check['rows']:
        raise ValueError('Exclusion waterfall does not reconcile.')
    for values in results['core_table_cardinality'].values():
        if values['distinct_nonempty_ids']-values['orphan_ids']+values['studies_without_rows'] != check['unique_nonempty_ids']:
            raise ValueError('Child-table coverage does not reconcile.')
    for days, values in results['date_precision_sensitivity']['windows'].items():
        if not values['definitely_in_window'] <= results['windows'][days]['trials'] <= values['possibly_in_window']:
            raise ValueError('Point-date count falls outside date-precision sensitivity bounds.')
    results['validation'] = 'ZIP CRCs, record widths, unique study IDs, category totals, exclusion waterfall, nested windows, and child-table coverage passed'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(results,indent=2)+'\n')
    print('Saved snapshot measurements to '+str(args.output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--snapshot-date', type=date.fromisoformat, required=True)
    parser.add_argument('--catalog-url', required=True)
    parser.add_argument('--live-audit', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    inspect(parser.parse_args())
