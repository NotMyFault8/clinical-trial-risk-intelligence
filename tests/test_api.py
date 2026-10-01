from fastapi.testclient import TestClient
from clinical_trial_risk.api.app import app

def test_dashboard_and_health_do_not_require_credentials():
    with TestClient(app) as client:
        assert client.get('/').status_code==200
        assert client.get('/health').json()['scope']=='local retrospective research'
        assert client.get('/trials/invalid/report').status_code==422
        assert client.get('/portfolio?limit=0').status_code==422
        assert client.get('/monitoring').json()['stored_request_bodies'] is False
