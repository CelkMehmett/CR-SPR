"""Optional encryption utilities for checkpoint blobs.

Uses AES-GCM via the `cryptography` package when available. If the
library is missing, functions raise ImportError when encryption is used.

Blobs are encoded as: b'ENC1' + nonce(12) + ciphertext
"""
from typing import Optional
import os
import base64

ENC_HEADER = b'ENC1'
_NONCE_SIZE = 12


def _get_key_from_env() -> Optional[bytes]:
    # Accept either a raw hex key or a passphrase in CHECKPOINT_ENC_KEY
    # First, support fetching from AWS SSM if CHECKPOINT_KEY_SSM_PATH provided
    # 1) KMS ciphertext (base64) - decrypt via AWS KMS
    kms_ct = os.environ.get('CHECKPOINT_KEY_KMS_CIPHERTEXT')
    if kms_ct:
        try:
            # defer boto3 import until needed
            import boto3  # type: ignore
            ct = base64.b64decode(kms_ct)
            # support optional assume-role via CHECKPOINT_AWS_ASSUME_ROLE_ARN
            def _get_kms_client():
                role_arn = os.environ.get('CHECKPOINT_AWS_ASSUME_ROLE_ARN')
                if role_arn:
                    # attempt to assume role and create a session with temporary creds
                    sts = boto3.client('sts')
                    resp = sts.assume_role(RoleArn=role_arn, RoleSessionName='crisper-kms-session')
                    creds = resp.get('Credentials', {})
                    session = boto3.Session(
                        aws_access_key_id=creds.get('AccessKeyId'),
                        aws_secret_access_key=creds.get('SecretAccessKey'),
                        aws_session_token=creds.get('SessionToken')
                    )
                    return session.client('kms')
                return boto3.client('kms')

            kms = _get_kms_client()
            resp = kms.decrypt(CiphertextBlob=ct)
            plaintext = resp.get('Plaintext')
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')
            if plaintext:
                return plaintext
        except Exception:
            # any failure falls through to other methods below
            pass

    ssm_path = os.environ.get('CHECKPOINT_KEY_SSM_PATH')
    if ssm_path:
        try:
            import boto3
            client = boto3.client('ssm')
            resp = client.get_parameter(Name=ssm_path, WithDecryption=True)
            v = resp['Parameter']['Value']
        except Exception:
            # couldn't fetch from SSM; fall back to env var
            v = os.environ.get('CHECKPOINT_ENC_KEY')
    else:
        v = os.environ.get('CHECKPOINT_ENC_KEY')
    if not v:
        return None
    # if looks like hex, decode
    try:
        if all(c in '0123456789abcdefABCDEF' for c in v) and len(v) in (32, 64):
            # 16 or 32 bytes hex
            return bytes.fromhex(v)
    except Exception:
        pass
    # otherwise derive 32-byte key via SHA256 of passphrase
    try:
        import hashlib
        return hashlib.sha256(v.encode('utf-8')).digest()
    except Exception:
        return None


def encryption_available() -> bool:
    try:
        return True
    except Exception:
        return False


def encrypt_blob(blob: bytes) -> bytes:
    key = _get_key_from_env()
    if key is None:
        raise ValueError('No CHECKPOINT_ENC_KEY environment variable set')
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    except Exception:
        raise ImportError('cryptography library required for encryption')

    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_SIZE)
    ct = aesgcm.encrypt(nonce, blob, None)
    return ENC_HEADER + nonce + ct


def decrypt_blob(blob: bytes) -> bytes:
    if not blob.startswith(ENC_HEADER):
        # not encrypted
        return blob
    key = _get_key_from_env()
    if key is None:
        raise ValueError('No CHECKPOINT_ENC_KEY environment variable set')
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    except Exception:
        raise ImportError('cryptography library required for decryption')

    nonce = blob[len(ENC_HEADER):len(ENC_HEADER)+_NONCE_SIZE]
    ct = blob[len(ENC_HEADER)+_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)
