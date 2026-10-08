"""Stream immutable AACT archives, aggregate in SQL, and isolate outcomes.

Source snapshot dates are recorded; execution timestamps are deliberately omitted.
"""
from __future__ import annotations
import argparse
import calendar
from collections import Counter
import csv
from datetime import date, datetime, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

import duckdb
import pandas as pd

ROOT = Path(os.environ.get('CTR_PROJECT_ROOT',Path(__file__).resolve().parents[3]))
TABLES = ['studies','designs','eligibilities','sponsors','conditions','interventions','facilities']
STUDY_FIELDS = ['nct_id','phase','enrollment','enrollment_type','number_of_arms','has_dmc',
                'is_fda_regulated_drug','is_fda_regulated_device']
ACTIVE = {'not_yet_recruiting','recruiting','enrolling_by_invitation'}
PLANNED = {'anticipated','estimated'}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()


def normalize(value):
    return (value or '').strip().lower().replace(',','').replace(' ','_')


def parse_date(value):
    try: return date.fromisoformat(value)
    except (ValueError,TypeError): return None


def start_interval(text):
    """Preserve month precision: unknown day is not an observed month-end date."""
    for fmt in ['%B %d, %Y','%Y-%m-%d','%B %Y','%Y-%m']:
        try:
            d=datetime.strptime(text,fmt).date()
            if fmt in ['%B %Y','%Y-%m']:
                return d,d.replace(day=calendar.monthrange(d.year,d.month)[1]),'month'
            return d,d,'day'
        except (ValueError,TypeError): pass
    return None,None,'unparsed'


def eligibility(row, snapshot, days=90):
    """Return first exclusion or definite/possible inclusion; no outcome consulted."""
    if normalize(row['study_type'])!='interventional': return 'non_interventional',False,False
    if normalize(row['start_date_type']) not in PLANNED: return 'start_not_planned',False,False
    posted=parse_date(row['study_first_posted_date'])
    if not posted: return 'missing_posted_date',False,False
    if posted>snapshot: return 'posted_after_snapshot',False,False
    updated=parse_date(row['last_update_posted_date'])
    if updated and updated>snapshot: return 'updated_after_snapshot',False,False
    if normalize(row['overall_status']) not in ACTIVE: return 'baseline_status_ineligible',False,False
    lower,upper,_=start_interval(row['start_month_year'])
    if lower is None: return 'unparsed_start',False,False
    cutoff=snapshot+timedelta(days=days)
    possible=upper>snapshot and lower<=cutoff
    definite=lower>snapshot and upper<=cutoff
    return ('definite' if definite else 'ambiguous_window' if possible else 'outside_window'),definite,possible


def records(z,table,headers):
    csv.field_size_limit(20*1024*1024)
    with z.open(table+'.txt') as f:
        r=csv.reader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''),delimiter='|',strict=True)
        actual=next(r)
        if actual!=headers: raise ValueError(f'Schema changed: {table}')
        for i,values in enumerate(r,2):
            if len(values)!=len(headers): raise ValueError(f'{table}:{i}: malformed width')
            yield dict(zip(headers,values))


def source_path(source):
    path=ROOT/source['archive_path']
    if digest(path)!=source['archive_sha256']: raise ValueError(f'Archive checksum mismatch: {path}')
    return path


def validate_aggregation(frame,expected_rows):
    if len(frame)!=expected_rows or frame.nct_id.isna().any() or frame.nct_id.duplicated().any():
        raise ValueError('Join cardinality failed')
    if frame.lead_count.isna().any() or not frame.lead_count.eq(1).all():
        raise ValueError('Expected exactly one lead sponsor per trial')


