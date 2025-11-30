import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.merkle_ledger import MerkleLedger
from core.api_server import app, ledger_fallback, autolab
from fastapi.testclient import TestClient

client = TestClient(app)
API_KEY = "your-secret-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def test_proof_and_verify_roundtrip():
    ml = MerkleLedger()
    ml.append({'a': 1})
    ml.append({'b': 2})
    # attach
    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    # request proof for index 1
    r = client.get('/api/ledger/proof/1', headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data['index'] == 1
    leaf_hex = data['leaf_hex']
    proof = data['proof']
    root = data['root']

    # verify via verify_proof endpoint
    payload = {'leaf_hex': leaf_hex, 'proof': proof, 'root_hex': root}
    r2 = client.post('/api/ledger/verify_proof', headers=HEADERS, json=payload)
    assert r2.status_code == 200
    assert r2.json().get('valid') is True
