"""
Simple SQLite-based checkpoint storage for RL controller states.

Stores pickled controller state blobs under a name and timestamp.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
import datetime
import os
from core.crypto_utils import encryption_available, encrypt_blob, decrypt_blob


def init_db(db_path: str = "./rl_checkpoints.db"):
    p = Path(db_path)
    conn = sqlite3.connect(str(p))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            blob BLOB NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_checkpoint(db_path: str, name: str, blob: bytes):
    init_db(db_path)
    # optionally encrypt blob if CHECKPOINT_ENC_KEY is present
    try:
        if os.environ.get('CHECKPOINT_ENC_KEY'):
            if not encryption_available():
                raise RuntimeError('Encryption key set but cryptography package missing')
            blob = encrypt_blob(blob)
    except Exception:
        # if encryption fails, raise to let caller decide
        raise
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO checkpoints (name, created_at, blob) VALUES (?, ?, ?)",
        (name, datetime.datetime.utcnow().isoformat(), sqlite3.Binary(blob))
    )
    conn.commit()
    conn.close()


def load_checkpoint(db_path: str, name: str) -> Optional[bytes]:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT blob FROM checkpoints WHERE name = ? ORDER BY id DESC LIMIT 1", (name,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    data = row[0]
    # if encryption key present, attempt decrypt (detect header inside crypto_utils)
    try:
        if os.environ.get('CHECKPOINT_ENC_KEY'):
            data = decrypt_blob(data)
    except Exception:
        # if decryption fails, raise
        raise
    return data


def list_checkpoints(db_path: str) -> List[Dict[str, str]]:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM checkpoints ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'created_at': r[2]} for r in rows]
