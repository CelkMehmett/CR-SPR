"""On-disk encrypted cache for small binary blobs (e.g., PEM/DER bytes).

API:
- DiskCache(directory, key) -> cache instance
- get(key) -> bytes or None
- set(key, value, ttl_seconds)

Storage layout: <dir>/<safe_key>.json containing {expires: ts or null, nonce: b64, ciphertext: b64}
Encryption: AES-GCM with 32-byte key from env or provided value.
If `cryptography` is not available, falls back to plaintext storage (not recommended for prod).
"""
import os
import json
import base64
import tempfile
import time
from typing import Optional
from pathlib import Path


def _safe_name(key: str) -> str:
    # simple safe filename
    import hashlib

    h = hashlib.sha256(key.encode()).hexdigest()
    return h


class DiskCache:
    def __init__(self, directory: str, key: Optional[bytes] = None, *,
                 ssm_path: Optional[str] = None,
                 kms_ciphertext_b64: Optional[str] = None,
                 role_arn: Optional[str] = None,
                 allow_plaintext: Optional[bool] = None):
        """Create a DiskCache.

        Key resolution order:
        1. explicit `key` argument
        2. env var `DISK_CACHE_KEY`
        3. env var or param `ssm_path` -> fetch from SSM Parameter Store
        4. env var or param `kms_ciphertext_b64` -> decrypt via KMS

        If boto3 is not available or AWS calls fail, an exception is raised explaining the problem.
        """
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

        # raw key bytes or None
        resolved = key
        if resolved is None:
            ev = os.environ.get('DISK_CACHE_KEY')
            if ev:
                resolved = ev.encode()

        # allow passing SSM path or KMS ciphertext via ctor or env
        ssm_path = ssm_path or os.environ.get('DISK_CACHE_KEY_SSM_PATH')
        kms_ciphertext_b64 = kms_ciphertext_b64 or os.environ.get('DISK_CACHE_KEY_KMS_CIPHERTEXT')
        # allow passing an AWS role ARN to assume when calling SSM/KMS
        self._role_arn = role_arn or os.environ.get('DISK_CACHE_KEY_ROLE_ARN')

        # allow plaintext fallback toggle: can be passed or read from env
        if allow_plaintext is None:
            raw = os.environ.get('DISK_CACHE_ALLOW_PLAINTEXT', 'true').lower()
            allow_plaintext = raw in ('1', 'true', 'yes')
        self._allow_plaintext = bool(allow_plaintext)

        if resolved is None and ssm_path:
            resolved = self._fetch_ssm_parameter(ssm_path)

        if resolved is None and kms_ciphertext_b64:
            resolved = self._decrypt_kms_ciphertext(kms_ciphertext_b64)

        self.key = resolved
        if isinstance(self.key, str):
            self.key = self.key.encode()

        # if cryptography available, use AESGCM
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
            self._have_crypto = True
            self._AESGCM = AESGCM
            if not self.key or len(self.key) not in (16, 24, 32):
                # derive 32-byte key from provided secret
                import hashlib

                self.key = hashlib.sha256(self.key or b'').digest()
        except Exception:
            self._have_crypto = False
            if not self._allow_plaintext:
                raise RuntimeError('cryptography not available and plaintext fallback disabled (DISK_CACHE_ALLOW_PLAINTEXT=false)')

    def _fetch_ssm_parameter(self, path: str) -> Optional[bytes]:
        """Fetch a SecureString or String parameter from SSM.

        Returns the raw bytes of the parameter value. Raises RuntimeError with
        actionable message if boto3 is not available or the call fails.
        """
        try:
            import boto3
            from botocore.config import Config
        except Exception as e:
            raise RuntimeError("boto3 is required to fetch DISK_CACHE_KEY from SSM but it's not installed") from e

        try:
            # prefer using the project's assume-role helper if available so callers
            # can pass a role ARN and we use that session (reduces duplicated STS code)
            try:
                from core.kms_utils import _assume_role_session  # type: ignore
            except Exception:
                _assume_role_session = None

            if _assume_role_session and self._role_arn:
                session = _assume_role_session(self._role_arn)
                ssm = session.client('ssm', config=Config(retries={'max_attempts': 3}))
            else:
                ssm = boto3.client('ssm', config=Config(retries={'max_attempts': 3}))

            resp = ssm.get_parameter(Name=path, WithDecryption=True)
            val = resp['Parameter']['Value']
            return val.encode()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch SSM parameter {path}: {e}") from e

    def _decrypt_kms_ciphertext(self, ciphertext_b64: str) -> Optional[bytes]:
        """Decrypt a base64 KMS ciphertext using AWS KMS and return plaintext bytes.

        Raises RuntimeError with helpful message if boto3 is missing or decryption fails.
        """
        try:
            import boto3
            from botocore.config import Config
        except Exception as e:
            raise RuntimeError("boto3 is required to decrypt DISK_CACHE_KEY_KMS_CIPHERTEXT but it's not installed") from e

        try:
            try:
                from core.kms_utils import _assume_role_session  # type: ignore
            except Exception:
                _assume_role_session = None

            if _assume_role_session and self._role_arn:
                session = _assume_role_session(self._role_arn)
                kms = session.client('kms', config=Config(retries={'max_attempts': 3}))
            else:
                kms = boto3.client('kms', config=Config(retries={'max_attempts': 3}))

            ct = base64.b64decode(ciphertext_b64)
            resp = kms.decrypt(CiphertextBlob=ct)
            pt = resp['Plaintext']
            return pt
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt KMS ciphertext: {e}") from e

    def _path(self, key: str) -> Path:
        return self.dir / (_safe_name(key) + '.json')

    def set(self, key: str, value: bytes, ttl_seconds: Optional[int] = None):
        p = self._path(key)
        expires = int(time.time() + ttl_seconds) if ttl_seconds else None
        if self._have_crypto:
            aes = self._AESGCM(self.key)
            nonce = os.urandom(12)
            ct = aes.encrypt(nonce, value, None)
            payload = {'expires': expires, 'nonce': base64.b64encode(nonce).decode(), 'ct': base64.b64encode(ct).decode()}
        else:
            # plaintext fallback
            payload = {'expires': expires, 'plain': base64.b64encode(value).decode()}
        # atomic write
        tf = tempfile.NamedTemporaryFile(delete=False, dir=str(self.dir))
        try:
            with open(tf.name, 'w') as f:
                json.dump(payload, f)
            os.replace(tf.name, p)
        finally:
            try:
                os.unlink(tf.name)
            except Exception:
                pass

    def get(self, key: str) -> Optional[bytes]:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            with open(p, 'r') as f:
                payload = json.load(f)
        except Exception:
            return None
        expires = payload.get('expires')
        if expires and time.time() > expires:
            try:
                p.unlink()
            except Exception:
                pass
            return None
        if self._have_crypto:
            try:
                nonce = base64.b64decode(payload['nonce'])
                ct = base64.b64decode(payload['ct'])
                aes = self._AESGCM(self.key)
                pt = aes.decrypt(nonce, ct, None)
                return pt
            except Exception:
                return None
        else:
            try:
                return base64.b64decode(payload['plain'])
            except Exception:
                return None
 