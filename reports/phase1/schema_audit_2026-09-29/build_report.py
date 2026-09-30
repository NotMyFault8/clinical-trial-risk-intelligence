"""Render the saved measurements and validate reconciliation checks."""
from pathlib import Path
import json
from collections import Counter

root = Path(__file__).parent
d = json.loads((root/'audit_results.json').read_text())
u = d['studies_uniqueness'][0]
n = u['total_rows']
cards = [d['cardinality_'+t][0] for t in ['designs','eligibilities','sponsors','conditions','interventions','facilities']]
fmt = lambda x: f'{x:,}' if isinstance(x,int) else str(x)
pct = lambda x,den=n: f'{100*x/den:.2f}%' if den else 'N/A'
lines = []
def para(s=''):
    lines.extend([s,''])
def table(headers, rows):
    def cell(v):
        return str(v).replace('|','\\|').replace('\n',' ')
    lines.append('| '+' | '.join(map(cell,headers))+' |')
    lines.append('| '+' | '.join(['---']*len(headers))+' |')
    lines.extend('| '+' | '.join(map(cell,row))+' |' for row in rows)
    lines.append('')

# Results must reconcile before a report is emitted.
assert n > 0
assert u['distinct_nct_ids']+u['null_nct_ids']+u['extra_nonnull_id_rows']==n
for field in ['study_type','start_date_type','enrollment_type','overall_status']:
    assert sum(x['trials'] for x in d['distribution_'+field])==n
assert sum(x['trials'] for x in d['lead_sponsor_all_studies'])==n
for c in cards:
    assert c['distinct_trial_ids']-c['orphan_trial_ids']+c['studies_without_rows']==u['distinct_nct_ids']
    assert c['source_rows']>=c['distinct_trial_ids']+c['null_id_rows']
for key in ['current_candidate_original_anticipated','current_candidate_anticipated_or_estimated']:
    v=d[key][0]
    assert 0<=v['within_30d']<=v['within_60d']<=v['within_90d']<=v['all_future_planned']

