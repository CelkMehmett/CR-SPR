"""Simple JSON edit logger to record before/after parameter states and metrics.

Biological note: acts like a DNA edit trace recorder.
"""
from __future__ import annotations
from typing import Any, Dict
import json
from datetime import datetime


def log_edit(path: str, before: Dict[str, Any], after: Dict[str, Any], metrics_before: Dict[str, float], metrics_after: Dict[str, float]):
    payload = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'before': before,
        'after': after,
        'metrics_before': metrics_before,
        'metrics_after': metrics_after,
    }
    with open(path, 'a') as f:
        f.write(json.dumps(payload) + '\n')
