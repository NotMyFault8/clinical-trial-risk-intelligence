import json
import pytest
from fastapi.testclient import TestClient

from clinical_trial_risk.api.app import app
from clinical_trial_risk.api import extraction


def test_api_exposes_exact_saved_comparison_and_research_release_state():
    with TestClient(app) as client:
        response = client.get('/extraction/evaluation')
        assert response.status_code == 200
        data = response.json()
        assert data['mode'] == 'saved_research_results'
        assert (data['dataset']['records'], data['dataset']['trials'], data['dataset']['groups']) == (100, 50, 50)
        systems = {item['id']: item for item in data['systems']}
        revised = systems['llm_v3']['matched_prefix']
        assert revised['micro'] == {
            'tp': 316, 'fp': 834, 'fn': 275,
            'precision': 316 / 1150, 'recall': 316 / 591, 'f1': 632 / 1741,
        }
        assert revised['document_schema_valid_rate'] == .88
        assert systems['token_ner']['matched_prefix']['micro']['f1'] > revised['micro']['f1']
        assert data['release']['semantic_release_passed'] is False
        assert data['release']['live_extraction_enabled'] is False
        assert set(data['release']['numeric_checks']) == {'schema', 'precision', 'f1'}


def test_ai_review_case_api_preserves_all_saved_evidence_and_counts():
    with TestClient(app) as client:
        overview = client.get('/extraction/review').json()
        assert overview['review_type'] == 'AI_secondary_review'
        assert overview['reviewer'] == 'Codex (AI)'
        assert overview['reviewed_cases'] == len(overview['cases']) == 12
        assert overview['clinical_eligibility_logic_validated'] is False
        totals = {}
        for brief in overview['cases']:
            response = client.get(brief['detail_url'])
            assert response.status_code == 200
            case = response.json()['case']
            assert case['record_id'] == brief['record_id']
            for label in ('A', 'B'):
                output = case[label]
                counts = totals.setdefault(output['system'], dict(tp=0, fp=0, fn=0))
                for key in counts:
                    counts[key] += output['metrics'][key]
                for item in output['prediction_checks']:
                    assert case['source'][item['start']:item['end']] == item['evidence']
        for system, counts in totals.items():
            assert counts == {key: overview['aggregate'][system][key] for key in counts}


def test_review_paths_and_markdown_contract_are_documented():
    with TestClient(app) as client:
        assert client.get('/extraction/review/cases/review-99').status_code == 404
        assert client.get('/extraction/review/cases/not-a-case').status_code == 422
        for path in ('/extraction/report', '/extraction/review/report'):
            response = client.get(path)
            assert response.status_code == 200
            assert response.headers['content-type'].startswith('text/markdown')
            assert 'human_review.md' not in response.text
        schema = client.get('/openapi.json').json()
        assert schema['info']['version'] == '0.3.0'
        assert 'text/markdown' in schema['paths']['/extraction/report']['get']['responses']['200']['content']


@pytest.mark.parametrize('path', [
    '/extraction/evaluation', '/extraction/review', '/extraction/review/cases/review-01',
    '/extraction/report', '/extraction/review/report',
])
def test_missing_research_artifacts_return_503_without_local_paths(monkeypatch, tmp_path, path):
    monkeypatch.setattr(extraction, 'RESULTS_DIR', tmp_path)
    with TestClient(app) as client:
        response = client.get(path)
        assert response.status_code == 503
        assert response.json()['detail']['code'] == 'research_artifact_unavailable'
        assert str(tmp_path) not in response.text


def test_corrupt_review_json_and_incomplete_case_fail_explicitly(monkeypatch, tmp_path):
    original = json.loads((extraction.RESULTS_DIR / 'ai_second_review.json').read_text())
    monkeypatch.setattr(extraction, 'RESULTS_DIR', tmp_path)
    path = tmp_path / 'ai_second_review.json'
    with TestClient(app) as client:
        path.write_text('{broken')
        assert client.get('/extraction/review').status_code == 503
        original['reviewed_cases'] = 13
        path.write_text(json.dumps(original))
        assert client.get('/extraction/review').status_code == 503
        original['reviewed_cases'] = 12
        prediction = original['cases'][0]['A']['prediction_checks'][0]
        start = prediction['start']
        prediction['start'] = '<invalid offset>'
        path.write_text(json.dumps(original))
        assert client.get('/extraction/review/cases/review-01').status_code == 503
        prediction['start'] = start
        original['cases'][0].pop('source')
        path.write_text(json.dumps(original))
        assert client.get('/extraction/review/cases/review-01').status_code == 503
