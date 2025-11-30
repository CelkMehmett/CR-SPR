"""
Append-only Audit Logger for CRISPR-FinAI edits.

Each edit is recorded as a JSON line with metadata for traceability.
Simple querying and CSV export utilities included.
"""

from __future__ import annotations
import json
import os
import time
import uuid
from typing import Any, Dict, Optional, List

AUDIT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'edits.jsonl'))
os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)


class AuditLogger:
    """Minimal append-only logger for edit operations.

    Record format: {
        edit_id, timestamp, author, target, before, after, metrics_before, metrics_after, note
    }
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path or AUDIT_FILE
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def _make_record(self, target: Dict[str, Any], before: Dict[str, Any], after: Dict[str, Any], metrics_before: Dict[str, float], metrics_after: Dict[str, float], author: str = 'cas-ai', note: str = '') -> Dict[str, Any]:
        return {
            'edit_id': str(uuid.uuid4()),
            'timestamp': int(time.time()),
            'author': author,
            'target': target,
            'before': before,
            'after': after,
            'metrics_before': metrics_before,
            'metrics_after': metrics_after,
            'note': note,
        }

    def log_edit(self, target: Dict[str, Any], before: Dict[str, Any], after: Dict[str, Any], metrics_before: Dict[str, float], metrics_after: Dict[str, float], author: str = 'cas-ai', note: str = '') -> str:
        rec = self._make_record(target, before, after, metrics_before, metrics_after, author, note)
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, default=str) + '\n')
        return rec['edit_id']

    def query_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        lines: List[Dict[str, Any]] = []
        with open(self.path, encoding='utf-8') as f:
            for line in f:
                try:
                    lines.append(json.loads(line))
                except Exception:
                    continue
        return lines[-n:]

    def export_csv(self, out_path: str) -> str:
        import csv

        rows = self.query_recent(1000000)
        if not rows:
            return out_path
        keys = set()
        for r in rows:
            keys.update(r.keys())
        keys = sorted(list(keys))
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else v for k, v in r.items()})
        return out_path
