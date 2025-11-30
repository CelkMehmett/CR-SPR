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


def test_signed_snapshot_bundle(monkeypatch):
    ml = MerkleLedger()
    ml.append({'a': 1})
    ml.append({'b': 2})

    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    # save snapshot
    r = client.post('/api/ledger/snapshot/bundle1', headers=HEADERS)
    assert r.status_code == 200

    # monkeypatch signature present
    # record signature with metadata snapshot
    r2 = client.post('/api/ledger/signature', headers=HEADERS, json={'key_id': 'k_snap', 'method': 'kms', 'signature_hex': 'snapbundle', 'metadata': {'snapshot': 'bundle1'}})
    assert r2.status_code == 200

    # monkeypatch kms_get_public_key
    def fake_get_public_key(key_id, region='us-east-1', role_arn=None):
        return (b'-----BEGIN PUBLIC KEY-----\nFAKE\n-----END PUBLIC KEY-----\n', 'RSA')

    monkeypatch.setattr('core.kms_utils.kms_get_public_key', fake_get_public_key)
    os.environ['LEDGER_KMS_KEY_ID'] = 'k_snap'

    r3 = client.get('/api/ledger/snapshot/export_signed/bundle1', headers=HEADERS)
    assert r3.status_code == 200
    data = r3.json()
    assert 'snapshot' in data and 'signature' in data
    assert data['signature']['signature'] == 'snapbundle'
    assert data['public_key_pem_b64'] is not None

    del os.environ['LEDGER_KMS_KEY_ID']