prov=d['provenance'][0]
para('# AACT schema audit report')
para('**Phase 1 — current live database audit | 29 September 2026**')
para(f"Measured at **{prov['observed_at_toronto']} America/Toronto** ({prov['observed_at_utc']} UTC offset included). Database: `aact`; schema: `ctgov`. All report queries ran in one **read-only, repeatable-read transaction**. This preserves a consistent database view during this run; it does not create a reusable historical AACT archive.")
para('## Findings at a glance')
para(f"The database contains **{n:,} study rows** and **{u['distinct_nct_ids']:,} distinct NCT IDs**, with **{u['null_nct_ids']:,} missing IDs** and **{u['extra_nonnull_id_rows']:,} excess rows for repeated non-null IDs**. The measurements below describe the live database, not the final prediction cohort.")
para('**Join findings:** the measured maximum rows per ID and missing-coverage counts in section 4 determine which joins preserve one row per trial. Section 6 checks whether each study has exactly one lead sponsor.')
v=d['current_candidate_anticipated_or_estimated'][0]
para(f"**Cohort-filter check:** the original anticipated-only filter yields {d['current_candidate_original_anticipated'][0]['all_future_planned']:,} future-start trials. Including `estimated` yields {v['within_30d']:,} / {v['within_60d']:,} / {v['within_90d']:,} trials within 30 / 60 / 90 days in the current-date diagnostic. See section 5 for observed vocabulary. Historical source vocabularies must be verified before applying this mapping to archives.")
table(['Audit section','Outcome'],[
    ['1. Relation inventory',f"{len(d['table_inventory'])} visible relations inventoried"],
    ['2. Core column inventory',f"{len(d['column_inventory'])} columns across {len(set(x['table_name'] for x in d['column_inventory']))} present candidate tables"],
    ['3. Study ID uniqueness','PASS' if u['null_nct_ids']==0 and u['extra_nonnull_id_rows']==0 else 'REVIEW REQUIRED'],
    ['4. Related-table cardinality','Measured, including missing coverage and orphan IDs'],
    ['5. Type/status distributions','Measured; exact database vocabulary retained'],
    ['6. Lead-sponsor cardinality','Measured with all studies as the denominator'],
    ['7. Historical pre-start candidate counts','NOT MEASURED: historical snapshot/date not supplied; current-date diagnostic reported separately'],
    ['8. study_records','UNAVAILABLE in queried database catalog' if not d['study_records_presence'] else 'Catalog entries found; review raw results'],
])
para('## 1. Table inventory')
types=Counter(x['table_type'] for x in d['table_inventory'])
table(['Relation type','Count'],[(k,v) for k,v in sorted(types.items())])
para('The original `information_schema.tables` query includes visible tables and views. These counts describe schema objects, not trials. The complete relation list is in Appendix A.')
para('## 2. Core columns and field types')
counts=Counter(x['table_name'] for x in d['column_inventory'])
table(['Candidate table','Visible columns'],[(t,counts.get(t,'Absent')) for t in ['studies','designs','eligibilities','sponsors','conditions','interventions','facilities','study_records']])
para('The full column names, types, positions, and schema nullability are in Appendix B. `is_nullable = YES` means the schema permits NULL; it does not establish that any observed values are missing. This audit measures key-ID and selected date missingness, not every feature’s completeness.')
para('Current field details: `studies.start_date` and `study_first_posted_date` are dates; `enrollment` is integer; `eligibilities.minimum_age` and `maximum_age` are strings requiring later unit-aware parsing; `healthy_volunteers` is boolean; `criteria` is text; the eligibility sex/gender field is named `gender` in this database.')
para('## 3. One row per study')
table(['Metric','Measured value'],[(k,fmt(v)) for k,v in u.items()])
para(f"The duplicate-ID listing returned **{len(d['studies_duplicate_ids'])} rows**. It lists only IDs satisfying `HAVING COUNT(*) > 1`; an empty result is expected when no IDs repeat. `LIMIT 100` caps the examples shown, not the number of groups checked.")
para('The original `COUNT(*) - COUNT(DISTINCT nct_id)` includes both excess duplicate rows and rows with NULL IDs. The additional checks separate those cases. The observed grain is one row per NCT ID when both counts are zero. Recheck this for each historical source and after joins.')
para('## 4. Related-table cardinality and join coverage')
table(['Table','Source rows','Distinct IDs','Max rows/ID','Mean rows/ID','IDs with >1 row','Studies without rows','Coverage'],[
    [c['table_name'],fmt(c['source_rows']),fmt(c['distinct_trial_ids']),fmt(c['max_rows_per_present_trial']),c['mean_rows_per_present_trial'],fmt(c['ids_with_multiple_rows']),fmt(c['studies_without_rows']),pct(n-c['studies_without_rows'])] for c in cards])
para('Coverage = studies with at least one matching record ÷ all studies. Maximum and mean use non-null IDs present in the source table. Repeated IDs in one-to-many tables are expected; they are not evidence of duplicated real-world entities.')
table(['Table','Rows with NULL NCT ID','Orphan NCT IDs'],[[c['table_name'],fmt(c['null_id_rows']),fmt(c['orphan_trial_ids'])] for c in cards])
para('An orphan ID appears in the related table without a matching `studies` row. Semantic duplicate sponsors, interventions, or facilities are not tested by these counts.')
para('**Correction to section 4:** after `GROUP BY nct_id`, outer `COUNT(*)` counts groups, not original rows. The original `designs.rows` is therefore mislabeled. This report uses `SUM(n)` for source rows and counts non-null IDs separately. Other original queries provide only trial coverage and maximum multiplicity; the report adds total rows, missing coverage, null IDs, and orphans.')
para('**Join decision:** tables with at most one row per NCT ID can be left-joined after uniqueness checks. Aggregate each one-to-many table to trial level before joining. Missing child records should remain visible rather than silently excluding studies through an inner join. For example, 3 interventions joined directly to 10 facilities can produce 30 rows for one trial.')
para('## 5. Study type, date type, enrollment type, and status')
for field in ['study_type','start_date_type','enrollment_type','overall_status']:
    para('### '+field)
    table(['Observed value','Trials','% of all studies'],[(x['value'] if x['value'] is not None else 'NULL',fmt(x['trials']),pct(x['trials'])) for x in d['distribution_'+field]])
