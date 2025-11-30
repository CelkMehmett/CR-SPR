"""Clean report generator (TF-free) for multi-stock benchmark.

This is a fresh, small script separate from the possibly corrupted `bench_multi_report.py`.
"""

import os
import glob
import pickle
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

np.random.seed(42)


def make_correlated_series(n_stocks=5, n=2000, base_noise=0.01):
    t = np.arange(n)
    base = 1.0 + 0.0005 * t + 0.02 * np.sin(2 * np.pi * t / 50)
    series = []
    for i in range(n_stocks):
        noise = base_noise * (1 + 0.5 * np.random.randn()) * np.random.randn(n)
        idio = 0.01 * np.sin(2 * np.pi * t / (50 + i * 5))
        series.append(base + idio + noise)
    return np.array(series)


def make_lag_features(series, lags=20):
    X = []
    y = []
    for i in range(lags, len(series)):
        X.append(series[i - lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)


def backtest_signals(price_series, preds):
    if len(preds) < 2:
        return np.array([]), np.array([])
    s = np.sign(preds[1:] - preds[:-1])
    ret = price_series[1:] - price_series[:-1]
    pnl = s * ret
    cum = np.cumsum(pnl)
    return cum, pnl


def load_persisted_models_for_stock(model_dir, stock_idx):
    pattern = os.path.join(model_dir, f"stock_{stock_idx}_*.pkl")
    files = sorted(glob.glob(pattern))
    models = {}
    for i, f in enumerate(files):
        try:
            with open(f, 'rb') as fh:
                m = pickle.load(fh)
            models[f'crispr_{i}'] = m
        except Exception:
            continue
    return models


def run(n_stocks=4, n=1200, lags=20, out_dir='reports_test', model_dir='bench_crispr_models'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks=n_stocks, n=n)
    rows = []

    for si in range(n_stocks):
        series = series_all[si]
        X, y = make_lag_features(series, lags=lags)
        split = int(0.7 * len(X))
        val_len = int(0.15 * len(X))
        X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
        y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)
        X_test_s = scaler.transform(X_test)

        lr = LinearRegression().fit(X_train_s, y_train)
        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)

        persist_test = X_test[:, -1]
        preds = {
            'persistence': persist_test,
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
        }

        # baseline ensemble via simple adaptive weights on validation
        preds_val = np.vstack([X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)])
        names = ['persistence', 'linear', 'rf']
        w = np.ones(len(names)) / len(names)
        alpha = 0.5
        for t in range(preds_val.shape[1]):
            p = preds_val[:, t]
            err = (p - y_val[t]) ** 2
            w = w * np.exp(-alpha * err)
            w = w / (w.sum() + 1e-12)
        baseline = (w[:, None] * np.vstack([preds[n] for n in names])).sum(axis=0)

        persisted = load_persisted_models_for_stock(model_dir, si)
        crispr_preds = dict(preds)
        crispr_names = list(names)
        for k, m in persisted.items():
            try:
                pt = m.predict(X_test_s)
            except Exception:
                try:
                    pt = m.predict(X_test)
                except Exception:
                    continue
            crispr_preds[k] = pt
            crispr_names.append(k)

        if len(crispr_names) > len(names):
            # simple equal-weight ensemble for augmented pool
            mat = np.vstack([crispr_preds[n] for n in crispr_names])
            crispr_ens = mat.mean(axis=0)
        else:
            crispr_ens = baseline

        price_series = series[split + val_len + lags: split + val_len + lags + len(baseline)]

        plt.figure(figsize=(8, 5))
        for n in names:
            cum, pnl = backtest_signals(price_series, preds[n])
            plt.plot(np.arange(len(cum)), cum, label=n)
            rows.append({'stock': f'stock_{si}', 'model': n, 'final_pnl': float(cum[-1]) if len(cum) else 0.0})

        cum_b, pnl_b = backtest_signals(price_series, baseline)
        plt.plot(np.arange(len(cum_b)), cum_b, label='baseline_ens', linewidth=2, color='k')
        rows.append({'stock': f'stock_{si}', 'model': 'baseline_ens', 'final_pnl': float(cum_b[-1]) if len(cum_b) else 0.0})

        cum_c, pnl_c = backtest_signals(price_series, crispr_ens)
        plt.plot(np.arange(len(cum_c)), cum_c, label='crispr_ens', linewidth=2, color='g')
        rows.append({'stock': f'stock_{si}', 'model': 'crispr_ens', 'final_pnl': float(cum_c[-1]) if len(cum_c) else 0.0})

        plt.legend()
        plt.title(f'stock_{si} cumulative PnL')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f'stock_{si}_pnl.png'))
        plt.close()

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, 'ensemble_pnl_detail.csv'), index=False)
    summary = df.groupby('model').agg(final_pnl_mean=('final_pnl', 'mean')).reset_index()
    summary.to_csv(os.path.join(out_dir, 'ensemble_pnl_summary.csv'), index=False)
    print('Wrote', out_dir)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--n-stocks', type=int, default=4)
    p.add_argument('--n', type=int, default=1200)
    p.add_argument('--lags', type=int, default=20)
    p.add_argument('--out-dir', default='reports_test')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
