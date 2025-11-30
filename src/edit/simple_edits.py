"""Small edit/repair utilities for signals.

Functions:
- fallback_to_baseline(signal, baseline_signal): if drift detected, return baseline
- smooth_signals(signal, window=5): apply rolling median smoothing to reduce noise
"""
from __future__ import annotations
import pandas as pd


def fallback_to_baseline(signal: pd.Series, baseline: pd.Series) -> pd.Series:
    """Return baseline if shapes align; otherwise try to align by index."""
    if not isinstance(signal, pd.Series) or not isinstance(baseline, pd.Series):
        return signal
    # try to align index
    try:
        out = baseline.reindex(signal.index).fillna(0).astype(int)
        return out
    except Exception:
        return baseline


def smooth_signals(signal: pd.Series, window: int = 5) -> pd.Series:
    if not isinstance(signal, pd.Series) or signal.empty:
        return signal
    # use rolling median and then threshold at 0.5 to produce binary signals
    med = signal.rolling(window, min_periods=1, center=False).median()
    return (med > 0.5).astype(int)
