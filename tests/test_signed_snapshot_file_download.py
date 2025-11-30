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


def test_signed_snapshot_file_download(monkeypatch, tmp_path):
    ml = MerkleLedger()
    ml.append({'a': 1})
    ml.append({'b': 2})

    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    # save snapshot
    r = client.post('/api/ledger/snapshot/file1', headers=HEADERS)
    assert r.status_code == 200

    # add signature record
    r2 = client.post('/api/ledger/signature', headers=HEADERS, json={'key_id': 'k_snap', 'method': 'kms', 'signature_hex': 'snapfile', 'metadata': {'snapshot': 'file1'}})
    assert r2.status_code == 200

    # monkeypatch kms_get_public_key
    def fake_get_public_key(key_id, region='us-east-1', role_arn=None):
        return (b'-----BEGIN PUBLIC KEY-----\nFAKE\n-----END PUBLIC KEY-----\n', 'RSA')

    monkeypatch.setattr('core.kms_utils.kms_get_public_key', fake_get_public_key)
    os.environ['LEDGER_KMS_KEY_ID'] = 'k_snap'

    r3 = client.get('/api/ledger/snapshot/export_signed_file/file1', headers=HEADERS)
    assert r3.status_code == 200
    # save file
    p = tmp_path / 'bundle.json'
    p.write_bytes(r3.content)
    data = r3.json()
    assert data['signature']['signature'] == 'snapfile'

    del os.environ['LEDGER_KMS_KEY_ID']
