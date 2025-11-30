import os
import json
import base64

from pathlib import Path

import pytest

from scripts.rekey_disk_cache import rekey_cache

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception:
    AESGCM = None


def _write_encrypted_file(dirp: Path, name: str, key: bytes, plaintext: bytes, expires=None):
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext, None)
    payload = {'expires': expires, 'nonce': base64.b64encode(nonce).decode(), 'ct': base64.b64encode(ct).decode()}
    (dirp / (name + '.json')).write_text(json.dumps(payload))


def _read_encrypted_file(dirp: Path, name: str, key: bytes):
    p = dirp / (name + '.json')
    data = json.loads(p.read_text())
    nonce = base64.b64decode(data['nonce'])
    ct = base64.b64decode(data['ct'])
    aes = AESGCM(key)
    return aes.decrypt(nonce, ct, None)


@pytest.mark.skipif(AESGCM is None, reason='cryptography not installed')
def test_rekey_happy_path(tmp_path):
    # prepare old and new keys (raw)
    old_key = b'oldsecret'
    new_key = b'newsecret'

    # normalize like DiskCache does
    import hashlib
    old_k = hashlib.sha256(old_key).digest()
    new_k = hashlib.sha256(new_key).digest()

    cache_dir = tmp_path / 'cache'
    cache_dir.mkdir()

    # create two sample files
    _write_encrypted_file(cache_dir, 'a', old_k, b'hello')
    _write_encrypted_file(cache_dir, 'b', old_k, b'world')

    # write key files
    oldkf = tmp_path / 'old.key'
    newkf = tmp_path / 'new.key'
    oldkf.write_bytes(old_key)
    newkf.write_bytes(new_key)

    n = rekey_cache(str(cache_dir), old_key_file=str(oldkf), new_key_file=str(newkf))
    assert n == 2

    # ensure files decrypt with new key
    assert _read_encrypted_file(cache_dir, 'a', new_k) == b'hello'
    assert _read_encrypted_file(cache_dir, 'b', new_k) == b'world'

