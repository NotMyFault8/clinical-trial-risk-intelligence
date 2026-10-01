import json
from clinical_trial_risk.reporting.evaluate import check_generated

def packet():return {'probability_display':'12.3%','percentile_display':'60.0','limitations':'Research only.',
    'evidence':[{'source_id':'baseline:1','quote':'Age > 18 years'}]}
def response(**changes):
    r={'risk_display':'12.3%','percentile_display':'60.0','overview':'Research record.',
       'associations':'Associated model factors.', 'evidence':[{'source_id':'baseline:1','quote':'Age > 18 years'}],
       'limitations':'Research only.','analyst_check':'Verify missing information.'}
    r.update(changes);return json.dumps(r)
def test_fabricated_probability_blocks_generated_report():
    x=check_generated(response(risk_display='99%'),packet())
    assert not x['automated_checks_pass'] and not x['released']
def test_fabricated_source_or_quote_fails():
    x=check_generated(response(evidence=[{'source_id':'future:1','quote':'Trial terminated'}]),packet())
    assert not x['automated_checks_pass'] and x['exact_supported_citations']==0
def test_missing_evidence_requires_abstention():
    p=packet();p['evidence']=[]
    assert check_generated(response(evidence=[]),p)['automated_checks_pass']
    assert not check_generated(response(),p)['automated_checks_pass']
def test_automated_fidelity_is_not_semantic_release():
    x=check_generated(response(),packet())
    assert x['automated_checks_pass'] and not x['released']
