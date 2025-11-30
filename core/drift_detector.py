"""Cognitive Drift Antibody System: simple drift detector and trigger mechanism.

Provides a rolling-window mean detector that calls registered callbacks when
performance drops by more than a configured threshold relative to baseline.
"""
from typing import Callable, List
import collections


class DriftDetector:
    def __init__(self, window: int = 20, threshold: float = 0.2):
        self.window = window
        self.threshold = threshold
        self.values = collections.deque(maxlen=window)
        self.callbacks: List[Callable[[float, float], None]] = []

    def register_callback(self, cb: Callable[[float, float], None]):
        self.callbacks.append(cb)

    def add(self, value: float):
        self.values.append(value)
        if len(self.values) >= max(3, self.window // 4):
            self._check()

    def _check(self):
        vals = list(self.values)
        baseline = sum(vals[:-1]) / max(1, len(vals)-1)
        current = vals[-1]
        if baseline == 0:
            return
        drop = (baseline - current) / abs(baseline)
        if drop >= self.threshold:
            for cb in self.callbacks:
                try:
                    cb(baseline, current)
                except Exception:
                    pass


def detect_isolationforest(feats) -> (bool, dict):
    """Compatibility helper used by older POC code.

    Tries to use sklearn's IsolationForest when available. Returns a tuple
    (is_drift: bool, diagnostics: dict). If sklearn is not installed, falls
    back to a simple z-score heuristic across features.
    """
    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np

        X = feats.values if hasattr(feats, 'values') else np.array(feats)
        if X.size == 0:
            return False, {'reason': 'no_data'}
        iso = IsolationForest(random_state=42, contamination='auto')
        preds = iso.fit_predict(X)
        # anomaly if any recent point is flagged as -1
        is_anom = int((preds == -1).sum() > 0)
        return bool(is_anom), {'anomalies': int((preds == -1).sum())}
    except Exception:
        # fallback: simple z-score over columns
        try:
            import numpy as np
            arr = feats.values if hasattr(feats, 'values') else np.array(feats)
            if arr.size == 0:
                return False, {'reason': 'no_data'}
            means = arr.mean(axis=0)
            stds = arr.std(axis=0)
            z = np.abs((arr - means) / (stds + 1e-9))
            max_z = z.max()
            is_drift = bool(max_z > 3.0)
            return is_drift, {'max_z': float(max_z)}
        except Exception:
            return False, {'reason': 'error'}
