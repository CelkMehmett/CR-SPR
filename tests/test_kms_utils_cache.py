import time
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core import kms_utils


def test_get_cached_public_key(monkeypatch):
    calls = []

    def fake_kms_get_public_key(key_id, region='us-east-1', role_arn=None):
        calls.append((key_id, region, role_arn))
        return (b'FAKE-PEM', 'RSA')

    monkeypatch.setattr(kms_utils, 'kms_get_public_key', fake_kms_get_public_key)

    # ensure fresh cache
    os.environ['KMS_PUBKEY_CACHE_TTL'] = '1'
    # recreate cache with short ttl
    kms_utils._PK_CACHE = kms_utils._PublicKeyCache(maxsize=16, ttl=1)

    # first call should hit underlying
    pk1 = kms_utils.get_cached_public_key('key1')
    assert pk1[0] == b'FAKE-PEM'
    assert len(calls) == 1

    # second call should be cached
    pk2 = kms_utils.get_cached_public_key('key1')
    assert pk2[0] == b'FAKE-PEM'
    assert len(calls) == 1

    # wait for ttl expiry
    time.sleep(1.1)
    pk3 = kms_utils.get_cached_public_key('key1')
    assert len(calls) == 2

    # different key triggers another call
    pk4 = kms_utils.get_cached_public_key('key2')
    assert len(calls) == 3
