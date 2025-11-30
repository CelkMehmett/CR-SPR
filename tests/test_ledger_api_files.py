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


def test_upload_download_and_verify(tmp_path):
    # build ledger and attach
    ledger = MerkleLedger()
    ledger.append({'x': 1})
    ledger.append({'y': 2})

    # attach to fallback for the test
    if autolab is None:
        ledger_fallback.leaves = ledger.leaves.copy()
    else:
        autolab.ledger.leaves = ledger.leaves.copy()

    # download snapshot
    r = client.get('/api/ledger/download', headers=HEADERS)
    assert r.status_code == 200
    # save file
    p = tmp_path / 'dl.json'
    p.write_bytes(r.content)

    # upload back
    with open(p, 'rb') as f:
        r2 = client.post('/api/ledger/upload', headers=HEADERS, files={'file': ('snapshot.json', f, 'application/json')})
    assert r2.status_code == 200
    assert r2.json().get('count') == 2

    # get export to verify content
    r3 = client.get('/api/ledger/export', headers=HEADERS)
    assert r3.status_code == 200
    data = r3.json()
    leaves = data.get('leaves')
    assert isinstance(leaves, list) and len(leaves) >= 2

    # build a proof for leaf 0 and verify via API
    # use MerkleLedger locally to create proof
    ml = MerkleLedger()
    ml.leaves = [bytes.fromhex(h) for h in leaves]
    proof = ml.inclusion_proof(0)
    leaf_hex = leaves[0]
    root = ml.root()

    payload = {'leaf_hex': leaf_hex, 'proof': proof, 'root_hex': root}
    r4 = client.post('/api/ledger/verify_proof', headers=HEADERS, json=payload)
    assert r4.status_code == 200
    assert r4.json().get('valid') is True