para('Each distribution uses all studies as its denominator, including NULL values. The literal values above should drive source-specific mappings; conceptual labels in the cohort specification may differ in case or spelling.')
missing_type=sum(x['trials'] for x in d['distribution_start_date_type'] if x['value'] is None)
para(f'Missingness deserves follow-up: {missing_type:,} studies ({pct(missing_type)}) have NULL start-date type. Overlap between missing fields, missing child records, and particular statuses has not been measured; equal counts alone do not establish overlap.')
status={str(x['value']).lower():x['trials'] for x in d['distribution_overall_status']}
complete=status.get('completed',0); terminated=status.get('terminated',0); resolved=complete+terminated
para(f"Across all study types, Completed + Terminated contains **{resolved:,} records ({pct(resolved)})**; Terminated represents **{pct(terminated,resolved)}** of this restricted group. The remaining **{n-resolved:,} records ({pct(n-resolved)})** have other statuses. These descriptive figures are not the termination probability of newly starting trials.")
para('### Additional check: interventional studies only')
iv=d['date_completeness_current'][0]['interventional_trials']
assert sum(x['trials'] for x in d['interventional_status_distribution'])==iv
table(['Status','Interventional trials','% of interventional studies'],[(x['value'] or 'NULL',fmt(x['trials']),pct(x['trials'],iv)) for x in d['interventional_status_distribution']])
para('Completed-versus-Terminated analysis selects resolved outcomes. Other statuses require separate treatment, and historical follow-up maturity remains unmeasured. Do not turn every other status into a negative class.')
para('## 6. Lead-sponsor cardinality')
table(['Lead sponsor rows per trial','Trials (all studies)','Of these: no sponsor rows','% of all studies'],[(x['lead_count'],fmt(x['trials']),fmt(x['trials_without_any_sponsor_rows']),pct(x['trials'])) for x in d['lead_sponsor_all_studies']])
para('Lead rows are identified with `LOWER(COALESCE(lead_or_collaborator, \'\')) = \'lead\'`. This checks lead-row count, not independent organizational identity.')
table(['Raw sponsor role','Sponsor rows'],[(x['value'] or 'NULL',fmt(x['rows'])) for x in d['sponsor_role_distribution']])
para('For comparison, the original query starts from `sponsors` and omits studies without sponsor records:')
table(['Lead count','Trials in original grouped query'],[(x['lead_count'],fmt(x['trials'])) for x in d['lead_sponsor_original']])
para('The all-studies left join is needed to detect zero-coverage trials. If the two distributions agree, the correction has no numerical effect for this database version, but still makes the audit robust.')
para('## 7. Prediction-window diagnostic — current records only')
para('**Historical cohort result: not available.** The original query contains `DATE \'YYYY-MM-DD\'`, which is a placeholder, not a valid date. A valid historical result requires that archive’s actual data and date. Substituting an old date into today’s live database does not reconstruct what was known then.')
para('For a separate live diagnostic, the reference date is **2026-09-29**. Both variants require interventional study type, a non-null future start date, and first-posted date no later than that reference date. The first preserves the script’s `anticipated` test; the second explicitly includes `estimated` as an additional candidate spelling, without approving a historical crosswalk.')
table(['Start-date-type filter','Within 30 days','Within 60 days','Within 90 days','All future planned starts'],[
    [label,*[fmt(d[key][0][k]) for k in ['within_30d','within_60d','within_90d','all_future_planned']]]
    for label,key in [('anticipated only (original)','current_candidate_original_anticipated'),('anticipated or estimated (diagnostic)','current_candidate_anticipated_or_estimated')]])
