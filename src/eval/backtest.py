"""
Backtesting utilities for CRISPR-FinAI (simple, dependency-light).

Includes metric calculations (Sharpe, volatility, max drawdown, hit rate)
and simple signal-to-returns simulation.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Tuple


def compute_metrics(returns: pd.Series, periods_per_year: int = 252) -> Dict[str, float]:
    """Compute core performance metrics from a returns series.

    Args:
        returns: pd.Series of strategy returns (e.g., 0.01 for 1%)
    """
    r = returns.dropna()
    if r.empty:
        return {"sharpe": float("nan"), "volatility": float("nan"), "max_drawdown": float("nan"), "hit_rate": float("nan")}
    avg = r.mean() * periods_per_year
    vol = r.std() * np.sqrt(periods_per_year)
    sharpe = avg / (vol + 1e-12)
    # max drawdown
    cum = (1 + r).cumprod()
    peak = cum.cummax()
    drawdown = (cum - peak) / (peak + 1e-12)
    max_dd = drawdown.min()
    hit_rate = float((r > 0).sum()) / len(r)
    return {"sharpe": float(sharpe), "volatility": float(vol), "max_drawdown": float(max_dd), "hit_rate": float(hit_rate)}


def simulate_trades_from_signals(price: pd.Series, signals: pd.Series, slippage: float = 0.0, transaction_cost: float = 0.0) -> pd.Series:
    """Convert position signals into strategy returns.

    signals: -1, 0, 1 position series. price: close price series.
    strategy_return_t = position_{t-1} * (price_t / price_{t-1} - 1) - costs
    """
    price = price.dropna().sort_index()
    signals = signals.reindex(price.index).ffill().fillna(0)
    rets = price.pct_change().fillna(0)
    pos = signals.shift(1).fillna(0)
    strategy_rets = pos * rets
    trades = pos.diff().abs().fillna(0)
    strategy_rets = strategy_rets - trades * transaction_cost - abs(pos) * slippage
    return strategy_rets


def simple_backtest(price: pd.Series, signals: pd.Series, periods_per_year: int = 252, **kwargs) -> Tuple[pd.Series, Dict[str, float]]:
    """Run a simple backtest and compute metrics.

    Returns (strategy_returns_series, metrics)
    """
    strat_rets = simulate_trades_from_signals(price, signals, **kwargs)
    metrics = compute_metrics(strat_rets, periods_per_year=periods_per_year)
    return strat_rets, metrics
