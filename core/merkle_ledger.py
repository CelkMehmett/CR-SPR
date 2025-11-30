"""Merkle ledger utilities for Merkle-AI Chain.

Provides append, root calculation and a simple inclusion proof builder and verifier.
"""
from typing import List, Tuple, Optional
import hashlib
import json
import sqlite3
from pathlib import Path
from contextlib import closing
import hmac
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False


def _hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


class MerkleLedger:
    def __init__(self):
        self.leaves: List[bytes] = []

    # Persistence utilities
    def save_sqlite(self, path: str = './merkle_ledger.db', table: str = 'ledger') -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            cur.execute(f"CREATE TABLE IF NOT EXISTS {table} (idx INTEGER PRIMARY KEY AUTOINCREMENT, leaf BLOB)")
            # append any new leaves
            cur.execute(f"SELECT COUNT(1) FROM {table}")
            row = cur.fetchone()
            existing = row[0] if row is not None else 0
            to_write = self.leaves[existing:]
            if to_write:
                cur.executemany(f"INSERT INTO {table} (leaf) VALUES (?)", [(l,) for l in to_write])
            conn.commit()

    def load_sqlite(self, path: str = './merkle_ledger.db', table: str = 'ledger') -> None:
        p = Path(path)
        if not p.exists():
            return
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            try:
                cur.execute(f"SELECT leaf FROM {table} ORDER BY idx ASC")
            except Exception:
                return
            rows = cur.fetchall()
            self.leaves = [bytes(r[0]) for r in rows]

    def export_json(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        arr = [l.hex() for l in self.leaves]
        with open(p, 'w') as f:
            json.dump({'leaves': arr}, f)

    def import_json(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        with open(p) as f:
            obj = json.load(f)
        self.leaves = [bytes.fromhex(h) for h in obj.get('leaves', [])]

    # Snapshot management (named snapshots stored in sqlite for portability)
    def save_snapshot(self, name: str, path: str = './merkle_ledger.db', snapshot_table: str = 'snapshots') -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        arr = [l.hex() for l in self.leaves]
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            cur.execute(f"CREATE TABLE IF NOT EXISTS {snapshot_table} (name TEXT PRIMARY KEY, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, data TEXT)")
            cur.execute(f"REPLACE INTO {snapshot_table} (name, data) VALUES (?, ?)", (name, json.dumps({'leaves': arr})))
            conn.commit()

    def list_snapshots(self, path: str = './merkle_ledger.db', snapshot_table: str = 'snapshots') -> list:
        p = Path(path)
        if not p.exists():
            return []
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            try:
                cur.execute(f"SELECT name, created FROM {snapshot_table} ORDER BY created ASC")
            except Exception:
                return []
            rows = cur.fetchall()
            return [{'name': r[0], 'created': r[1]} for r in rows]

    def load_snapshot(self, name: str, path: str = './merkle_ledger.db', snapshot_table: str = 'snapshots') -> None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT data FROM {snapshot_table} WHERE name=?", (name,))
            row = cur.fetchone()
            if not row:
                raise KeyError('snapshot not found')
            obj = json.loads(row[0])
            self.leaves = [bytes.fromhex(h) for h in obj.get('leaves', [])]

    def delete_snapshot(self, name: str, path: str = './merkle_ledger.db', snapshot_table: str = 'snapshots') -> None:
        p = Path(path)
        if not p.exists():
            return
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            try:
                cur.execute(f"DELETE FROM {snapshot_table} WHERE name=?", (name,))
                conn.commit()
            except Exception:
                pass

    # Signature history: store signatures produced for roots
    def save_signature(self, signature_hex: str, key_id: str = '', method: str = '', metadata: dict = None, path: str = './merkle_ledger.db', sig_table: str = 'signatures') -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        meta = json.dumps(metadata or {})
        root = self.root()
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            cur.execute(f"CREATE TABLE IF NOT EXISTS {sig_table} (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, key_id TEXT, method TEXT, root TEXT, signature TEXT, metadata TEXT)")
            cur.execute(f"INSERT INTO {sig_table} (key_id, method, root, signature, metadata) VALUES (?, ?, ?, ?, ?)", (key_id, method, root or '', signature_hex, meta))
            conn.commit()

    def list_signatures(self, path: str = './merkle_ledger.db', sig_table: str = 'signatures') -> list:
        p = Path(path)
        if not p.exists():
            return []
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            try:
                cur.execute(f"SELECT id, created, key_id, method, root, signature, metadata FROM {sig_table} ORDER BY id DESC")
            except Exception:
                return []
            rows = cur.fetchall()
            out = []
            for r in rows:
                out.append({
                    'id': r[0], 'created': r[1], 'key_id': r[2], 'method': r[3], 'root': r[4], 'signature': r[5], 'metadata': json.loads(r[6] or '{}')
                })
            return out

    def get_signature(self, sig_id: int, path: str = './merkle_ledger.db', sig_table: str = 'signatures') -> dict:
        p = Path(path)
        if not p.exists():
            raise KeyError('no signatures')
        with closing(sqlite3.connect(str(p))) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT id, created, key_id, method, root, signature, metadata FROM {sig_table} WHERE id=?", (sig_id,))
            row = cur.fetchone()
            if not row:
                raise KeyError('signature not found')
            return {'id': row[0], 'created': row[1], 'key_id': row[2], 'method': row[3], 'root': row[4], 'signature': row[5], 'metadata': json.loads(row[6] or '{}')}

    # Signing helpers for root auditability
    def _root_bytes(self) -> bytes:
        r = self.root()
        if r is None:
            return b''
        return bytes.fromhex(r)

    def sign_root(self, key: bytes) -> str:
        """Return HMAC-SHA256 signature hex for the current root using `key`."""
        root_b = self._root_bytes()
        sig = hmac.new(key, root_b, hashlib.sha256).hexdigest()
        return sig

    @staticmethod
    def verify_root_signature(root_hex: str, signature_hex: str, key: bytes) -> bool:
        try:
            root_b = bytes.fromhex(root_hex)
            expected = hmac.new(key, root_b, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature_hex)
        except Exception:
            return False

    # Asymmetric Ed25519 helpers (PEM input supported)
    def sign_root_ed25519(self, private_pem: bytes) -> str:
        """Sign the current root using an Ed25519 private key in PEM format. Returns hex signature."""
        if not _HAS_CRYPTO:
            raise RuntimeError('cryptography not available')
        root_b = self._root_bytes()
        priv = serialization.load_pem_private_key(private_pem, password=None)
        if not isinstance(priv, Ed25519PrivateKey):
            raise RuntimeError('private key is not Ed25519')
        sig = priv.sign(root_b)
        return sig.hex()

    @staticmethod
    def verify_root_signature_ed25519(root_hex: str, signature_hex: str, public_pem: bytes) -> bool:
        """Verify Ed25519 signature given root hex and public key PEM."""
        if not _HAS_CRYPTO:
            return False
        try:
            pub = serialization.load_pem_public_key(public_pem)
            if not isinstance(pub, Ed25519PublicKey):
                return False
            root_b = bytes.fromhex(root_hex)
            sig = bytes.fromhex(signature_hex)
            pub.verify(sig, root_b)
            return True
        except Exception:
            return False

    def append(self, record: dict) -> str:
        raw = json.dumps(record, sort_keys=True, default=str).encode('utf-8')
        h = _hash(raw)
        self.leaves.append(h)
        return h.hex()

    def root(self) -> Optional[str]:
        if not self.leaves:
            return None
        nodes = list(self.leaves)
        while len(nodes) > 1:
            nxt = []
            for i in range(0, len(nodes), 2):
                a = nodes[i]
                b = nodes[i+1] if i+1 < len(nodes) else a
                nxt.append(_hash(a + b))
            nodes = nxt
        return nodes[0].hex()

    def inclusion_proof(self, index: int) -> List[Tuple[str, str]]:
        """Return a proof as list of (hex_hash, direction) where direction is 'L' or 'R'."""
        proof = []
        n = len(self.leaves)
        if index < 0 or index >= n:
            raise IndexError('leaf index out of range')
        layer = list(self.leaves)
        idx = index
        while len(layer) > 1:
            nxt = []
            for i in range(0, len(layer), 2):
                a = layer[i]
                b = layer[i+1] if i+1 < len(layer) else a
                nxt.append(_hash(a + b))
                if i == idx or i+1 == idx:
                    # sibling
                    if i == idx:
                        sibling = b
                        direction = 'R'
                    else:
                        sibling = a
                        direction = 'L'
                    proof.append((sibling.hex(), direction))
                    idx = len(nxt) - 1
            layer = nxt
        return proof

    @staticmethod
    def verify_proof(leaf_hash_hex: str, proof: List[Tuple[str, str]], root_hex: str) -> bool:
        cur = bytes.fromhex(leaf_hash_hex)
        for h_hex, direction in proof:
            h = bytes.fromhex(h_hex)
            if direction == 'L':
                cur = _hash(h + cur)
            else:
                cur = _hash(cur + h)
        return cur.hex() == root_hex
