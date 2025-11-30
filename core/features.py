"""Feature engineering helpers: returns, MA, RSI, z-score.

Biological note: transforms raw genetic material into interpretable features for the editor.
"""
from __future__ import annotations
import pandas as pd


def returns(series: pd.Series) -> pd.Series:
    return series.pct_change()


def sma(series: pd.Series, window: int = 20) -> pd.Series:
    return series.rolling(window).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / (down + 1e-9)
    return 100 - (100 / (1 + rs))


def zscore(series: pd.Series, window: int = 20) -> pd.Series:
    return (series - series.rolling(window).mean()) / (series.rolling(window).std() + 1e-9)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    # expects Close column
    price = df['Close']
    out = pd.DataFrame(index=df.index)
    out['ret'] = returns(price)
    out['sma_20'] = sma(price, 20)
    out['sma_50'] = sma(price, 50)
    out['rsi_14'] = rsi(price, 14)
    out['z_20'] = zscore(price, 20)
    return out.dropna()
