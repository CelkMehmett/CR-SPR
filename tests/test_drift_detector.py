import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.drift_detector import DriftDetector


def test_drift_detector_triggers():
    d = DriftDetector(window=6, threshold=0.3)
    triggered = []

    def cb(baseline, current):
        triggered.append((baseline, current))

    d.register_callback(cb)
    # push stable high values
    for v in [1.0, 1.1, 0.9, 1.05, 1.02]:
        d.add(v)
    # now sudden drop
    d.add(0.5)
    assert len(triggered) >= 1
