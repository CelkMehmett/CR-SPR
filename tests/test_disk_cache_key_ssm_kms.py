import base64
import pytest
import types
import sys

from core.disk_cache import DiskCache


class DummySSM:
    def __init__(self, value: str):
        self._value = value

    def get_parameter(self, Name, WithDecryption=False):
        return {'Parameter': {'Value': self._value}}


class DummyKMS:
    def __init__(self, plaintext: bytes):
        self._pt = plaintext

    def decrypt(self, CiphertextBlob=None):
        return {'Plaintext': self._pt}


def test_ssm_parameter_fetch(monkeypatch, tmp_path):
    # monkeypatch boto3 client for ssm
    def fake_client(name, config=None):
        if name == 'ssm':
            return DummySSM('supersecret')
        raise RuntimeError('unexpected')

    fake_boto3 = types.SimpleNamespace()
    fake_boto3.client = fake_client
    # boto3 imports botocore.config.Config; provide a fake
    fake_botocore = types.SimpleNamespace()
    fake_botocore_config = types.SimpleNamespace(Config=lambda **kwargs: None)
    # provide both package and submodule entries so import works
    monkeypatch.setitem(sys.modules, 'botocore', fake_botocore)
    monkeypatch.setitem(sys.modules, 'botocore.config', fake_botocore_config)
    monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)

    dc = DiskCache(str(tmp_path), ssm_path='/my/param')
    # DiskCache will derive a 32-byte SHA256 key when cryptography is available
    import hashlib
    expected_raw = b'supersecret'
    expected_hashed = hashlib.sha256(expected_raw).digest()
    assert dc.key in (expected_raw, expected_hashed)


def test_kms_decrypt(monkeypatch, tmp_path):
    pt = b'myplaintext'
    ct = base64.b64encode(b'cipherblob').decode()

    def fake_client(name, config=None):
        if name == 'kms':
            return DummyKMS(pt)
        raise RuntimeError('unexpected')

    fake_boto3 = types.SimpleNamespace()
    fake_boto3.client = fake_client
    fake_botocore = types.SimpleNamespace()
    fake_botocore_config = types.SimpleNamespace(Config=lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, 'botocore', fake_botocore)
    monkeypatch.setitem(sys.modules, 'botocore.config', fake_botocore_config)
    monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)

    dc = DiskCache(str(tmp_path), kms_ciphertext_b64=ct)
    import hashlib
    expected_raw = pt
    expected_hashed = hashlib.sha256(expected_raw).digest()
    assert dc.key in (expected_raw, expected_hashed)


def test_boto3_missing_raises(tmp_path):
    # ensure boto3 is not present
    sys.modules.pop('boto3', None)
    with pytest.raises(RuntimeError):
        DiskCache(str(tmp_path), ssm_path='/param/does/not/matter')
