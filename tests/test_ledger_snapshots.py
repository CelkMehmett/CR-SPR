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


def test_snapshot_save_list_load_delete_export(tmp_path):
    ml = MerkleLedger()
    ml.append({'x': 1})
    ml.append({'y': 2})

    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    # save snapshot
    r = client.post('/api/ledger/snapshot/testsnap', headers=HEADERS)
    assert r.status_code == 200

    # list
    r2 = client.get('/api/ledger/snapshots', headers=HEADERS)
    assert r2.status_code == 200
    snaps = r2.json().get('snapshots', [])
    assert any(s['name'] == 'testsnap' for s in snaps)

    # export
    r3 = client.get('/api/ledger/snapshot/export/testsnap', headers=HEADERS)
    assert r3.status_code == 200
    # load back into new ledger via upload endpoint
    # save response content to file and upload
    fpath = tmp_path / 'snap.json'
    fpath.write_bytes(r3.content)
    with open(fpath, 'rb') as f:
        r4 = client.post('/api/ledger/upload', headers=HEADERS, files={'file': ('snap.json', f, 'application/json')})
    assert r4.status_code == 200

    # delete
    r5 = client.delete('/api/ledger/snapshot/testsnap', headers=HEADERS)
    assert r5.status_code == 200

    # load deleted -> should 404
    r6 = client.post('/api/ledger/snapshot/load/testsnap', headers=HEADERS)
    assert r6.status_code == 404
