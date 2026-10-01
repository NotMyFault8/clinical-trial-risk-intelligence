import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from clinical_trial_risk.data.cohort import ROOT
from clinical_trial_risk.models.train import load_data
from clinical_trial_risk.reporting.packets import runtime,template
from clinical_trial_risk.api.app import app

pytestmark=[pytest.mark.integration,pytest.mark.skipif(not (ROOT/'artifacts/model_registry.json').exists(),reason='Frozen local artifacts required')]

def test_temporal_and_key_invariants_on_real_data():
    d=load_data();assert not d.nct_id.duplicated().any()
    assert d[d.split=='train'].year.max()<d[d.split=='test'].year.min()
    assert not set(d[d.split=='tune'].sponsor_cluster)&set(d[d.split=='calibrate'].sponsor_cluster)
    m=pd.read_parquet(ROOT/'data/processed/cohort_metadata.parquet');m=m[m.primary]
    assert (m.start_lower>m.snapshot_date).all()
    assert (pd.to_datetime(m.start_upper)<=pd.to_datetime(m.snapshot_date)+pd.Timedelta(days=90)).all()

def test_baseline_report_has_no_outcome_fields_and_exact_evidence():
    rt=runtime();p=rt.packet(rt.ids[0]);body=template(p)
    assert p['probability_display'] in body
    assert not {'label','outcome_status','why_stopped','completion_date'}&set(p)
    text=p['sources'][0]['text']
    for item in p['extractions']:assert text[item['start']:item['end']]==item['evidence']
    from scipy.special import expit
    a=p['attributions'];assert np.isclose(expit(a['base_log_odds']+a['all_contributions_sum']),p['probability'])

def test_api_matches_direct_packet_and_unknown_trial_abstains():
    with TestClient(app) as c:
        assert c.get('/health').status_code==200
        rt=runtime();nct=rt.ids[0];r=c.get(f'/trials/{nct}/report')
        assert r.status_code==200
        assert r.json()['packet']['probability']==rt.packet(nct)['probability']
        assert c.get('/trials/NCT99999999/report').status_code==404
