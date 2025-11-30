"""Data loader for CSV/JSON OHLCV or indicator files.

Biological note: This module acts as the 'sequencer' reading the genome (data) for analysis.
"""
from __future__ import annotations
import pandas as pd


def load_csv(path: str, date_col: str = 'Date', parse_dates: bool = True) -> pd.DataFrame:
    df = pd.read_csv(path)
    if parse_dates and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
    return df


def load_json(path: str, date_col: str = 'Date') -> pd.DataFrame:
    df = pd.read_json(path)
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
    return df


def infer_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    # ensure common OHLCV columns exist; if not, try to infer them
    cols = [c.lower() for c in df.columns]
    mapping = {}
    for c in df.columns:
        lc = c.lower()
        if lc in ('open', 'o'):
            mapping[c] = 'Open'
        if lc in ('high', 'h'):
            mapping[c] = 'High'
        if lc in ('low', 'l'):
            mapping[c] = 'Low'
        if lc in ('close', 'c', 'adjclose', 'adj_close'):
            mapping[c] = 'Close'
        if lc in ('volume', 'v'):
            mapping[c] = 'Volume'
    return df.rename(columns=mapping)
