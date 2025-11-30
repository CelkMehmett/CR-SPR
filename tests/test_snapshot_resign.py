import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from core.api_server import app, autolab, ledger_fallback
from core.merkle_ledger import MerkleLedger

client = TestClient(app)
API_KEY = "your-secret-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def test_resign_snapshot(monkeypatch, tmp_path):
    ml = MerkleLedger()
    ml.append({'a': 1})
    ml.append({'b': 2})

    # attach and save snapshot
    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    r = client.post('/api/ledger/snapshot/testsnap2', headers=HEADERS)
    assert r.status_code == 200

    # monkeypatch kms sign helper
    def fake_kms_sign(key_id=None):
        return 'snapnewsig'

    monkeypatch.setattr('core.api_server._kms_sign_root', fake_kms_sign)

    r2 = client.post('/api/ledger/snapshot/rotate/testsnap2', headers=HEADERS, json={'new_key_id': 'k_snap', 'method': 'kms'})
    assert r2.status_code == 200
    data = r2.json()
    assert data['snapshot'] == 'testsnap2'
    assert data['signature']['signature'] == 'snapnewsig'