def extract_baseline(source,seen_primary,seen_possible):
    snapshot=date.fromisoformat(source['snapshot_date'])
    counts=Counter(); types=Counter(); statuses=Counter(); rows=[]; provenance=[]; idset=set()
    with zipfile.ZipFile(source_path(source)) as z:
        for row in records(z,'studies',source['headers']['studies']):
            nct=row['nct_id']
            if not nct or nct in idset: raise ValueError('Missing/duplicate study key')
            idset.add(nct); types[row['start_date_type'] or 'NULL']+=1
            status,primary,possible=eligibility(row,snapshot)
            counts[status]+=1
            if not possible: continue
            statuses[row['overall_status']]+=1
            primary=primary and nct not in seen_primary
            possible=possible and nct not in seen_possible
            if not (primary or possible): counts['repeat_candidate_skipped']+=1; continue
            if primary: seen_primary.add(nct)
            if possible: seen_possible.add(nct)
            rows.append({k:row[k] for k in STUDY_FIELDS})
            lower,upper,precision=start_interval(row['start_month_year'])
            provenance.append(dict(nct_id=nct,snapshot_date=snapshot.isoformat(),primary=primary,
                possible=possible,start_lower=lower.isoformat(),start_upper=upper.isoformat(),
                date_precision=precision,baseline_status=row['overall_status'],
                first_posted_date=row['study_first_posted_date'],last_update_posted_date=row['last_update_posted_date'],
                title=row['brief_title']))
        selected={r['nct_id'] for r in rows}
        tables={'studies':pd.DataFrame(rows,columns=STUDY_FIELDS)}
        audit={'source_rows':len(idset),'first_exclusion_counts':dict(counts),
               'start_type_vocabulary':dict(types),'eligible_baseline_statuses':dict(statuses),
               'selected':len(selected),'tables':{}}
        for table in TABLES[1:]:
            selected_rows=[]; total=0; orphans=0; nulls=0; keys=Counter()
            for row in records(z,table,source['headers'][table]):
                total+=1; nct=row['nct_id']; nulls+=not bool(nct); orphans+=bool(nct) and nct not in idset
                if nct in selected: selected_rows.append(row); keys[nct]+=1
            if orphans or nulls: raise ValueError(f'{table}: null/orphan foreign keys')
            if table in ['designs','eligibilities'] and any(n!=1 for n in keys.values()):
                raise ValueError(f'{table}: one-to-one join would multiply rows')
            tables[table]=pd.DataFrame(selected_rows,columns=source['headers'][table])
            audit['tables'][table]={'source_rows':total,'selected_rows':len(selected_rows),
                'selected_trials':len(keys),'missing_trials':len(selected)-len(keys),
                'max_rows_per_selected_trial':max(keys.values(),default=0),'null_keys':int(nulls),'orphans':int(orphans)}
            print(snapshot,table,total,'selected',len(selected_rows),flush=True)
    con=duckdb.connect()
    for table,df in tables.items(): con.register(table,df)
    # Selected children are also retained for auditable SQL reproduction.
    interim=ROOT/'data/interim'/snapshot.isoformat(); interim.mkdir(parents=True,exist_ok=True)
    for table,df in tables.items(): df.to_parquet(interim/(table+'.parquet'),index=False)
    result=con.execute((ROOT/'sql/phase2/trial_features.sql').read_text()).df(); con.close()
    validate_aggregation(result,len(selected))
    result.insert(1,'snapshot_date',snapshot.isoformat())
    return result,pd.DataFrame(provenance),audit


def extract_outcomes(source,needed):
    found={}; source_ids=set(); rowcount=0
    with zipfile.ZipFile(source_path(source)) as z:
        for row in records(z,'studies',source['headers']['studies']):
            rowcount+=1; nct=row['nct_id']
            if not nct or nct in source_ids: raise ValueError('Outcome key failure')
            source_ids.add(nct)
            if nct in needed:
                status=normalize(row['overall_status'])
                found[nct]={'nct_id':nct,'outcome_snapshot':source['snapshot_date'],
                    'outcome_status':status,'label':{'completed':0,'terminated':1}.get(status),
                    'outcome_last_update':row['last_update_posted_date']}
    for nct in needed-set(found):
        found[nct]={'nct_id':nct,'outcome_snapshot':source['snapshot_date'],
            'outcome_status':'missing_record','label':None,'outcome_last_update':None}
    return pd.DataFrame(found.values()),rowcount


def main():
    manifest=json.loads((ROOT/'configs/snapshots.json').read_text())
    sources=manifest['sources']; features=[]; metadata=[]; audits={}; seen_primary=set(); seen_possible=set()
    dest=ROOT/'data/processed'; dest.mkdir(parents=True,exist_ok=True)
    report=ROOT/'reports/cohort'; report.mkdir(parents=True,exist_ok=True)
    for source in sources:
        if source['role']!='baseline': continue
        f,m,a=extract_baseline(source,seen_primary,seen_possible)
        features.append(f); metadata.append(m); audits[source['snapshot_date']]=a
    features=pd.concat(features,ignore_index=True); metadata=pd.concat(metadata,ignore_index=True)
    labels=[]
    for source in sources:
        if source['role']!='outcome': continue
        baseline=str(int(source['snapshot_date'][:4])-5)+source['snapshot_date'][4:]
        needed=set(metadata.loc[metadata.snapshot_date==baseline,'nct_id'])
        l,rows=extract_outcomes(source,needed); l.insert(1,'snapshot_date',baseline)
        labels.append(l); audits[baseline]['outcome_source_rows']=rows
        print('Outcome',source['snapshot_date'],l.outcome_status.value_counts().to_dict(),flush=True)
    labels=pd.concat(labels,ignore_index=True)
    joined=metadata.merge(labels,on=['nct_id','snapshot_date'],validate='one_to_one')
    for snapshot,group in joined.groupby('snapshot_date'):
        p=group[group.primary]; audits[snapshot]['primary_status_counts']=p.outcome_status.value_counts().to_dict()
        audits[snapshot]['primary_trials']=len(p)
        audits[snapshot]['resolved_primary_trials']=int(p.label.notna().sum())
    features.to_parquet(dest/'baseline_features.parquet',index=False)
    metadata.to_parquet(dest/'cohort_metadata.parquet',index=False)
    labels.to_parquet(dest/'outcomes.parquet',index=False)
    missing=features.isna().sum().to_dict()
    (report/'audit.json').write_text(json.dumps({'snapshots':audits,'feature_missing_counts':missing,
        'rows':len(features),'primary_trials':int(metadata.primary.sum()),
        'source_manifest_sha256':digest(ROOT/'configs/snapshots.json'),
        'pipeline_sha256':digest(Path(__file__)),'aggregation_sha256':digest(ROOT/'sql/phase2/trial_features.sql'),
        'outputs':{p.name:digest(p) for p in dest.glob('*.parquet')}},indent=2)+'\n')


if __name__=='__main__': main()
