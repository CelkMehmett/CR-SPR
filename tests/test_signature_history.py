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


def test_signature_record_list_get():
    ml = MerkleLedger()
    ml.append({'k': 1})
    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    # record signature
    r = client.post('/api/ledger/signature', headers=HEADERS, json={'key_id': 'k1', 'method': 'hmac', 'signature_hex': 'abcd', 'metadata': {'ver': 1}})
    assert r.status_code == 200

    # list
    r2 = client.get('/api/ledger/signatures', headers=HEADERS)
    assert r2.status_code == 200
    sigs = r2.json().get('signatures', [])
    assert len(sigs) >= 1
    first = sigs[0]
    assert 'id' in first

    # get
    sig_id = first['id']
    r3 = client.get(f'/api/ledger/signature/{sig_id}', headers=HEADERS)
    assert r3.status_code == 200
    obj = r3.json()
    assert obj['signature'] in ('abcd', 'abcd') or obj['signature'] == 'abcd'

    # cleanup not necessary
