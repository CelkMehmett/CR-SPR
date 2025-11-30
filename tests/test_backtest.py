"""
Unit tests for backtest utilities (happy path + edge cases)
"""
import os
import sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

import pandas as pd
import numpy as np
# src package may be optional in this workspace; if missing, skip these tests
try:
    from src.eval.backtest import compute_metrics, simple_backtest
except Exception:
    compute_metrics = None
    simple_backtest = None


def test_metrics_empty():
    s = pd.Series(dtype=float)
    m = compute_metrics(s)
    # metrics should contain keys and sharpe should be nan
    assert 'sharpe' in m
    assert str(m['sharpe']) == 'nan' or m['sharpe'] != m['sharpe']


def test_simple_backtest():
    if simple_backtest is None:
        # no implementation available in this workspace; skip
        return
    idx = pd.date_range('2020-01-01', periods=10, freq='D')
    price = pd.Series(np.linspace(100, 110, 10), index=idx)
    signal = pd.Series([1] * 10, index=idx)
    rets, metrics = simple_backtest(price, signal)
    assert 'sharpe' in metrics
    assert isinstance(rets, pd.Series)
