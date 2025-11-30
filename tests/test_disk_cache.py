import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.disk_cache import DiskCache


def test_disk_cache_set_get(tmp_path):
    d = tmp_path / 'cache'
    d.mkdir()
    key = b'secret-key-1234567890-012345'
    c = DiskCache(str(d), key=key)
    c.set('k1', b'PAYLOAD', ttl_seconds=2)
    v = c.get('k1')
    assert v == b'PAYLOAD'
    time.sleep(2.1)
    assert c.get('k1') is None


def test_disk_cache_plaintext_fallback(tmp_path, monkeypatch):
    # force no cryptography by monkeypatching import to raise
    monkeypatch.setitem(sys.modules, 'cryptography', None)
    d = tmp_path / 'cache2'
    d.mkdir()
    c = DiskCache(str(d), key=b'k')
    c.set('k2', b'X', ttl_seconds=1)
    assert c.get('k2') == b'X'
    time.sleep(1.1)
    assert c.get('k2') is None
