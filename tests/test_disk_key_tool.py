import base64
import types
import sys


from scripts import disk_key_tool


class DummyKMS:
    def encrypt(self, KeyId=None, Plaintext=None):
        return {'CiphertextBlob': b'cipher-' + (Plaintext or b'')}


class DummySSM:
    def __init__(self):
        self.store = {}

    def put_parameter(self, Name=None, Value=None, Type=None, Overwrite=False, Description=''):
        self.store[Name] = Value
        return {'Version': 1}


def test_encrypt_with_kms(monkeypatch, tmp_path):
    key_file = tmp_path / 'k.bin'
    key_file.write_bytes(b'mykey')

    def fake_client(name, region_name=None, config=None):
        if name == 'kms':
            return DummyKMS()
        raise RuntimeError('unexpected')

    fake_boto3 = types.SimpleNamespace()
    fake_boto3.client = fake_client
    fake_botocore = types.SimpleNamespace()
    fake_botocore_config = types.SimpleNamespace(Config=lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)
    monkeypatch.setitem(sys.modules, 'botocore', fake_botocore)
    monkeypatch.setitem(sys.modules, 'botocore.config', fake_botocore_config)

    # capture stdout
    out = []
    monkeypatch.setattr('builtins.print', lambda *a, **k: out.append(' '.join(map(str, a))))

    disk_key_tool.encrypt_with_kms(str(key_file), 'fake-key')
    assert out
    ct_b64 = out[-1]
    # ensure it's base64 decodable
    decoded = base64.b64decode(ct_b64)
    assert decoded.startswith(b'cipher-')


def test_upload_to_ssm(monkeypatch, tmp_path):
    key_file = tmp_path / 'k.bin'
    key_file.write_bytes(b'mykey')

    def fake_client(name, region_name=None, config=None):
        if name == 'ssm':
            return DummySSM()
        raise RuntimeError('unexpected')

    fake_boto3 = types.SimpleNamespace()
    fake_boto3.client = fake_client
    fake_botocore = types.SimpleNamespace()
    fake_botocore_config = types.SimpleNamespace(Config=lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)
    monkeypatch.setitem(sys.modules, 'botocore', fake_botocore)
    monkeypatch.setitem(sys.modules, 'botocore.config', fake_botocore_config)

    out = []
    monkeypatch.setattr('builtins.print', lambda *a, **k: out.append(' '.join(map(str, a))))

    disk_key_tool.upload_to_ssm(str(key_file), '/param/test')
    assert any('Uploaded' in o for o in out)

