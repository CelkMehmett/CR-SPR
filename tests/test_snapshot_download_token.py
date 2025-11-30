import os
import json


def test_snapshot_download_requires_token(tmp_path, monkeypatch):
    # Set DEMO_TOKEN before importing the server module so it picks it up
    monkeypatch.setenv('DEMO_TOKEN', 'testtoken')

    # Import server after setting env var
    from poc.presentation_v2 import server

    client = server.app.test_client()

    # Ensure snapshot dir exists
    sd = server.SNAPSHOT_DIR
    os.makedirs(sd, exist_ok=True)

    # Create a small snapshot file
    fname = '20251029T000000_test_snapshot.json'
    path = os.path.join(sd, fname)
    snapshot = {
        'name': 'test_snapshot',
        'snapshot_time': '2025-10-29T00:00:00',
        'metadata': {'edit_history': []}
    }
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(snapshot, fh)

    sid = server._snapshot_id_from_filename(path)

    # Attempt download without token -> should be 401
    r = client.get(f'/snapshots/{sid}/download')
    assert r.status_code == 401, f"expected 401 when no token provided, got {r.status_code}"

    # Attempt with wrong token -> 401
    r = client.get(f'/snapshots/{sid}/download', headers={'X-DEMO-TOKEN': 'wrong'})
    assert r.status_code == 401

    # Attempt with correct token -> 200 and content matches file
    r = client.get(f'/snapshots/{sid}/download', headers={'X-DEMO-TOKEN': 'testtoken'})
    assert r.status_code == 200
    # response is streamed; ensure the content includes the snapshot name
    body = b''.join(r.response) if r.response is not None else r.data
    assert b'test_snapshot' in body

    # Cleanup
    try:
        os.remove(path)
    except Exception:
        pass
