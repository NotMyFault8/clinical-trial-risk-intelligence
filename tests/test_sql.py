from pathlib import Path
import duckdb
import pandas as pd

def test_child_tables_aggregate_before_join_without_inflation():
    con=duckdb.connect()
    rows={
    'studies':[dict(nct_id='NCT00000001',phase='Phase 2',enrollment='999',enrollment_type='Actual',number_of_arms='2',has_dmc='Yes')],
    'designs':[dict(nct_id='NCT00000001',allocation='Randomized',intervention_model='Parallel',primary_purpose='Treatment',masking='Double')],
    'eligibilities':[dict(nct_id='NCT00000001',gender='All',minimum_age='18 Years',maximum_age='N/A',healthy_volunteers='No',criteria='Adults')],
    'sponsors':[dict(nct_id='NCT00000001',lead_or_collaborator='lead',agency_class='INDUSTRY',name='Lead')],
    'conditions':[dict(nct_id='NCT00000001',name=n) for n in ['a','b']],
    'interventions':[dict(nct_id='NCT00000001',intervention_type=t) for t in ['Drug','Device']],
    'facilities':[dict(nct_id='NCT00000001',country=c) for c in ['United States','Canada','Canada']]}
    for name,r in rows.items():con.register(name,pd.DataFrame(r))
    result=con.execute((Path(__file__).parents[1]/'sql/phase2/trial_features.sql').read_text()).df()
    assert len(result)==1
    r=result.iloc[0]
    assert r.condition_count==2 and r.intervention_count==2 and r.facility_count==3 and r.country_count==2
    assert pd.isna(r.planned_enrollment) and r.planned_enrollment_missing==1
