import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.redis_cache import RedisCache


def test_redis_cache_fallback_and_set_get(monkeypatch):
    # Force no REDIS_URL so fallback is used
    if 'KMS_PUBKEY_REDIS_URL' in os.environ:
        del os.environ['KMS_PUBKEY_REDIS_URL']
    rc = RedisCache(url=None)
    rc.set('k1', b'VALUE', ttl_seconds=1)
    v = rc.get('k1')
    assert v == b'VALUE'
    time.sleep(1.1)
    assert rc.get('k1') is None


def test_redis_cache_with_fakeredis(monkeypatch):
    try:
        import fakeredis
    except Exception:
        # fakeredis not available in environment; skip
        return
    # create a fake redis server and patch redis.from_url
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server)

    def fake_from_url(url):
        return client

    monkeypatch.setattr('redis.from_url', fake_from_url)
    rc = RedisCache(url='redis://localhost:6379/0')
    rc.set('k2', b'BYTES', ttl_seconds=1)
    v = rc.get('k2')
    assert v == b'BYTES'
    time.sleep(1.1)
    assert rc.get('k2') is None
