import os
import pytest

from core.kms_utils import _assume_role_session


@pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1", reason="Local integration tests disabled")
def test_assume_role_with_localstack(tmp_path):
    # This test expects LocalStack to be running and that the provisioning step
    # has created a role named 'CrisprTestRole' with an assume-role policy allowing sts:AssumeRole.
    # We will attempt to assume that role using _assume_role_session and call STS.GetCallerIdentity.

    # Discover role ARN via AWS CLI (provisioning should create it at /ci/roles/CrisprTestRole)
    # But if CI writes the role ARN into a file, read it from ROLE_ARN.txt
    role_arn = None
    if (tmp_path / "ROLE_ARN.txt").exists():
        role_arn = (tmp_path / "ROLE_ARN.txt").read_text().strip()
    else:
        # fallback to environment variable set by Makefile/CI
        role_arn = os.environ.get('DISK_CACHE_KEY_ROLE_ARN') or os.environ.get('ROLE_ARN')

    if not role_arn:
        pytest.skip('No role ARN available for assume-role test')

    # Try to assume the role
    session = _assume_role_session(role_arn)
    sts = session.client('sts', region_name='us-east-1')
    resp = sts.get_caller_identity()
    assert 'Account' in resp and 'Arn' in resp
