import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from core.api_server import app

client = TestClient(app)


def test_metrics_endpoint_with_prometheus(monkeypatch):
    # simulate prometheus_client.generate_latest
    class Dummy:
        CONTENT_TYPE_LATEST = 'text/plain; version=0.0.4'

        @staticmethod
        def generate_latest():
            return b"metric_a 1\n"

    monkeypatch.setitem(sys.modules, 'prometheus_client', Dummy)
    r = client.get('/metrics')
    assert r.status_code == 200
    assert b"metric_a" in r.content


def test_metrics_endpoint_without_prometheus(monkeypatch):
    # ensure prometheus_client import fails
    if 'prometheus_client' in sys.modules:
        del sys.modules['prometheus_client']
    # create a dummy module that raises on attribute access
    class Broken:
        def __getattr__(self, name):
            raise ImportError()

    monkeypatch.setitem(sys.modules, 'prometheus_client', Broken)
    r = client.get('/metrics')
    assert r.status_code == 204
