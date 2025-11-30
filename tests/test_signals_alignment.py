import os
import sys
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path so `poc` and `src` imports resolve when pytest runs
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from poc.compare_algorithms import naive_momentum_signal, arima_signal, rf_signal
from src.eval.backtest import simple_backtest


def make_price_series(n=200):
    # business-day index
    idx = pd.bdate_range(end=pd.Timestamp.today(), periods=n)
    # synthetic walkup price
    rng = np.random.RandomState(42)
    steps = rng.normal(loc=0.0005, scale=0.01, size=n)
    price = 100 + np.cumsum(steps)
    return pd.Series(price, index=idx)


def test_signal_alignment_and_backtest():
    price = make_price_series(260)
    for fn in (naive_momentum_signal, arima_signal, rf_signal):
        sig = fn(price)
        # signals should be a Series
        assert isinstance(sig, pd.Series), f"signal from {fn.__name__} not a Series"
        # same index as price (after reindex in compare we expect same labels)
        assert sig.index.equals(price.index) or sig.index.isin(price.index).all(), (
            f"signal index mismatch for {fn.__name__}: {sig.index[:3]} vs {price.index[:3]}"
        )
        # run a tiny backtest to ensure we get a 1D Series back
        rets, metrics = simple_backtest(price, sig)
        assert hasattr(rets, 'ndim') and (rets.ndim == 1 or isinstance(rets, pd.Series)), (
            f"backtest returned non-1D for {fn.__name__}"
        )
        # metrics should contain sharpe key
        assert 'sharpe' in metrics
