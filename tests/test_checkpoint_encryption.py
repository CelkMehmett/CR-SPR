import os
import sys
import pytest

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core import rl_checkpoint


def _crypto_available():
    try:
        import cryptography  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _crypto_available(), reason="cryptography not installed")
def test_encrypt_decrypt_roundtrip(tmp_path):
    # set a deterministic key for test (32 bytes hex)
    os.environ['CHECKPOINT_ENC_KEY'] = '00' * 32
    data = b'hello world'
    # write as a checkpoint
    db = tmp_path / 'test_ckpt.db'
    rl_checkpoint.save_checkpoint(str(db), 't1', data)
    # load it back
    out = rl_checkpoint.load_checkpoint(str(db), 't1')
    assert out == data
