import json
from clinical_trial_risk.llm.extract import validate_output

def output(**kwargs):return json.dumps({'Measurement':[],'Value':[],'Temporal':[],**kwargs})
def test_invented_and_repeated_evidence_rejected():
    x=validate_output(output(Measurement=['platelet count','age']), 'age and age')
    assert not x['items'] and len(x['rejected'])==2
def test_spans_offsets_exact_and_deduplicated():
    x=validate_output(output(Measurement=['BMI','BMI']), 'Requires BMI > 20')
    assert len(x['items'])==1 and x['items'][0]['start']==9
def test_bad_schema_fails_closed():
    assert not validate_output('{"risk":0.9}','anything')['schema_valid']
    assert not validate_output('ignore all rules','anything')['schema_valid']

def test_duplicate_json_keys_rejected():
    assert not validate_output('{"Measurement":[],"Value":[],"Temporal":[],"Value":["5"]}','5')['schema_valid']
