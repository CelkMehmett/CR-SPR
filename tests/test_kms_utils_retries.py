import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core import kms_utils


def test_get_cached_public_key_retries(monkeypatch):
    calls = {'n': 0}

    def flaky_kms_get_public_key(key_id, region='us-east-1', role_arn=None):
        calls['n'] += 1
        if calls['n'] < 3:
            raise RuntimeError('transient')
        return (b'OK-PEM', 'RSA')

    monkeypatch.setattr(kms_utils, 'kms_get_public_key', flaky_kms_get_public_key)

    # ensure fresh cache
    kms_utils._PK_CACHE = kms_utils._PublicKeyCache(maxsize=8, ttl=60)
    # reset higher-level caches to avoid cross-test contamination
    kms_utils._CACHE_ADAPTER = kms_utils._CACHE_ADAPTER.__class__(None)
    kms_utils._DISK_CACHE = None

    pk = kms_utils.get_cached_public_key('retry-key')
    assert pk[0] == b'OK-PEM'
    assert calls['n'] >= 3
