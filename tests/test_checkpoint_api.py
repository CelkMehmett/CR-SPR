import os
import time
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from fastapi.testclient import TestClient
from core import api_server

client = TestClient(api_server.app)
HEADERS = {'Authorization': 'Bearer your-secret-api-key-here'}


def test_export_import_checkpoint():
    # ensure a checkpoint exists by starting a short job
    db = 'rl_checkpoints.db'
    if os.path.exists(db):
        os.remove(db)

    r = client.post('/api/rl/start', json={'symbols': ['X'], 'models': ['m1'], 'rounds': 2, 'light_mode': True, 'checkpoint_name': 'exp1'}, headers=HEADERS)
    assert r.status_code == 200
    time.sleep(0.6)

    # export
    r2 = client.get('/api/rl/export_checkpoint/exp1', headers=HEADERS)
    assert r2.status_code == 200
    payload = r2.json()
    assert payload['name'] == 'exp1'
    blob_hex = payload['blob']

    # import under a new name
    r3 = client.post('/api/rl/import_checkpoint', json={'name': 'exp1_copy', 'blob_hex': blob_hex}, headers=HEADERS)
    assert r3.status_code == 200

    # list checkpoints should contain both
    r4 = client.get('/api/rl/checkpoints', headers=HEADERS)
    names = [p['name'] for p in r4.json()]
    assert 'exp1' in names
    assert 'exp1_copy' in names
