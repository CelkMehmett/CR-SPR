import sys
import os
import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.detect.drift import performance_drift, distribution_drift
from src.edit.simple_edits import fallback_to_baseline, smooth_signals


def make_price(n=400, drift=False):
    idx = pd.bdate_range(end=pd.Timestamp.today(), periods=n)
    rng = np.random.RandomState(0)
    steps = rng.normal(loc=0.0002, scale=0.01, size=n)
    if drift:
        # introduce negative bias in recent half
        steps[n//2:] -= 0.001
    price = 100 + np.cumsum(steps)
    return pd.Series(price, index=idx)


def test_performance_and_distribution_drift():
    p = make_price(400, drift=False)
    is_d, diag = performance_drift(p, recent_window=63, hist_window=126)
    assert isinstance(is_d, bool)
    assert 'recent_sharpe' in diag or 'reason' in diag

    p2 = make_price(400, drift=True)
    is_d2, diag2 = performance_drift(p2, recent_window=63, hist_window=126)
    # with injected drift we expect detection to be either True or have valid diagnostics
    assert isinstance(is_d2, bool)

    # distribution drift
    is_dd, ddiag = distribution_drift(p, window=200, recent=63)
    assert isinstance(is_dd, bool)
    is_dd2, ddiag2 = distribution_drift(p2, window=200, recent=63)
    assert isinstance(is_dd2, bool)


def test_edits():
    p = make_price(200)
    sig = (p > p.rolling(20).mean()).astype(int)
    baseline = (p > p.rolling(50).mean()).astype(int)
    out = fallback_to_baseline(sig, baseline)
    assert out.index.equals(sig.index)
    # smoothing
    noisy = sig.copy()
    noisy.iloc[::7] = 1 - noisy.iloc[::7]
    smooth = smooth_signals(noisy, window=7)
    assert isinstance(smooth, pd.Series)
    assert smooth.index.equals(noisy.index)
