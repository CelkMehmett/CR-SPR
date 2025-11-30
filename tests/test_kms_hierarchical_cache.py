import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core import kms_utils


def test_disk_cache_read_through(monkeypatch, tmp_path):
    # enable disk cache and create a cache dir
    os.environ['KMS_PUBKEY_USE_DISK'] = 'true'
    os.environ['KMS_PUBKEY_DISK_DIR'] = str(tmp_path / 'diskc')

    # reload module components that read env at import time
    monkeypatch.setenv('KMS_PUBKEY_USE_DISK', 'true')

    # create disk cache and write an entry
    dc = kms_utils.DiskCache(str(tmp_path / 'diskc'))
    key = 'us-east-1:mykey:'
    dc.set(key, b'PEM-DISK', ttl_seconds=60)

    called = {'n': 0}

    def fake_kms_get_public_key(key_id, region='us-east-1', role_arn=None):
        called['n'] += 1
        return (b'SHOULD-NOT', 'RSA')

    monkeypatch.setattr(kms_utils, 'kms_get_public_key', fake_kms_get_public_key)

    # clear in-memory cache and set module disk cache
    kms_utils._PK_CACHE = kms_utils._PublicKeyCache(maxsize=8, ttl=60)
    kms_utils._DISK_CACHE = dc

    val = kms_utils.get_cached_public_key('mykey')
    assert val[0] == b'PEM-DISK'
    assert called['n'] == 0

    # cleanup
    del os.environ['KMS_PUBKEY_USE_DISK']
    del os.environ['KMS_PUBKEY_DISK_DIR']
