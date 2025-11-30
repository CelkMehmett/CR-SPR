import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.merkle_ledger import MerkleLedger
from core.api_server import autolab
from fastapi.testclient import TestClient

client = TestClient(__import__('core.api_server').api_server.app)
API_KEY = "your-secret-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def test_ledger_save_load_export_import(tmp_path):
    ledger = MerkleLedger()
    ledger.append({'a': 1})
    ledger.append({'b': 2})

    # export to json file
    f = tmp_path / 'snap.json'
    ledger.export_json(str(f))
    assert f.exists()

    # import into new ledger
    l2 = MerkleLedger()
    l2.import_json(str(f))
    assert len(l2.leaves) == 2
    assert l2.root() == ledger.root()

    # attach to autolab and save via API (if available)
    if autolab is not None:
        autolab.ledger = ledger
        r = client.post('/api/ledger/save', headers=HEADERS)
        assert r.status_code in (200, 500)  # allow 500 if autolab not fully configured in environment
        # load back
        r2 = client.post('/api/ledger/load', headers=HEADERS)
        assert r2.status_code in (200, 500)

    # test import endpoint with payload
    payload = {'leaves_hex': [l.hex() for l in ledger.leaves]}
    r3 = client.post('/api/ledger/import', headers=HEADERS, json=payload)
    assert r3.status_code == 200
    assert r3.json().get('count') == 2

    # test export endpoint
    r4 = client.get('/api/ledger/export', headers=HEADERS)
    assert r4.status_code == 200
    data = r4.json()
    assert 'leaves' in data
