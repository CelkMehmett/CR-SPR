import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core import kms_utils


class SimpleCounter:
    def __init__(self):
        self.n = 0

    def inc(self, amount=1):
        self.n += amount


def test_metrics_increment_on_cache_and_attempts(monkeypatch):
    # replace real counters with simple counters
    ch = SimpleCounter()
    cm = SimpleCounter()
    ka = SimpleCounter()
    monkeypatch.setattr(kms_utils, 'cache_hits', ch)
    monkeypatch.setattr(kms_utils, 'cache_misses', cm)
    monkeypatch.setattr(kms_utils, 'kms_attempts', ka)

    # monkeypatch kms_get_public_key to a simple function
    calls = {'n': 0}

    def fake_kms_get_public_key(key_id, region='us-east-1', role_arn=None):
        calls['n'] += 1
        return (b'PEM', 'RSA')

    monkeypatch.setattr(kms_utils, 'kms_get_public_key', fake_kms_get_public_key)

    # reset cache
    kms_utils._PK_CACHE = kms_utils._PublicKeyCache(maxsize=8, ttl=60)

    # first call should miss and increment attempts
    kms_utils.get_cached_public_key('m1')
    assert cm.n == 1
    assert ka.n == 1

    # second call should hit
    kms_utils.get_cached_public_key('m1')
    assert ch.n == 1
    assert cm.n == 1
    assert ka.n == 1

    # different key -> miss and attempt
    kms_utils.get_cached_public_key('m2')
    assert cm.n == 2
    assert ka.n == 2

    # ensure underlying was called twice
    assert calls['n'] == 2
