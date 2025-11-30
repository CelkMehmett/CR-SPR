#!/usr/bin/env python3
"""Re-encrypt all files in a DiskCache directory with a new key.

This script reads each JSON cache file, decrypts it using the "old" key
and re-encrypts it with the "new" key. It preserves the `expires` field.

Key resolution for old/new: same as DiskCache - you may pass --key-file or
--ssm-path or --kms-ciphertext-b64 or rely on env vars. For convenience this
function accepts explicit plaintext key files via --old-key-file/--new-key-file.

Usage (simple):
  scripts/rekey_disk_cache.py --cache-dir ./.kms_cache --old-key-file old.key --new-key-file new.key

Note: this tool requires `cryptography` to be installed.
"""
import argparse
import base64
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional


def _resolve_via_diskcache_helper(key_file: Optional[str], ssm_path: Optional[str], kms_cipher_b64: Optional[str], role_arn: Optional[str]):
    # Import DiskCache locally to reuse its key resolution behavior
    try:
        from core.disk_cache import DiskCache
    except Exception:
        DiskCache = None
    if key_file:
        with open(key_file, 'rb') as f:
            return f.read()
    # fallback: instantiate a DiskCache just to resolve key (it needs a directory)
    if DiskCache is not None:
        td = tempfile.mkdtemp(prefix='diskcache-key-resolve-')
        try:
            dc = DiskCache(td, key=None, ssm_path=ssm_path, kms_ciphertext_b64=kms_cipher_b64, role_arn=role_arn)
            return dc.key
        finally:
            try:
                shutil.rmtree(td)
            except Exception:
                pass
    raise RuntimeError('Cannot resolve key: provide --key-file or ensure DiskCache and boto3 are available')


def rekey_cache(cache_dir: str, old_key_file: Optional[str] = None, new_key_file: Optional[str] = None, old_ssm: Optional[str] = None, new_ssm: Optional[str] = None, old_kms_ct: Optional[str] = None, new_kms_ct: Optional[str] = None, old_role_arn: Optional[str] = None, new_role_arn: Optional[str] = None, backup_dir: Optional[str] = None) -> int:
    """Re-encrypt all .json files in cache_dir. Returns number of files processed."""
    # resolve keys to raw bytes (final derived key is computed inside DiskCache when available)
    old_key = _resolve_via_diskcache_helper(old_key_file, old_ssm, old_kms_ct, old_role_arn)
    new_key = _resolve_via_diskcache_helper(new_key_file, new_ssm, new_kms_ct, new_role_arn)

    # require cryptography
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as e:
        raise RuntimeError('cryptography is required to rekey disk cache') from e

    # depending on DiskCache derivation, keys may need hashing to 32 bytes; mirror DiskCache behavior
    import hashlib

    def _normalize_key(k: bytes) -> bytes:
        if k is None:
            return None
        if len(k) in (16, 24, 32):
            return k
        return hashlib.sha256(k or b'').digest()

    old_k = _normalize_key(old_key)
    new_k = _normalize_key(new_key)

    cache_p = Path(cache_dir)
    if not cache_p.exists() or not cache_p.is_dir():
        raise RuntimeError(f'cache dir not found: {cache_dir}')

    if backup_dir:
        backup_p = Path(backup_dir)
        backup_p.mkdir(parents=True, exist_ok=True)

    processed = 0
    for f in cache_p.iterdir():
        if not f.is_file() or not f.name.endswith('.json'):
            continue
        # read payload
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        expires = data.get('expires')
        # decrypt
        if 'ct' in data and 'nonce' in data:
            try:
                aes_old = AESGCM(old_k)
                nonce = base64.b64decode(data['nonce'])
                ct = base64.b64decode(data['ct'])
                pt = aes_old.decrypt(nonce, ct, None)
            except Exception:
                # skip files we can't decrypt with old key
                continue
        elif 'plain' in data:
            pt = base64.b64decode(data['plain'])
        else:
            continue
        # backup original
        if backup_dir:
            shutil.copy2(f, Path(backup_dir) / f.name)
        else:
            # write a .bak next to file
            try:
                shutil.copy2(f, f.with_suffix('.json.bak'))
            except Exception:
                pass
        # encrypt with new key
        aes_new = AESGCM(new_k)
        nonce_new = os.urandom(12)
        ct_new = aes_new.encrypt(nonce_new, pt, None)
        payload = {'expires': expires, 'nonce': base64.b64encode(nonce_new).decode(), 'ct': base64.b64encode(ct_new).decode()}
        # atomic write
        tmpf = f.with_suffix('.json.tmp')
        tmpf.write_text(json.dumps(payload))
        tmpf.replace(f)
        processed += 1
    return processed


def main(argv=None):
    p = argparse.ArgumentParser(description='Re-encrypt DiskCache directory with a new key')
    p.add_argument('--cache-dir', required=True)
    p.add_argument('--old-key-file')
    p.add_argument('--new-key-file')
    p.add_argument('--old-ssm')
    p.add_argument('--new-ssm')
    p.add_argument('--old-kms-ct')
    p.add_argument('--new-kms-ct')
    p.add_argument('--old-role-arn')
    p.add_argument('--new-role-arn')
    p.add_argument('--backup-dir')
    args = p.parse_args(argv)
    n = rekey_cache(args.cache_dir, old_key_file=args.old_key_file, new_key_file=args.new_key_file, old_ssm=args.old_ssm, new_ssm=args.new_ssm, old_kms_ct=args.old_kms_ct, new_kms_ct=args.new_kms_ct, old_role_arn=args.old_role_arn, new_role_arn=args.new_role_arn, backup_dir=args.backup_dir)
    print(f'Processed {n} files')


if __name__ == '__main__':
    main()
