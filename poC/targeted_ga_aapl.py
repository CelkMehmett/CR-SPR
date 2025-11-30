"""Targeted GA runner: optimize AAPL ARIMA and RandomForest hyperparams.

Saves results to poc/scale_results_quick/ga_reports_targeted.jsonl and prints progress.
This script is defensive and prints helpful errors to stdout for debugging.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

def safe_import(name):
    try:
        mod = __import__(name)
        return mod
    except Exception as e:
        print(f"[import error] {name}: {e}")
        return None
# Ensure repository root is on sys.path so local package imports work when
# running this script directly (without PYTHONPATH set).
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from agents.editor_ga import SimpleGAEditor
from poc.compare_algorithms import download_yfinance
from src.eval.backtest import simple_backtest


def eval_arima_factory(price):
    def eval_arima(x):
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except Exception:
            print('[eval_arima] statsmodels unavailable')
            return -999.0
        p = int(np.clip(round(float(x[0])), 0, 5))
        d = int(np.clip(round(float(x[1])), 0, 2))
        q = int(np.clip(round(float(x[2])), 0, 5))
        ser = price.dropna()
        n = len(ser)
        if n < 60:
            return -999.0
        window = min(250, max(20, n // 2))
        signals = pd.Series(0, index=ser.index)
        for idx in range(window, n):
            train = ser.iloc[idx - window:idx]
            if len(train) < 10:
                continue
            try:
                model = ARIMA(train, order=(p, d, q))
                res = model.fit(method_kwargs={'warn_convergence': False})
                pred = res.forecast(steps=1)
                try:
                    pred_val = float(pred.iloc[0]) if hasattr(pred, 'iloc') else float(pred[0])
                except Exception:
                    try:
                        pred_val = float(pred[0])
                    except Exception:
                        continue
                last_obs = float(train.iloc[-1])
                if np.isfinite(pred_val):
                    try:
                        label = ser.index[idx]
                        signals.loc[label] = 1 if pred_val > last_obs else 0
                    except Exception:
                        signals.iloc[idx] = 1 if pred_val > last_obs else 0
            except Exception:
                continue
        rets, metrics = simple_backtest(price, signals, transaction_cost=0.0005, slippage=0.0001)
        sharpe = metrics.get('sharpe', -999.0)
        return float(sharpe if pd.notna(sharpe) else -999.0)

    return eval_arima


def eval_rf_factory(price):
    def eval_rf(x):
        try:
            from sklearn.ensemble import RandomForestClassifier
        except Exception:
            print('[eval_rf] scikit-learn unavailable')
            return -999.0
        n_est = int(np.clip(round(float(x[0])), 10, 500))
        max_d = int(np.clip(round(float(x[1])), 1, 50))
        s = price.copy()
        dfp = pd.DataFrame({'price': s})
        dfp['ret'] = dfp['price'].pct_change()
        for i in range(1, 11):
            dfp[f'lag_{i}'] = dfp['ret'].shift(i)
        dfp['sma_5'] = dfp['price'].rolling(5).mean()
        dfp['sma_20'] = dfp['price'].rolling(20).mean()
        dfp['sma_diff'] = dfp['sma_5'] - dfp['sma_20']
        dfp = dfp.dropna()
        if dfp.empty or len(dfp) < 50:
            return -999.0
        preds = pd.Series(0, index=dfp.index)
        features = [c for c in dfp.columns if c.startswith('lag_')] + ['sma_diff']
        min_train = 100
        min_train = min(min_train, max(20, int(len(dfp) * 0.5)))
        for i in range(min_train, len(dfp)):
            train_idx = dfp.index[:i]
            test_idx = dfp.index[i:i + 1]
            X_train = dfp.loc[train_idx, features].copy()
            y_train = (dfp['price'].shift(-1) > dfp['price']).astype(int).loc[train_idx]
            X_test = dfp.loc[test_idx, features].copy()
            valid_idx = X_train.dropna().index.intersection(y_train.dropna().index)
            X_train = X_train.loc[valid_idx]
            y_train = y_train.loc[valid_idx]
            if len(X_train) < 20:
                continue
            try:
                clf = RandomForestClassifier(n_estimators=n_est, max_depth=max_d, random_state=42)
                clf.fit(X_train.values, y_train.values)
                p = clf.predict(X_test.fillna(0).values)
                try:
                    val = int(p.item())
                except Exception:
                    try:
                        val = int(p[0])
                    except Exception:
                        val = int(p)
                preds.loc[test_idx] = val
            except Exception:
                continue
        sig = pd.Series(0, index=price.index)
        sig.loc[preds.index] = preds
        rets, metrics = simple_backtest(price, sig, transaction_cost=0.0005, slippage=0.0001)
        sharpe = metrics.get('sharpe', -999.0)
        return float(sharpe if pd.notna(sharpe) else -999.0)

    return eval_rf


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--symbol', default='AAPL')
    p.add_argument('--start', default='2023-01-01')
    p.add_argument('--end', default='2024-12-31')
    p.add_argument('--out', default='poc/scale_results_quick/ga_reports_targeted.jsonl')
    p.add_argument('--pop', type=int, default=30)
    p.add_argument('--gens', type=int, default=20)
    args = p.parse_args()

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = download_yfinance(args.symbol, args.start, args.end)
    except Exception as e:
        print(f'[error] failed to download price for {args.symbol}: {e}')
        sys.exit(1)

    if 'Close' not in df.columns:
        print('[error] Close column missing in downloaded data')
        sys.exit(1)

    price = df['Close'].sort_index()

    # prepare evaluators
    eval_arima = eval_arima_factory(price)
    eval_rf = eval_rf_factory(price)

    # Run GA for ARIMA
    try:
        editor_arima = SimpleGAEditor(num_genes=3, gene_space=[{'low':0,'high':5},{'low':0,'high':2},{'low':0,'high':5}], pop_size=args.pop, generations=args.gens)
        best_arima, fit_arima = editor_arima.edit(eval_arima)
    except Exception as e:
        print(f'[error] ARIMA GA failed: {e}')
        best_arima, fit_arima = None, None

    # Run GA for RF
    try:
        editor_rf = SimpleGAEditor(num_genes=2, gene_space=[{'low':10,'high':500},{'low':1,'high':50}], pop_size=args.pop, generations=args.gens)
        best_rf, fit_rf = editor_rf.edit(eval_rf)
    except Exception as e:
        print(f'[error] RF GA failed: {e}')
        best_rf, fit_rf = None, None

    # write report
    with outp.open('a') as f:
        if best_arima is not None:
            json.dump({'symbol': args.symbol, 'model': 'arima', 'best_sol': [int(round(float(v))) for v in best_arima.tolist()], 'best_fit': fit_arima}, f)
            f.write('\n')
        else:
            json.dump({'symbol': args.symbol, 'model': 'arima', 'error': True}, f); f.write('\n')

        if best_rf is not None:
            json.dump({'symbol': args.symbol, 'model': 'random_forest', 'best_sol': [int(round(float(best_rf[0]))), int(round(float(best_rf[1])))], 'best_fit': fit_rf}, f)
            f.write('\n')
        else:
            json.dump({'symbol': args.symbol, 'model': 'random_forest', 'error': True}, f); f.write('\n')

    print('Done. Results appended to', outp)


if __name__ == '__main__':
    main()
