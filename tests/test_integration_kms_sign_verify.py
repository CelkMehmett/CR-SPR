import os
import pytest
import hashlib

from core.kms_utils import kms_sign_digest, kms_verify_signature


@pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1", reason="Local integration tests disabled")
def test_kms_sign_verify_flow(tmp_path):
    # Requires LocalStack running and a KMS key created at /ci/keys/kms-test (created by provisioning step)
    # The CI provisioning creates a key and writes ciphertext to key.b64; here we assume a key is available.
    # For simplicity, discover a key by listing keys via AWS CLI (LocalStack) — but here we expect CI to set KMS_KEY_ID env var
    key_id = os.environ.get('KMS_KEY_ID')
    if not key_id:
        pytest.skip('KMS_KEY_ID not provided')

    # create a digest to sign
    data = b"integration-test-data"
    digest = hashlib.sha256(data).digest()

    sig_hex = kms_sign_digest(key_id=key_id, digest=digest, signing_algorithm='ECDSA_SHA_256', region='us-east-1')
    assert isinstance(sig_hex, str) and len(sig_hex) > 0

    ok = kms_verify_signature(key_id=key_id, digest=digest, signature_hex=sig_hex, signing_algorithm='ECDSA_SHA_256', region='us-east-1')
    assert ok is True
