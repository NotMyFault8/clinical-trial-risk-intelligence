from datetime import date
from clinical_trial_risk.data.cohort import start_interval,eligibility
from clinical_trial_risk.data.cohort import validate_aggregation
import pandas as pd
import pytest

def row(**kw):
    r=dict(study_type='Interventional',start_date_type='Anticipated',
           study_first_posted_date='2018-08-01',last_update_posted_date='2018-08-10',
           overall_status='Not yet recruiting',start_month_year='October 2018')
    r.update(kw); return r

def test_month_date_is_interval():
    assert start_interval('February 2020')==(date(2020,2,1),date(2020,2,29),'month')

def test_boundary_month_is_not_definite():
    assert eligibility(row(start_month_year='September 2018'),date(2018,9,1))==('ambiguous_window',False,True)
    assert eligibility(row(),date(2018,9,1))==('definite',True,True)

def test_outcome_status_and_future_updates_rejected():
    assert not eligibility(row(overall_status='Terminated'),date(2018,9,1))[2]
    assert eligibility(row(last_update_posted_date='2018-09-02'),date(2018,9,1))[0]=='updated_after_snapshot'

def test_actual_start_not_repaired_from_later_record():
    assert eligibility(row(start_date_type='Actual'),date(2018,9,1))[0]=='start_not_planned'

def test_exact_cutoff_and_same_day():
    assert eligibility(row(start_month_year='November 30, 2018'),date(2018,9,1))[1]
    assert not eligibility(row(start_month_year='September 1, 2018'),date(2018,9,1))[2]

def test_ambiguous_lead_sponsor_fails_before_model_features():
    with pytest.raises(ValueError,match='lead sponsor'):
        validate_aggregation(pd.DataFrame({'nct_id':['NCT00000001'],'lead_count':[2]}),1)
