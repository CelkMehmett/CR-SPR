"""Tiny backtest evaluator for signals.

Biological note: evaluates edits' phenotypic effects on performance.
"""
from __future__ import annotations
from typing import Tuple, Dict
import pandas as pd


def simple_backtest(price: pd.Series, signal: pd.Series, transaction_cost: float = 0.0005, slippage: float = 0.0) -> Tuple[pd.Series, Dict[str, float]]:
    # align
    price = price.sort_index()
    sig = signal.reindex(price.index).fillna(0)
    pos = sig.shift(1).fillna(0)
    rets = price.pct_change().fillna(0)
    strat = pos * rets
    # subtract transaction costs on changes
    trades = pos.diff().abs()
    strat = strat - trades * transaction_cost - trades * slippage
    cum = (1 + strat).cumprod() - 1
    metrics = compute_metrics(strat)
    return cum, metrics


def compute_metrics(returns: pd.Series) -> Dict[str, float]:
    if returns is None or len(returns) == 0:
        return {'sharpe': float('nan'), 'volatility': float('nan'), 'win_rate': float('nan')}
    vol = returns.std() * (252 ** 0.5)
    mean = returns.mean() * 252
    sharpe = mean / (vol + 1e-9)
    win_rate = float((returns > 0).sum()) / max(1, len(returns))
    return {'sharpe': float(sharpe), 'volatility': float(vol), 'win_rate': float(win_rate)}
