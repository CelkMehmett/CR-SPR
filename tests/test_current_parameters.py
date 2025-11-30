import json

try:
    import requests
except Exception:
    requests = None


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


def test_current_parameters_endpoint():
    # GET current parameters
    r = http_get('/current_parameters')
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = json.loads(r.text)
        assert 'parameters' in data
        assert isinstance(data['parameters'], dict)
