import os
import sys
import binascii

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.merkle_ledger import MerkleLedger
from core.api_server import app, ledger_fallback, autolab
from fastapi.testclient import TestClient

client = TestClient(app)
API_KEY = "your-secret-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def test_signed_root_and_verify(tmp_path, monkeypatch):
    # set key
    key = b'secret-key-1234'
    os.environ['LEDGER_SIGN_KEY'] = binascii.hexlify(key).decode()

    ml = MerkleLedger()
    ml.append({'a': 1})
    ml.append({'b': 2})

    # attach to fallback
    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    r = client.get('/api/ledger/signed_root', headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    root = data.get('root')
    sig = data.get('signature')
    assert root is not None and sig is not None

    # verify via verify endpoint
    payload = {'root_hex': root, 'signature_hex': sig}
    r2 = client.post('/api/ledger/verify_root', headers=HEADERS, json=payload)
    assert r2.status_code == 200
    assert r2.json().get('valid') is True

    # tamper root
    bad = root[:-1] + ('0' if root[-1] != '0' else '1')
    payload2 = {'root_hex': bad, 'signature_hex': sig}
    r3 = client.post('/api/ledger/verify_root', headers=HEADERS, json=payload2)
    assert r3.status_code == 200
    assert r3.json().get('valid') is False

    # cleanup
    del os.environ['LEDGER_SIGN_KEY']
