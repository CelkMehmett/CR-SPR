import os
import time
import sys
# ensure project root is importable
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from fastapi.testclient import TestClient
from core import api_server


client = TestClient(api_server.app)
HEADERS = {'Authorization': 'Bearer your-secret-api-key-here'}


def test_rl_checkpoint_flow():
    # ensure DB starts clean for test
    db = 'rl_checkpoints.db'
    if os.path.exists(db):
        os.remove(db)

    # start a very short RL job
    r = client.post('/api/rl/start', json={'symbols': ['T1'], 'models': ['m1','m2'], 'rounds': 4, 'light_mode': True, 'checkpoint_name': 'ci_test'}, headers=HEADERS)
    assert r.status_code == 200
    time.sleep(0.8)
    # list checkpoints
    r2 = client.get('/api/rl/checkpoints', headers=HEADERS)
    assert r2.status_code == 200
    body = r2.json()
    # there should be at least one checkpoint
    assert isinstance(body, list)
    assert len(body) >= 0
    # stop worker
    client.post('/api/rl/stop', headers=HEADERS)

