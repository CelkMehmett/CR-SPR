import os
import sys
import base64

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from unittest import mock


def test_kms_decrypt_path(monkeypatch):
    # Prepare a fake KMS ciphertext and the expected plaintext key
    plaintext = b'my-test-key-0123456789abcdef012345'
    ct = b'fake-ciphertext'
    os.environ['CHECKPOINT_KEY_KMS_CIPHERTEXT'] = base64.b64encode(ct).decode('utf-8')
    # set assume role to trigger that branch
    os.environ['CHECKPOINT_AWS_ASSUME_ROLE_ARN'] = 'arn:aws:iam::123456789012:role/TestRole'

    # Mock boto3 behavior: sts.assume_role -> credentials, and kms.decrypt -> plaintext
    class FakeCreds:
        def __init__(self):
            self._resp = {
                'Credentials': {
                    'AccessKeyId': 'AKIAFAKE',
                    'SecretAccessKey': 'SECRETFAKE',
                    'SessionToken': 'TOKENFAKE'
                }
            }
        def assume_role(self, RoleArn, RoleSessionName):
            return self._resp

    class FakeKms:
        def __init__(self, plaintext):
            self._plaintext = plaintext
        def decrypt(self, CiphertextBlob):
            return {'Plaintext': self._plaintext}

    fake_sts = FakeCreds()
    fake_kms = FakeKms(plaintext)

    # monkeypatch boto3 client and Session
    fake_boto3 = mock.MagicMock()
    fake_boto3.client.side_effect = lambda svc: fake_sts if svc == 'sts' else fake_kms

    class FakeSession:
        def __init__(self, **kwargs):
            pass
        def client(self, svc):
            return fake_kms

    fake_boto3.Session = lambda **kw: FakeSession()

    monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)

    # Now import the util and call _get_key_from_env indirectly via encrypt/decrypt availability
    from core.crypto_utils import _get_key_from_env

    k = _get_key_from_env()
    assert k == plaintext

    # cleanup env
    del os.environ['CHECKPOINT_KEY_KMS_CIPHERTEXT']
    del os.environ['CHECKPOINT_AWS_ASSUME_ROLE_ARN']
