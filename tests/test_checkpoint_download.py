import os
import sys
import time

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from fastapi.testclient import TestClient
from core import api_server

client = TestClient(api_server.app)
HEADERS = {'Authorization': 'Bearer your-secret-api-key-here'}


def test_download_checkpoint():
    # ensure a checkpoint exists
    r = client.post('/api/rl/start', json={'symbols': ['D1'], 'models': ['m1'], 'rounds': 2, 'light_mode': True, 'checkpoint_name': 'dl1'}, headers=HEADERS)
    assert r.status_code == 200
    time.sleep(0.6)

    r2 = client.get('/api/rl/download_checkpoint/dl1', headers=HEADERS)
    assert r2.status_code == 200
    content = r2.content
    assert isinstance(content, (bytes, bytearray))
