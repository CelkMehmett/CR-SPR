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


def test_signature_rotation(monkeypatch):
    ml = MerkleLedger()
    ml.append({'a': 1})
    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    # record an initial signature
    r = client.post('/api/ledger/signature', headers=HEADERS, json={'key_id': 'k_old', 'method': 'hmac', 'signature_hex': 'oldsig', 'metadata': {}})
    assert r.status_code == 200

    # monkeypatch _kms_sign_root to return a new signature
    def fake_kms_sign(key_id=None):
        return 'newsig'

    monkeypatch.setattr('core.api_server._kms_sign_root', fake_kms_sign)

    # rotate using new key id
    r2 = client.post('/api/ledger/rotate_signature', headers=HEADERS, json={'new_key_id': 'k_new', 'method': 'kms'})
    assert r2.status_code == 200
    data = r2.json()
    assert data['new']['signature'] == 'newsig' or data['new']['signature'] == 'newsig'
    assert data['old']['signature'] == 'oldsig'
