"""Lightweight drift detection utilities.

Two detectors:
- performance_drift: compare recent rolling Sharpe to historical baseline
- distribution_drift: KS-test between two return windows

These are intentionally small and dependency-light.
"""
from __future__ import annotations
from typing import Tuple
import numpy as np
import pandas as pd
from scipy import stats


def returns(series: pd.Series) -> pd.Series:
    return series.pct_change().dropna()


def rolling_sharpe(rets: pd.Series, window: int = 63) -> pd.Series:
    # approximate annualization factor for daily business days
    ann = np.sqrt(252)
    return (rets.rolling(window).mean() / rets.rolling(window).std()).fillna(0) * ann


def performance_drift(price: pd.Series, recent_window: int = 63, hist_window: int = 252, threshold: float = 0.5) -> Tuple[bool, dict]:
    """Detect performance drift by comparing recent rolling Sharpe to historical.

    Returns (is_drift, diagnostics)
    - is_drift True if recent_sharpe < threshold * hist_sharpe
    """
    if price is None or len(price) < max(recent_window, hist_window) + 2:
        return False, {"reason": "insufficient_data"}

    rets = returns(price)
    if rets.empty:
        return False, {"reason": "no_returns"}

    recent = rolling_sharpe(rets, window=recent_window).dropna()
    hist = rolling_sharpe(rets, window=hist_window).dropna()
    if recent.empty or hist.empty:
        return False, {"reason": "not_enough_sharpe_points"}

    recent_sh = float(recent.iloc[-1])
    hist_sh = float(hist.mean())

    if hist_sh == 0:
        is_drift = bool(recent_sh < threshold and recent_sh < 0)
    else:
        is_drift = bool(recent_sh < (threshold * hist_sh))

    return is_drift, {"recent_sharpe": recent_sh, "hist_sharpe": hist_sh}


def distribution_drift(price: pd.Series, window: int = 126, recent: int = 63, p_thresh: float = 0.05) -> Tuple[bool, dict]:
    """Detect drift by KS-test between older window and recent window of returns.

    Returns (is_drift, diagnostics)
    """
    if price is None or len(price) < window + recent + 2:
        return False, {"reason": "insufficient_data"}
    rets = returns(price)
    if rets.empty:
        return False, {"reason": "no_returns"}

    older = rets.iloc[-(window + recent):-recent]
    new = rets.iloc[-recent:]
    if older.empty or new.empty:
        return False, {"reason": "not_enough_samples"}

    stat, p = stats.ks_2samp(older, new)
    is_drift = bool(p < p_thresh)
    return is_drift, {"ks_stat": float(stat), "p_value": float(p)}
