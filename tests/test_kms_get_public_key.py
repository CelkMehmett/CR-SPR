import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from core.api_server import app

client = TestClient(app)
API_KEY = "your-secret-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def test_kms_public_key_monkeypatched(monkeypatch):
    # monkeypatch kms_get_public_key to return a fake PEM
    def fake_get_public_key(key_id, region='us-east-1', role_arn=None):
        return (b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq...\n-----END PUBLIC KEY-----\n', 'RSA')

    monkeypatch.setattr('core.api_server.kms_get_public_key' if hasattr(__import__('core.api_server'), 'kms_get_public_key') else 'core.kms_utils.kms_get_public_key', fake_get_public_key)

    # set env var
    os.environ['LEDGER_KMS_KEY_ID'] = 'fake-key-id'

    r = client.get('/api/ledger/kms_public_key', headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert 'public_key_pem_b64' in data
    assert data['algorithm'] == 'RSA'

    del os.environ['LEDGER_KMS_KEY_ID']