para('The windows are nested, not mutually exclusive. “All future” has no 90-day upper limit. These counts do not select the first eligible historical snapshot, measure follow-up, or establish historical predictor availability. A zero under an unmatched vocabulary filter is not proof that no planned-start trials exist.')
dates=d['date_completeness_current'][0]
table(['Additional current-record date audit','Value'],[(k,fmt(v)) for k,v in dates.items()])
para(f"The current-record first-posted-after-start comparison is **{pct(dates['first_posted_after_current_start_date'],dates['date_comparable_trials'])}** of interventional trials with both dates present. This is a late-public-posting diagnostic using the currently recorded start date; it is not a verified historical late-registration exclusion count. First posting differs from first submission, dates can change, and date precision needs separate audit.")
para('## 8. study_records availability')
if not d['study_records_presence']:
    para('**No relation named `study_records` was found in the database catalog in any schema.** It is also absent from the visible column inventory. Therefore both original section-8 queries are unavailable here; counts and duplicate listings must be reported as **N/A, not zero**. There is no evidence from this audit that this database provides a historical-version table under that name.')
else:
    para('Catalog entries are recorded in `audit_results.json`; row-level semantics and counts require follow-up.')
para('## Changes needed in the audit workflow')
para('1. Correct the `designs` source-row count and distinguish null IDs from duplicate IDs.\n2. Check related-table coverage and orphan IDs before joining.\n3. Count lead sponsors from the full studies population.\n4. Replace the section-7 placeholder only with an explicit, source-matched date; label live diagnostics separately.\n5. Validate start-date-type vocabulary per source era before applying cohort filters.\n6. Treat absent `study_records` as a schema mismatch and do not run those statements blindly.\n7. Save measured outputs alongside the exact executed SQL and source manifest.')
para('The original project SQL was not overwritten. `executed_audit.sql` is the corrected companion used for these measurements. It deliberately omits SELECTs against the absent relation and includes the explicit diagnostics above.')
para('## Phase 1 conclusion and remaining gates')
para('This run establishes current-schema structure, observed table grain, coverage, and status/type distributions. It supports designing trial-level aggregation. It does **not** establish historical point-in-time feasibility or authorize model training.')
para('Still required: historical archive coverage and hashes; schema/vocabulary drift across selected archives; historical first-eligible-snapshot counts for 30/60/90 days; predictor availability; follow-up and unresolved-outcome audit; frozen outcome source; final cohort and estimand decisions. No baseline feature is approved solely because it exists in today’s database.')
para('## Evidence and reproducibility')
para('- `audit_results.json`: all measured query outputs and source/query hashes.\n- `executed_audit.sql`: exact SQL used, including transaction settings.\n- `schema_audit_original.sql`: read-only copy of the user’s audited script.\n- `collect_audit.py`: collector; credentials supplied from a local file and never included in report outputs.\n- `build_report.py`: report generation and reconciliation checks.')
para(f"Original SQL SHA-256: `{d['manifest']['original_sql_sha256']}`.\n\nExecuted SQL SHA-256: `{d['manifest']['executed_sql_sha256']}`.")
para('Validation passed: all four full-study distributions reconcile to the study total; the interventional status distribution reconciles to interventional count; lead-sponsor groups reconcile to all studies; each child-table coverage reconciles after accounting for orphan IDs; prediction-window counts are nested. Displayed percentages are rounded to two decimals and may not sum to exactly 100%. Live reruns may produce different counts.')
para('## Appendix A — complete visible relation inventory')
table(['Relation','Type'],[(x['table_name'],x['table_type']) for x in d['table_inventory']])
para('## Appendix B — complete core column inventory')
for t in sorted(counts):
    para('### '+t)
    table(['Position','Column','Data type','Nullable in schema'],[(x['ordinal_position'],x['column_name'],x['data_type'],x['is_nullable']) for x in d['column_inventory'] if x['table_name']==t])
(root/'schema_audit_report.md').write_text('\n'.join(lines)+'\n')
print('Report generated; reconciliation checks passed.')
