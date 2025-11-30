import time
import json

try:
    import requests
except Exception:
    requests = None


def http_post(path, data=None):
    url = f'http://127.0.0.1:8008{path}'
    if requests:
        return requests.post(url, json=data, timeout=5)
    import urllib.request
    req = urllib.request.Request(url, data=(json.dumps(data) if data is not None else None).encode('utf-8') if data is not None else None, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        class R:
            status_code = resp.getcode()
            text = resp.read().decode('utf-8')
        return R()


def http_get(path):
    url = f'http://127.0.0.1:8008{path}'
    if requests:
        return requests.get(url, timeout=5)
    import urllib.request
    with urllib.request.urlopen(url, timeout=5) as resp:
        class R:
            status_code = resp.getcode()
            text = resp.read().decode('utf-8')
        return R()


def test_run_real_batch_creates_snapshot():
    # POST to start a demo real batch
    r = http_post('/run_real_batch', data={})
    assert r.status_code in (200, 202, 204)

    # Poll /snapshots until a snapshot is visible or timeout
    deadline = time.time() + 10.0
    snaps = None
    while time.time() < deadline:
        try:
            r2 = http_get('/snapshots')
            if r2.status_code == 200:
                data = json.loads(r2.text)
                snaps = data.get('snapshots')
                if snaps:
                    break
        except Exception:
            pass
        time.sleep(0.5)

    assert snaps and len(snaps) > 0, 'No snapshots created within timeout'

    # Fetch the first snapshot by id and validate structure
    sid = snaps[0]['id']
    r3 = http_get(f'/snapshots/{sid}')
    assert r3.status_code == 200
    snap = json.loads(r3.text)
    assert 'chromosomes' in snap
    assert 'metadata' in snap

