"""
POC: Compare several prediction algorithms and report backtest metrics.

Algorithms included (lightweight/demo):
- Naive momentum (price > SMA20)
- ARIMA (statsmodels) -> forecasted signal
- RandomForest (scikit-learn) on windowed features

The script fetches data via yfinance (fallback) and runs `simple_backtest`.
Results are printed and saved to `poc/compare_results.csv` and returns per-symbol per-model as parquet.
"""

from __future__ import annotations
import os
import argparse
from typing import List

import pandas as pd
import numpy as np

from src.eval.backtest import simple_backtest
from src.detect.drift import performance_drift
from src.edit.simple_edits import smooth_signals


def download_yfinance(symbol: str, start: str, end: str) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(symbol, start=start, end=end, progress=False)
    return df


def naive_momentum_signal(price: pd.Series) -> pd.Series:
    sma = price.rolling(20).mean()
    return (price > sma).astype(int)


def arima_signal(price: pd.Series) -> pd.Series:
    """
    Walk-forward ARIMA signals: fit on rolling windows and predict next step.
    Falls back to zero signals if statsmodels not available.
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except Exception:
        return pd.Series(0, index=price.index)

    # coerce DataFrame -> Series if needed
    if isinstance(price, pd.DataFrame):
        if 'Close' in price.columns:
            price = price['Close']
        else:
            price = price.iloc[:, 0]

    price = price.dropna().copy()
    if price.empty:
        return pd.Series(0, index=price.index)

    # try to ensure a regular business-day index for statsmodels where possible
    try:
        if pd.infer_freq(price.index) is None:
            price = price.asfreq('B').ffill()
    except Exception:
        # if any issue, continue with original index
        pass

    n = len(price)
    if n < 60:
        return pd.Series(0, index=price.index)

    # walk-forward: train on rolling window of 250 bars (approx 1 year)
    window = min(250, max(20, n // 2))
    signals = pd.Series(0, index=price.index)

    # idx is the index position of the point we will predict (forecasted point)
    for idx in range(window, n):
        train = price.iloc[idx - window:idx]
        # robust null check (works for Series or DataFrame)
        if getattr(train, 'isnull', lambda: pd.Series(False))().values.any() or len(train) < 10:
            # not enough clean data
            continue
        try:
            model = ARIMA(train, order=(2, 1, 0))
            res = model.fit(method_kwargs={'warn_convergence': False})
            # forecast the next step (aligned to price.index[idx])
            pred = res.forecast(steps=1)
            # res.forecast may return ndarray/Series - use .iloc for Series access
            try:
                pred_val = float(pred.iloc[0]) if hasattr(pred, 'iloc') else float(pred[0])
            except Exception:
                pred_val = float(pred[0]) if hasattr(pred, '__len__') else float(pred)
            # compare forecast to last observed value (train last point)
            last_obs = float(train.iloc[-1])
            if np.isfinite(pred_val):
                # Map this forecast to the correct timestamp label instead of
                # relying on an inferred frequency. Use the existing price.index
                # label at position `idx` as the point we attempted to predict.
                try:
                    label = price.index[idx]
                    signals.loc[label] = 1 if pred_val > last_obs else 0
                except Exception:
                    # fallback to positional assignment
                    signals.iloc[idx] = 1 if pred_val > last_obs else 0
        except Exception:
            # leave default 0
            continue

    return signals.reindex(price.index).fillna(0)


def rf_signal(price: pd.Series) -> pd.Series:
    try:
        from sklearn.ensemble import RandomForestClassifier
    except Exception:
        return pd.Series(0, index=price.index)
    # coerce to 1D pandas Series and preserve index when possible
    orig_index = None
    # If it's a DataFrame with a Close column, prefer that
    if isinstance(price, pd.DataFrame):
        if 'Close' in price.columns:
            s = price['Close']
        else:
            # if single-column DataFrame, take first column
            if price.shape[1] == 1:
                s = price.iloc[:, 0]
            else:
                # can't handle multi-column directly
                s = price.iloc[:, 0]
        orig_index = s.index
        price_arr = np.asarray(s).squeeze()
    elif isinstance(price, pd.Series):
        orig_index = price.index
        price_arr = np.asarray(price).squeeze()
    else:
        arr = np.asarray(price)
        if arr.ndim == 2 and arr.shape[1] == 1:
            arr = arr.ravel()
        price_arr = arr.squeeze()
        orig_index = None

    # Build Series
    if orig_index is not None:
        price = pd.Series(price_arr, index=orig_index)
    else:
        price = pd.Series(price_arr)

    if price.empty or len(price) < 60:
        return pd.Series(0, index=price.index)

    # create features
    df = pd.DataFrame({'price': price})
    df['ret'] = df['price'].pct_change()
    for i in range(1, 11):
        df[f'lag_{i}'] = df['ret'].shift(i)
    df['sma_5'] = df['price'].rolling(5).mean()
    df['sma_20'] = df['price'].rolling(20).mean()
    df['sma_diff'] = df['sma_5'] - df['sma_20']
    df = df.dropna()

    if df.empty or len(df) < 50:
        return pd.Series(0, index=price.index)

    # walk-forward training: train on expanding window and predict next step
    preds = pd.Series(0, index=df.index)
    features = [c for c in df.columns if c.startswith('lag_')] + ['sma_diff']
    min_train = 100
    # ensure min_train is sensible relative to data
    min_train = min(min_train, max(20, int(len(df) * 0.5)))
    for i in range(min_train, len(df)):
        train_idx = df.index[:i]
        test_idx = df.index[i:i + 1]
        X_train = df.loc[train_idx, features].copy()
        y_train = (df['price'].shift(-1) > df['price']).astype(int).loc[train_idx]
        X_test = df.loc[test_idx, features].copy()

        # align and drop any problematic rows
        valid_idx = X_train.dropna().index.intersection(y_train.dropna().index)
        X_train = X_train.loc[valid_idx]
        y_train = y_train.loc[valid_idx]

        if len(X_train) < 20:
            # insufficient training data for this split
            continue

        try:
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X_train.values, y_train.values)
            p = clf.predict(X_test.fillna(0).values)
            # use .item() or .iloc[0] to avoid positional indexing deprecation
            try:
                val = int(p.item())
            except Exception:
                try:
                    val = int(p[0])
                except Exception:
                    val = int(p)
            preds.loc[test_idx] = val
        except Exception:
            # leave prediction as 0
            continue

    # align back to original index
    sig = pd.Series(0, index=price.index)
    sig.loc[preds.index] = preds
    return sig.fillna(0)


def crispr_adaptive_signal(price: pd.Series) -> pd.Series:
    """
    CRISPR-inspired adaptive signal: combines naive momentum with drift detection + repair.
    
    If drift is detected (performance_drift), applies smoothing to reduce signal noise.
    This is a simple proof-of-concept for a self-healing model.
    """
    # Start with naive momentum baseline
    sma = price.rolling(20).mean()
    sig = (price > sma).astype(int)

    # Detect drift on recent window
    is_drift, diag = performance_drift(price, recent_window=30, hist_window=120, threshold=0.15)

    if is_drift:
        # Apply smoothing repair when drift detected
        sig = smooth_signals(sig, window=5)

    return sig


def compare(symbols: List[str], start: str, end: str, out_dir: str = 'poc/results') -> pd.DataFrame:
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for s in symbols:
        df = download_yfinance(s, start, end)
        if 'Close' not in df.columns:
            print(f'No Close for {s}, skipping')
            continue

        # Extract a 1D Close price series for the symbol. yfinance may return
        # a MultiIndex columns DataFrame (Price, Ticker) or a DataFrame with
        # the ticker as column. Ensure `price` is a pandas Series indexed by Date.
        price = df['Close'].sort_index()
        if isinstance(price, pd.DataFrame):
            # Prefer the column matching the symbol
            if s in price.columns:
                price = price[s]
            else:
                # If it's a single-column DataFrame, squeeze it, otherwise try
                # to pick the first column as a fallback.
                if price.shape[1] == 1:
                    price = price.iloc[:, 0]
                else:
                    # try to handle MultiIndex columns like ('Close', 'AAPL') by
                    # selecting the second level matching the symbol
                    try:
                        price = price.xs(s, axis=1, level=1)
                    except Exception:
                        price = price.iloc[:, 0]

        # final coercion to 1D Series
        if isinstance(price, pd.DataFrame):
            price = price.iloc[:, 0]
        price = price.squeeze()

        models = {
            'naive_momentum': naive_momentum_signal,
            'arima': arima_signal,
            'random_forest': rf_signal,
            'crispr_adaptive': crispr_adaptive_signal,
        }

        for name, sig_fn in models.items():
            sig = sig_fn(price)
            # Ensure signal index matches price index exactly to avoid reindexing surprises
            try:
                sig = sig.reindex(price.index).ffill().fillna(0)
            except Exception:
                # fallback: coerce to same-length zero series
                sig = pd.Series(0, index=price.index)

            rets, metrics = simple_backtest(price, sig, transaction_cost=0.0005, slippage=0.0001)
            # Diagnostics: if returns empty or metrics are NaN, print quick info to help debug
            if rets.dropna().empty or any([pd.isna(v) for v in metrics.values()]):
                print(f"[diagnostic] model={name} symbol={s} rets_len={len(rets)} rets_nonzero={(rets!=0).sum()} ")
                print(f"[diagnostic] sig_len={len(sig)} sig_nonzero={(sig!=0).sum()} sig_index_first_last={sig.index[0]}..{sig.index[-1]}")
            rows.append({'symbol': s, 'model': name, **metrics})
            # save returns
            out_path = os.path.join(out_dir, f'{s}_{name}_returns.parquet')
            try:
                # support Series or DataFrame
                if isinstance(rets, pd.Series):
                    rets.to_frame('returns').to_parquet(out_path)
                elif isinstance(rets, pd.DataFrame):
                    rets.to_parquet(out_path)
                else:
                    pd.Series(rets).to_frame('returns').to_parquet(out_path)
            except Exception:
                # fallback CSV
                try:
                    if isinstance(rets, pd.Series):
                        rets.to_frame('returns').to_csv(out_path + '.csv')
                    elif isinstance(rets, pd.DataFrame):
                        rets.to_csv(out_path + '.csv')
                    else:
                        pd.Series(rets).to_frame('returns').to_csv(out_path + '.csv')
                except Exception:
                    # last resort: skip saving
                    pass

    res = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, 'compare_results.csv')
    res.to_csv(csv_path, index=False)
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--symbols', nargs='+', required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    args = p.parse_args()
    res = compare(args.symbols, args.start, args.end)
    print(res)


if __name__ == '__main__':
    main()
