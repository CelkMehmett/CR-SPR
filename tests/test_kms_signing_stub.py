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


def test_kms_sign_verify_monkeypatch(monkeypatch):
    # prepare ledger
    ml = MerkleLedger()
    ml.append({'a': 1})
    ml.append({'b': 2})
    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    root = (autolab.ledger if autolab else ledger_fallback).root()

    # monkeypatch the internal helper
    def fake_sign(key_id=None):
        return 'deadbeef'

    def fake_verify(root_hex, signature_hex, key_id=None):
        return signature_hex == 'deadbeef' and root_hex == root

    monkeypatch.setattr('core.api_server._kms_sign_root', fake_sign)
    monkeypatch.setattr('core.api_server._kms_verify_root', fake_verify)

    r = client.post('/api/ledger/sign_kms', headers=HEADERS, json={})
    assert r.status_code == 200
    assert r.json().get('signature') == 'deadbeef'

    r2 = client.post('/api/ledger/verify_kms', headers=HEADERS, json={'root_hex': root, 'signature_hex': 'deadbeef'})
    assert r2.status_code == 200
    assert r2.json().get('valid') is True

    r3 = client.post('/api/ledger/verify_kms', headers=HEADERS, json={'root_hex': root, 'signature_hex': 'cafebabe'})
    assert r3.status_code == 200
    assert r3.json().get('valid') is False
