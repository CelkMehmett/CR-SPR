import os
import sys
import time

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from fastapi.testclient import TestClient
from core import api_server

client = TestClient(api_server.app)
HEADERS = {'Authorization': 'Bearer your-secret-api-key-here'}


def test_download_checkpoint_encrypted():
    # set a deterministic key (32 bytes hex)
    key_hex = 'a3' * 16  # 32 hex chars -> 16 bytes; crypto_utils accepts 16 or 32 bytes hex
    os.environ['CHECKPOINT_ENC_KEY'] = key_hex

    # ensure cryptography is available; if not, skip by raising
    try:
        pass  # type: ignore
    except Exception:
        # cryptography not installed; skip test by returning early
        return

    # create checkpoint
    r = client.post('/api/rl/start', json={'symbols': ['D2'], 'models': ['m2'], 'rounds': 2, 'light_mode': True, 'checkpoint_name': 'enc1'}, headers=HEADERS)
    assert r.status_code == 200
    time.sleep(0.6)

    # download (the endpoint will attempt to decrypt because CHECKPOINT_ENC_KEY is set)
    r2 = client.get('/api/rl/download_checkpoint/enc1', headers=HEADERS)
    assert r2.status_code == 200
    content = r2.content
    assert isinstance(content, (bytes, bytearray))

    # Inspect the underlying SQLite DB to ensure the stored blob is encrypted
    import sqlite3
    db_path = './rl_checkpoints.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT blob FROM checkpoints WHERE name = ? ORDER BY id DESC LIMIT 1", ('enc1',))
    row = cur.fetchone()
    conn.close()
    assert row is not None
    stored_raw = row[0]

    # raw stored blob should be encrypted (starts with ENC1)
    from core.crypto_utils import ENC_HEADER, decrypt_blob
    assert stored_raw.startswith(ENC_HEADER)

    # decrypted stored blob should equal the downloaded content
    dec = decrypt_blob(stored_raw)
    assert dec == content
