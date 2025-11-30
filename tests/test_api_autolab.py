import os
import sys
import time
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from core.api_server import app, autolab

client = TestClient(app)

API_KEY = "your-secret-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def test_autolab_availability_and_status():
    resp = client.get('/api/autolab/status', headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert 'available' in data


def test_autolab_step_requires_available():
    # If autolab is None, endpoint should return 500
    if autolab is None:
        resp = client.post('/api/autolab/step', headers=HEADERS)
        assert resp.status_code == 500
    else:
        resp = client.post('/api/autolab/step', headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'ok'


def test_autolab_start_stop():
    if autolab is None:
        # ensure endpoints report not available
        resp = client.post('/api/autolab/start', headers=HEADERS)
        assert resp.status_code == 500
        resp = client.post('/api/autolab/stop', headers=HEADERS)
        assert resp.status_code == 500
    else:
        # start
        resp = client.post('/api/autolab/start', headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()['status'] == 'running'
        # give it a small moment
        time.sleep(0.1)
        # status should say running
        resp = client.get('/api/autolab/status', headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data['available'] is True
        assert data['running'] is True
        # stop
        resp = client.post('/api/autolab/stop', headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()['status'] == 'stopped'
        # status should say not running
        resp = client.get('/api/autolab/status', headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data['running'] is False


def test_autolab_root_endpoint():
    if autolab is None:
        resp = client.get('/api/autolab/root', headers=HEADERS)
        assert resp.status_code == 500
    else:
        resp = client.get('/api/autolab/root', headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert 'root' in data
