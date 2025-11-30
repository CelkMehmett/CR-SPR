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


def test_kms_attempts_increments_on_retries(monkeypatch):
    calls = {'n': 0}

    def flaky_kms_get_public_key(key_id, region='us-east-1', role_arn=None):
        calls['n'] += 1
        if calls['n'] < 3:
            raise RuntimeError('transient')
        return (b'OK', 'RSA')

    monkeypatch.setattr(kms_utils, 'kms_get_public_key', flaky_kms_get_public_key)

    c = SimpleCounter()
    monkeypatch.setattr(kms_utils, 'kms_attempts', c)

    # reset cache so we actually call
    kms_utils._PK_CACHE = kms_utils._PublicKeyCache(maxsize=8, ttl=60)

    res = kms_utils.get_cached_public_key('retry-key')
    assert res[0] == b'OK'
    # retries: 3 attempts -> counter should be at least 3
    assert c.n >= 3
