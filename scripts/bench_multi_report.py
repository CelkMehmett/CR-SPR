"""Minimal TF-free report generator for the multi-stock benchmark.

This file is intentionally small and avoids TensorFlow/Keras. It trains
simple baselines (persistence, LinearRegression, RandomForest), optionally
loads persisted pickled models from ``model_dir`` (named like ``stock_<i>_*.pkl``),
and writes per-stock PNGs plus two CSVs in ``out_dir``.
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


def make_correlated_series(n_stocks, n):
    t = np.arange(n)
    base = 1.0 + 0.0005 * t + 0.02 * np.sin(2 * np.pi * t / 50)
    out = []
    for i in range(n_stocks):
        noise = 0.01 * np.random.randn(n)
        idio = 0.01 * np.sin(2 * np.pi * t / (50 + i * 5))
        out.append(base + idio + noise)
    return np.array(out)


def make_lag_features(series, lags):
    X, y = [], []
    for i in range(lags, len(series)):
        X.append(series[i - lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)


def backtest(price_series, preds):
    if len(preds) < 2:
        return 0.0
    s = np.sign(preds[1:] - preds[:-1])
    ret = price_series[1:] - price_series[:-1]
    return float(np.sum(s * ret))


def load_models(model_dir, stock_idx):
    pattern = os.path.join(model_dir, f"stock_{stock_idx}_*.pkl")
    files = sorted(glob.glob(pattern))
    out = []
    for f in files:
        try:
            with open(f, 'rb') as fh:
                out.append(pickle.load(fh))
        except Exception:
            continue
    return out


def run(n_stocks=4, n=1200, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks, n)
    rows = []

    for si in range(n_stocks):
        s = series_all[si]
        X, y = make_lag_features(s, lags)
        split = int(0.7 * len(X))
        val_len = int(0.15 * len(X))
        X_train, X_test = X[:split], X[split + val_len:]
        y_train, y_test = y[:split], y[split + val_len:]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        lr = LinearRegression().fit(X_train_s, y_train)
        rf = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train_s, y_train)

        preds = {
            'persistence': X_test[:, -1],
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
        }

        baseline = np.vstack([preds['persistence'], preds['linear'], preds['rf']]).mean(axis=0)

        persisted = load_models(model_dir, si)
        crispr_preds = []
        for m in persisted:
            try:
                crispr_preds.append(m.predict(X_test_s))
            except Exception:
                try:
                    crispr_preds.append(m.predict(X_test))
                except Exception:
                    continue

        if crispr_preds:
            crispr_ens = np.vstack([baseline] + crispr_preds).mean(axis=0)
        else:
            crispr_ens = baseline

        price_series = s[split + val_len + lags: split + val_len + lags + len(baseline)]

        for name, arr in [('persistence', preds['persistence']), ('linear', preds['linear']), ('rf', preds['rf']), ('baseline', baseline), ('crispr_ens', crispr_ens)]:
            pnl = np.sum(np.sign(arr[1:] - arr[:-1]) * (price_series[1:] - price_series[:-1])) if len(arr) > 1 else 0.0
            rows.append({'stock': f'stock_{si}', 'model': name, 'final_pnl': float(pnl)})

        plt.figure(figsize=(6, 4))
        for name, arr in [('persistence', preds['persistence']), ('linear', preds['linear']), ('rf', preds['rf']), ('baseline', baseline), ('crispr_ens', crispr_ens)]:
            if len(arr) > 1:
                cum = np.cumsum(np.sign(arr[1:] - arr[:-1]) * (price_series[1:] - price_series[:-1]))
            else:
                cum = np.array([0.0])
            plt.plot(cum, label=name)
        plt.legend()
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
    p.add_argument('--out-dir', default='reports')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
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

def make_correlated_series(n_stocks, n):
    t = np.arange(n)
    base = 1.0 + 0.0005 * t + 0.02 * np.sin(2 * np.pi * t / 50)
    out = []
    for i in range(n_stocks):
    noise = 0.01 * np.random.randn(n)
    idio = 0.01 * np.sin(2 * np.pi * t / (50 + i * 5))
    out.append(base + idio + noise)
    return np.array(out)

def make_lag_features(series, lags):
    X, y = [], []
    for i in range(lags, len(series)):
        X.append(series[i - lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)

def backtest(price_series, preds):
    if len(preds) < 2:
        return 0.0
    s = np.sign(preds[1:] - preds[:-1])
    ret = price_series[1:] - price_series[:-1]
    return float(np.sum(s * ret))

def load_models(model_dir, stock_idx):
    pattern = os.path.join(model_dir, f"stock_{stock_idx}_*.pkl")
    files = sorted(glob.glob(pattern))
    out = []
    for f in files:
        try:
            with open(f, 'rb') as fh:
                out.append(pickle.load(fh))
        except Exception:
            continue
    return out

def run(n_stocks=4, n=1200, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks, n)
    rows = []
    for si in range(n_stocks):
        s = series_all[si]
        X, y = make_lag_features(s, lags)
    split = int(0.7 * len(X))
    val_len = int(0.15 * len(X))
    X_train, X_test = X[:split], X[split + val_len:]
    y_train, y_test = y[:split], y[split + val_len:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    lr = LinearRegression().fit(X_train_s, y_train)
    rf = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train_s, y_train)

    preds = {
            'persistence': X_test[:, -1],
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
    }

    baseline = np.vstack([preds['persistence'], preds['linear'], preds['rf']]).mean(axis=0)
    persisted = load_models(model_dir, si)
    crispr_preds = []
    for m in persisted:
            try:
                crispr_preds.append(m.predict(X_test_s))
            except Exception:
                try:
                    crispr_preds.append(m.predict(X_test))
                except Exception:
                    continue

        if crispr_preds:
            crispr_ens = np.vstack([baseline] + crispr_preds).mean(axis=0)
        else:
            crispr_ens = baseline
    price_series = s[split + val_len + lags: split + val_len + lags + len(baseline)]

    for name, arr in [('persistence', preds['persistence']), ('linear', preds['linear']), ('rf', preds['rf']), ('baseline', baseline), ('crispr_ens', crispr_ens)]:
            pnl = np.sum(np.sign(arr[1:] - arr[:-1]) * (price_series[1:] - price_series[:-1])) if len(arr) > 1 else 0.0
            rows.append({'stock': f'stock_{si}', 'model': name, 'final_pnl': float(pnl)})

        plt.figure(figsize=(6, 4))
        for name, arr in [('persistence', preds['persistence']), ('linear', preds['linear']), ('rf', preds['rf']), ('baseline', baseline), ('crispr_ens', crispr_ens)]:
            if len(arr) > 1:
                cum = np.cumsum(np.sign(arr[1:] - arr[:-1]) * (price_series[1:] - price_series[:-1]))
            else:
                cum = np.array([0.0])
            plt.plot(cum, label=name)
    plt.legend()
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
    p.add_argument('--out-dir', default='reports')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
"""Minimal TF-free report generator for the multi-stock benchmark.

This file is intentionally small and avoids TensorFlow/Keras. It trains
simple baselines (persistence, LinearRegression, RandomForest), optionally
loads persisted pickled models from ``model_dir`` (named like ``stock_<i>_*.pkl``),
and writes per-stock PNGs plus two CSVs in ``out_dir``.
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


def make_correlated_series(n_stocks, n):
    t = np.arange(n)
    base = 1.0 + 0.0005 * t + 0.02 * np.sin(2 * np.pi * t / 50)
    out = []
    for i in range(n_stocks):
        noise = 0.01 * np.random.randn(n)
        idio = 0.01 * np.sin(2 * np.pi * t / (50 + i * 5))
        out.append(base + idio + noise)
    return np.array(out)


def make_lag_features(series, lags):
    X, y = [], []
    for i in range(lags, len(series)):
        X.append(series[i - lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)


def backtest(price_series, preds):
    if len(preds) < 2:
        return 0.0
    s = np.sign(preds[1:] - preds[:-1])
    ret = price_series[1:] - price_series[:-1]
    return float(np.sum(s * ret))


def load_models(model_dir, stock_idx):
    pattern = os.path.join(model_dir, f"stock_{stock_idx}_*.pkl")
    files = sorted(glob.glob(pattern))
    out = []
    for f in files:
        try:
            with open(f, 'rb') as fh:
                out.append(pickle.load(fh))
        except Exception:
            continue
    return out


def run(n_stocks=4, n=1200, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks, n)
    rows = []

    for si in range(n_stocks):
        s = series_all[si]
        X, y = make_lag_features(s, lags)
        split = int(0.7 * len(X))
        val_len = int(0.15 * len(X))
        X_train, X_test = X[:split], X[split + val_len:]
        y_train, y_test = y[:split], y[split + val_len:]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        lr = LinearRegression().fit(X_train_s, y_train)
        rf = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train_s, y_train)

        preds = {
            'persistence': X_test[:, -1],
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
        }

        baseline = np.vstack([preds['persistence'], preds['linear'], preds['rf']]).mean(axis=0)

        persisted = load_models(model_dir, si)
        crispr_preds = []
        for m in persisted:
            try:
                crispr_preds.append(m.predict(X_test_s))
            except Exception:
                try:
                    crispr_preds.append(m.predict(X_test))
                except Exception:
                    continue

        if crispr_preds:
            crispr_ens = np.vstack([baseline] + crispr_preds).mean(axis=0)
        else:
            crispr_ens = baseline

        price_series = s[split + val_len + lags: split + val_len + lags + len(baseline)]

        for name, arr in [('persistence', preds['persistence']), ('linear', preds['linear']), ('rf', preds['rf']), ('baseline', baseline), ('crispr_ens', crispr_ens)]:
            pnl = np.sum(np.sign(arr[1:] - arr[:-1]) * (price_series[1:] - price_series[:-1])) if len(arr) > 1 else 0.0
            rows.append({'stock': f'stock_{si}', 'model': name, 'final_pnl': float(pnl)})

        plt.figure(figsize=(6, 4))
        for name, arr in [('persistence', preds['persistence']), ('linear', preds['linear']), ('rf', preds['rf']), ('baseline', baseline), ('crispr_ens', crispr_ens)]:
            if len(arr) > 1:
                cum = np.cumsum(np.sign(arr[1:] - arr[:-1]) * (price_series[1:] - price_series[:-1]))
            else:
                cum = np.array([0.0])
            plt.plot(cum, label=name)
        plt.legend()
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
    p.add_argument('--out-dir', default='reports')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)

This entirely replaces the previous corrupted content. It purposely avoids
TensorFlow/Keras and other heavy deps so it runs reliably in minimal
environments. It trains simple baselines (persistence, linear, RF), loads
any persisted pickled CRISPR models from disk (if present), and writes
per-stock PNGs plus two CSVs in the output directory.
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


def make_correlated_series(n_stocks=4, n=1200, base_noise=0.01):
    t = np.arange(n)
    base = 1.0 + 0.0005 * t + 0.02 * np.sin(2 * np.pi * t / 50)
    out = []
    for i in range(n_stocks):
        noise = base_noise * np.random.randn(n)
        idio = 0.01 * np.sin(2 * np.pi * t / (50 + i * 5))
        out.append(base + idio + noise)
    return np.array(out)


def make_lag_features(series, lags=20):
    X, y = [], []
    for i in range(lags, len(series)):
        X.append(series[i - lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)


def backtest(price_series, preds):
    if len(preds) < 2:
        return 0.0
    s = np.sign(preds[1:] - preds[:-1])
    ret = price_series[1:] - price_series[:-1]
    return float(np.sum(s * ret))


def load_persisted_models(model_dir, stock_idx):
    pattern = os.path.join(model_dir, f"stock_{stock_idx}_*.pkl")
    files = sorted(glob.glob(pattern))
    models = []
    for f in files:
        try:
            with open(f, 'rb') as fh:
                models.append(pickle.load(fh))
        except Exception:
            continue
    return models


def run(n_stocks=4, n=1200, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
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
        rf = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train_s, y_train)

        preds = {
            'persistence': X_test[:, -1],
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
        }

        mat = np.vstack([preds['persistence'], preds['linear'], preds['rf']])
        baseline = mat.mean(axis=0)

        persisted = load_persisted_models(model_dir, si)
        crispr_preds = {}
        for i, m in enumerate(persisted):
            try:
                crispr_preds[f'crispr_{i}'] = m.predict(X_test_s)
            except Exception:
                try:
                    crispr_preds[f'crispr_{i}'] = m.predict(X_test)
                except Exception:
                    continue

        if crispr_preds:
            all_preds = np.vstack([baseline] + [v for v in crispr_preds.values()])
            crispr_ens = all_preds.mean(axis=0)
        else:
            crispr_ens = baseline

        price_series = series[split + val_len + lags: split + val_len + lags + len(baseline)]

        for name, arr in list(preds.items()) + [('baseline', baseline), ('crispr_ens', crispr_ens)]:
            final_pnl = backtest(price_series, arr)
            rows.append({'stock': f'stock_{si}', 'model': name, 'final_pnl': final_pnl})

        plt.figure(figsize=(6, 4))
        for name, arr in list(preds.items()) + [('baseline', baseline), ('crispr_ens', crispr_ens)]:
            cum = np.cumsum(np.sign(arr[1:] - arr[:-1]) * (price_series[1:] - price_series[:-1]))
            plt.plot(cum, label=name)
        plt.legend()
        plt.title(f'stock_{si} PnL')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f'stock_{si}_pnl.png'))
        plt.close()

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, 'ensemble_pnl_detail.csv'), index=False)
    summary = df.groupby('model').agg(final_pnl_mean=('final_pnl', 'mean')).reset_index()
    summary.to_csv(os.path.join(out_dir, 'ensemble_pnl_summary.csv'), index=False)
    print('Wrote', out_dir)
"""Minimal clean report generator for the multi-stock benchmark (TF-free).

Produces per-stock PNGs and two CSVs: ensemble_pnl_summary.csv and ensemble_pnl_detail.csv.
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


def run(n_stocks=4, n=1200, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
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

        # simple validation-trained weights
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
    p.add_argument('--out-dir', default='reports')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
"""Clean report generator (TF-free) for multi-stock benchmark.

This is a fresh, small script replacing a corrupted previous version.
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
"""Minimal report generator for the multi-stock benchmark (single clean copy).

This file intentionally small and TF-free to avoid earlier corruption. It trains a few
baseline models and compares baseline ensemble vs. CRISPR-persisted models if any exist.
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


class AdaptiveEnsemble:
    def __init__(self, model_names, eta=1.0):
        self.model_names = list(model_names)
        self.eta = eta
        self.w = np.ones(len(self.model_names)) / len(self.model_names)

    def update(self, preds_matrix, y_true):
        errs = np.mean((preds_matrix - y_true.reshape(1, -1)) ** 2, axis=1)
        self.w = self.w * np.exp(-self.eta * errs)
        self.w = self.w / (np.sum(self.w) + 1e-12)

    def predict(self, preds_matrix):
        return np.dot(self.w, preds_matrix)


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


def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks=n_stocks, n=n)

    aggregate = []

    for si in range(n_stocks):
        series = series_all[si]
        X, y = make_lag_features(series, lags=lags)
        split = int(0.7 * len(X))
        val_len = int(0.15 * len(X))
        X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
        y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

        persist_test = X_test[:, -1]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)
        X_test_s = scaler.transform(X_test)

        lr = LinearRegression().fit(X_train_s, y_train)
        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)

        preds = {
            'persistence': persist_test,
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
        }
        preds_val = [X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)]
        model_order = ['persistence', 'linear', 'rf']

        preds_val = np.vstack(preds_val)

        ens = AdaptiveEnsemble(model_order, eta=1.0)
        chunk = 20
        for start in range(0, preds_val.shape[1], chunk):
            end = min(start + chunk, preds_val.shape[1])
            ens.update(preds_val[:, start:end], y_val[start:end])
        baseline_ens_preds = ens.predict(np.vstack([preds[k] for k in model_order]))

        persisted = load_persisted_models_for_stock(model_dir, si)
        crispr_preds = dict(preds)
        crispr_model_names = list(model_order)
        crispr_preds_val_list = [preds_val[i] for i in range(preds_val.shape[0])]

        for name, m in persisted.items():
            try:
                pv = m.predict(X_val_s)
                pt = m.predict(X_test_s)
            except Exception:
                try:
                    pv = m.predict(X_val)
                    pt = m.predict(X_test)
                except Exception:
                    continue
            crispr_preds[name] = pt
            crispr_preds_val_list.append(pv)
            crispr_model_names.append(name)

        if len(crispr_model_names) > len(model_order):
            preds_val_all = np.vstack(crispr_preds_val_list)
            ens_crispr = AdaptiveEnsemble(crispr_model_names, eta=1.0)
            for start in range(0, preds_val_all.shape[1], chunk):
                end = min(start + chunk, preds_val_all.shape[1])
                ens_crispr.update(preds_val_all[:, start:end], y_val[start:end])
            crispr_ens_preds = ens_crispr.predict(np.vstack([crispr_preds[n] for n in crispr_model_names]))
        else:
            crispr_ens_preds = baseline_ens_preds
            crispr_model_names = model_order

        plt.figure(figsize=(8, 5))
        T = len(list(preds.values())[0])
        price_series = series[split + val_len + lags: split + val_len + lags + T]

        for name in model_order:
            arr = preds[name]
            cum, pnl = backtest_signals(price_series, arr)
            plt.plot(np.arange(len(cum)), cum, label=f'b_{name}')
            aggregate.append({'stock': f'stock_{si}', 'model': f'b_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

        cum_b, pnl_b = backtest_signals(price_series, baseline_ens_preds)
        plt.plot(np.arange(len(cum_b)), cum_b, label='b_ensemble', linewidth=2, color='black')
        aggregate.append({'stock': f'stock_{si}', 'model': 'b_ensemble', 'final_pnl': float(cum_b[-1]) if len(cum_b) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_b)) if len(pnl_b) > 0 else 0.0})

        for name in crispr_model_names:
            if name in crispr_preds:
                arr = crispr_preds[name]
                cum, pnl = backtest_signals(price_series, arr)
                plt.plot(np.arange(len(cum)), cum, linestyle='--', label=f'c_{name}')
                aggregate.append({'stock': f'stock_{si}', 'model': f'c_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

        cum_c, pnl_c = backtest_signals(price_series, crispr_ens_preds)
        plt.plot(np.arange(len(cum_c)), cum_c, label='c_ensemble', linewidth=2, color='tab:green')
        aggregate.append({'stock': f'stock_{si}', 'model': 'c_ensemble', 'final_pnl': float(cum_c[-1]) if len(cum_c) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_c)) if len(pnl_c) > 0 else 0.0})

        plt.legend()
        plt.title(f'stock_{si} cumulative PnL: baseline (b_) vs crispr (c_)')
        plt.xlabel('time')
        plt.ylabel('cumulative PnL')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f'stock_{si}_pnl.png'))
        plt.close()

    df = pd.DataFrame(aggregate)
    summary = df.groupby('model').agg(final_pnl_mean=('final_pnl', 'mean'), final_pnl_std=('final_pnl', 'std')).reset_index()
    summary.to_csv(os.path.join(out_dir, 'ensemble_pnl_summary.csv'), index=False)
    df.to_csv(os.path.join(out_dir, 'ensemble_pnl_detail.csv'), index=False)
    print('Wrote reports to', out_dir)
    print(summary)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--n-stocks', type=int, default=8)
    p.add_argument('--n', type=int, default=2500)
    p.add_argument('--lags', type=int, default=20)
    p.add_argument('--out-dir', default='reports')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run_report(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
"""Minimal report generator for the multi-stock benchmark.

Trains simple baseline models and compares baseline ensemble vs ensemble augmented with persisted CRISPR models
located in `model_dir` (pickles named like stock_<i>_*.pkl).

Outputs per-stock PNGs and two CSVs in out_dir.
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


class AdaptiveEnsemble:
    def __init__(self, model_names, eta=1.0):
        self.model_names = list(model_names)
        self.eta = eta
        self.w = np.ones(len(self.model_names)) / len(self.model_names)

    def update(self, preds_matrix, y_true):
        errs = np.mean((preds_matrix - y_true.reshape(1, -1)) ** 2, axis=1)
        self.w = self.w * np.exp(-self.eta * errs)
        self.w = self.w / (np.sum(self.w) + 1e-12)

    def predict(self, preds_matrix):
        return np.dot(self.w, preds_matrix)


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


def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks=n_stocks, n=n)

    aggregate = []

    for si in range(n_stocks):
        series = series_all[si]
        X, y = make_lag_features(series, lags=lags)
        split = int(0.7 * len(X))
        val_len = int(0.15 * len(X))
        X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
        y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

        persist_test = X_test[:, -1]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)
        X_test_s = scaler.transform(X_test)

        lr = LinearRegression().fit(X_train_s, y_train)
        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)

        preds = {
            'persistence': persist_test,
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
        }
        preds_val = [X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)]
        model_order = ['persistence', 'linear', 'rf']

        preds_val = np.vstack(preds_val)

        ens = AdaptiveEnsemble(model_order, eta=1.0)
        chunk = 20
        for start in range(0, preds_val.shape[1], chunk):
            end = min(start + chunk, preds_val.shape[1])
            ens.update(preds_val[:, start:end], y_val[start:end])
        baseline_ens_preds = ens.predict(np.vstack([preds[k] for k in model_order]))

        persisted = load_persisted_models_for_stock(model_dir, si)
        crispr_preds = dict(preds)
        crispr_model_names = list(model_order)
        crispr_preds_val_list = [preds_val[i] for i in range(preds_val.shape[0])]

        for name, m in persisted.items():
            try:
                pv = m.predict(X_val_s)
                pt = m.predict(X_test_s)
            except Exception:
                try:
                    pv = m.predict(X_val)
                    pt = m.predict(X_test)
                except Exception:
                    continue
            crispr_preds[name] = pt
            crispr_preds_val_list.append(pv)
            crispr_model_names.append(name)

        if len(crispr_model_names) > len(model_order):
            preds_val_all = np.vstack(crispr_preds_val_list)
            ens_crispr = AdaptiveEnsemble(crispr_model_names, eta=1.0)
            for start in range(0, preds_val_all.shape[1], chunk):
                end = min(start + chunk, preds_val_all.shape[1])
                ens_crispr.update(preds_val_all[:, start:end], y_val[start:end])
            crispr_ens_preds = ens_crispr.predict(np.vstack([crispr_preds[n] for n in crispr_model_names]))
        else:
            crispr_ens_preds = baseline_ens_preds
            crispr_model_names = model_order

        plt.figure(figsize=(8, 5))
        T = len(list(preds.values())[0])
        price_series = series[split + val_len + lags: split + val_len + lags + T]

        for name in model_order:
            arr = preds[name]
            cum, pnl = backtest_signals(price_series, arr)
            plt.plot(np.arange(len(cum)), cum, label=f'b_{name}')
            aggregate.append({'stock': f'stock_{si}', 'model': f'b_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

        cum_b, pnl_b = backtest_signals(price_series, baseline_ens_preds)
        plt.plot(np.arange(len(cum_b)), cum_b, label='b_ensemble', linewidth=2, color='black')
        aggregate.append({'stock': f'stock_{si}', 'model': 'b_ensemble', 'final_pnl': float(cum_b[-1]) if len(cum_b) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_b)) if len(pnl_b) > 0 else 0.0})

        for name in crispr_model_names:
            if name in crispr_preds:
                arr = crispr_preds[name]
                cum, pnl = backtest_signals(price_series, arr)
                plt.plot(np.arange(len(cum)), cum, linestyle='--', label=f'c_{name}')
                aggregate.append({'stock': f'stock_{si}', 'model': f'c_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

        cum_c, pnl_c = backtest_signals(price_series, crispr_ens_preds)
        plt.plot(np.arange(len(cum_c)), cum_c, label='c_ensemble', linewidth=2, color='tab:green')
        aggregate.append({'stock': f'stock_{si}', 'model': 'c_ensemble', 'final_pnl': float(cum_c[-1]) if len(cum_c) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_c)) if len(pnl_c) > 0 else 0.0})

        plt.legend()
        plt.title(f'stock_{si} cumulative PnL: baseline (b_) vs crispr (c_)')
        plt.xlabel('time')
        plt.ylabel('cumulative PnL')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f'stock_{si}_pnl.png'))
        plt.close()

    df = pd.DataFrame(aggregate)
    summary = df.groupby('model').agg(final_pnl_mean=('final_pnl', 'mean'), final_pnl_std=('final_pnl', 'std')).reset_index()
    summary.to_csv(os.path.join(out_dir, 'ensemble_pnl_summary.csv'), index=False)
    df.to_csv(os.path.join(out_dir, 'ensemble_pnl_detail.csv'), index=False)
    print('Wrote reports to', out_dir)
    print(summary)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--n-stocks', type=int, default=8)
    p.add_argument('--n', type=int, default=2500)
    p.add_argument('--lags', type=int, default=20)
    p.add_argument('--out-dir', default='reports')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run_report(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
"""Generate PnL backtests and reports for multi-stock benchmark.

Minimal, TF-free implementation to avoid earlier indentation/runtime issues.
Trains baseline models (persistence, linear, RF, optional XGBoost) and compares baseline
ensemble vs ensemble augmented with persisted CRISPR models found in `model_dir`.

Produces per-stock PNGs and two CSVs: ensemble_pnl_summary.csv and ensemble_pnl_detail.csv.
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

try:
    import xgboost as xgb
except Exception:
    xgb = None

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


class AdaptiveEnsemble:
    def __init__(self, model_names, eta=1.0):
        self.model_names = list(model_names)
        self.eta = eta
        self.w = np.ones(len(self.model_names)) / len(self.model_names)

    def update(self, preds_matrix, y_true):
        errs = np.mean((preds_matrix - y_true.reshape(1, -1)) ** 2, axis=1)
        self.w = self.w * np.exp(-self.eta * errs)
        self.w = self.w / (np.sum(self.w) + 1e-12)

    def predict(self, preds_matrix):
        return np.dot(self.w, preds_matrix)


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


def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks=n_stocks, n=n)

    aggregate = []

    for si in range(n_stocks):
        series = series_all[si]
        X, y = make_lag_features(series, lags=lags)
        split = int(0.7 * len(X))
        val_len = int(0.15 * len(X))
        X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
        y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

        persist_test = X_test[:, -1]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)
        X_test_s = scaler.transform(X_test)

        lr = LinearRegression().fit(X_train_s, y_train)
        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)

        xg = None
        if xgb is not None:
            try:
                xg = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0).fit(X_train_s, y_train)
            except Exception:
                xg = None

        preds = {
            'persistence': persist_test,
            'linear': lr.predict(X_test_s),
            'rf': rf.predict(X_test_s)
        }
        preds_val = [X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)]
        model_order = ['persistence', 'linear', 'rf']

        if xg is not None:
            preds['xg'] = xg.predict(X_test_s)
            preds_val.append(xg.predict(X_val_s))
            model_order.append('xg')

        preds_val = np.vstack(preds_val)

        ens = AdaptiveEnsemble(model_order, eta=1.0)
        chunk = 20
        for start in range(0, preds_val.shape[1], chunk):
            end = min(start + chunk, preds_val.shape[1])
            ens.update(preds_val[:, start:end], y_val[start:end])
        baseline_ens_preds = ens.predict(np.vstack([preds[k] for k in model_order]))

        persisted = load_persisted_models_for_stock(model_dir, si)
        crispr_preds = dict(preds)
        crispr_model_names = list(model_order)
        crispr_preds_val_list = [preds_val[i] for i in range(preds_val.shape[0])]

        for name, m in persisted.items():
            try:
                pv = m.predict(X_val_s)
                pt = m.predict(X_test_s)
            except Exception:
                try:
                    pv = m.predict(X_val)
                    pt = m.predict(X_test)
                except Exception:
                    continue
            crispr_preds[name] = pt
            crispr_preds_val_list.append(pv)
            crispr_model_names.append(name)

        if len(crispr_model_names) > len(model_order):
            preds_val_all = np.vstack(crispr_preds_val_list)
            ens_crispr = AdaptiveEnsemble(crispr_model_names, eta=1.0)
            for start in range(0, preds_val_all.shape[1], chunk):
                end = min(start + chunk, preds_val_all.shape[1])
                ens_crispr.update(preds_val_all[:, start:end], y_val[start:end])
            crispr_ens_preds = ens_crispr.predict(np.vstack([crispr_preds[n] for n in crispr_model_names]))
        else:
            crispr_ens_preds = baseline_ens_preds
            crispr_model_names = model_order

        plt.figure(figsize=(10, 6))
        T = len(list(preds.values())[0])
        price_series = series[split + val_len + lags: split + val_len + lags + T]

        for name in model_order:
            arr = preds[name]
            cum, pnl = backtest_signals(price_series, arr)
            plt.plot(np.arange(len(cum)), cum, label=f'b_{name}')
            aggregate.append({'stock': f'stock_{si}', 'model': f'b_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

        cum_b, pnl_b = backtest_signals(price_series, baseline_ens_preds)
        plt.plot(np.arange(len(cum_b)), cum_b, label='b_ensemble', linewidth=2, color='black')
        aggregate.append({'stock': f'stock_{si}', 'model': 'b_ensemble', 'final_pnl': float(cum_b[-1]) if len(cum_b) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_b)) if len(pnl_b) > 0 else 0.0})

        for name in crispr_model_names:
            if name in crispr_preds:
                arr = crispr_preds[name]
                cum, pnl = backtest_signals(price_series, arr)
                plt.plot(np.arange(len(cum)), cum, linestyle='--', label=f'c_{name}')
                aggregate.append({'stock': f'stock_{si}', 'model': f'c_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

        cum_c, pnl_c = backtest_signals(price_series, crispr_ens_preds)
        plt.plot(np.arange(len(cum_c)), cum_c, label='c_ensemble', linewidth=2, color='tab:green')
        aggregate.append({'stock': f'stock_{si}', 'model': 'c_ensemble', 'final_pnl': float(cum_c[-1]) if len(cum_c) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_c)) if len(pnl_c) > 0 else 0.0})

        plt.legend()
        plt.title(f'stock_{si} cumulative PnL: baseline (b_) vs crispr (c_)')
        plt.xlabel('time')
        plt.ylabel('cumulative PnL')
        plt.grid(False)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f'stock_{si}_pnl.png'))
        plt.close()

    df = pd.DataFrame(aggregate)
    summary = df.groupby('model').agg(final_pnl_mean=('final_pnl', 'mean'), final_pnl_std=('final_pnl', 'std')).reset_index()
    summary.to_csv(os.path.join(out_dir, 'ensemble_pnl_summary.csv'), index=False)
    df.to_csv(os.path.join(out_dir, 'ensemble_pnl_detail.csv'), index=False)
    print('Wrote reports to', out_dir)
    print(summary)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--n-stocks', type=int, default=8)
    p.add_argument('--n', type=int, default=2500)
    p.add_argument('--lags', type=int, default=20)
    p.add_argument('--out-dir', default='reports')
    p.add_argument('--model-dir', default='bench_crispr_models')
    args = p.parse_args()
    run_report(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
"""Generate plots and simple PnL backtests for the multi-stock benchmark.

This script re-runs the data generation and model predictions (same config as bench_multi_stocks)
and computes a one-step-ahead directional strategy PnL for each model and the adaptive ensemble.
Saves CSV summary and PNG plots per stock and an aggregate plot.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler

np.random.seed(42)


def make_correlated_series(n_stocks=5, n=2000, base_noise=0.01):
    t = np.arange(n)
    base = 1.0 + 0.0005 * t + 0.02 * np.sin(2 * np.pi * t / 50)
    series = []
    for i in range(n_stocks):
        noise = base_noise * (1 + 0.5 * np.random.randn()) * np.random.randn(n)
        idio = 0.01 * np.sin(2 * np.pi * t / (50 + i*5))
        series.append(base + idio + noise)
    return np.array(series)


def make_lag_features(series, lags=20):
    X = []
    y = []
    for i in range(lags, len(series)):
        X.append(series[i-lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)


class AdaptiveEnsemble:
    def __init__(self, model_names, eta=1.0):
        self.model_names = list(model_names)
        self.eta = eta
        self.w = np.ones(len(self.model_names)) / len(self.model_names)

    def update(self, preds_matrix, y_true):
        errs = np.mean((preds_matrix - y_true.reshape(1, -1))**2, axis=1)
        self.w = self.w * np.exp(-self.eta * errs)
        self.w = self.w / (np.sum(self.w) + 1e-12)

    def predict(self, preds_matrix):
        return np.dot(self.w, preds_matrix)


def backtest_signals(price_series, preds):
    # preds: array of predictions aligned with price_series indices (length T)
    # Generate signals s_t = sign(pred_t - price_t) (one-step ahead approach)
    # PnL per step: s_t * (price_{t+1} - price_t). Return cumulative PnL (len T-1)
    s = np.sign(preds[1:] - preds[:-1])
    ret = price_series[1+0:] - price_series[:-1]
    pnl = s * ret
    cum = np.cumsum(pnl)
    return cum, pnl


def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports'):
    os.makedirs(out_dir, exist_ok=True)
    series_all = make_correlated_series(n_stocks=n_stocks, n=n)

    aggregate = []

    for si in range(n_stocks):
        series = series_all[si]
        X, y = make_lag_features(series, lags=lags)
        split = int(0.7 * len(X))
        val_len = int(0.15 * len(X))
        X_train, X_val, X_test = X[:split], X[split:split+val_len], X[split+val_len:]
        y_train, y_val, y_test = y[:split], y[split:split+val_len], y[split+val_len:]

        # persistence
        persist_test = X_test[:, -1]

    # Standardize features per-stock
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    lr = LinearRegression().fit(X_train_s, y_train)
    rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)
    xg = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0).fit(X_train_s, y_train)

    X_train_l = X_train_s.reshape((X_train_s.shape[0], X_train_s.shape[1], 1))
    X_val_l = X_val_s.reshape((X_val_s.shape[0], X_val_s.shape[1], 1))
    X_test_l = X_test_s.reshape((X_test_s.shape[0], X_test_s.shape[1], 1))
        model = keras.Sequential([
            keras.layers.Input(shape=(lags, 1)),
            keras.layers.LSTM(32, activation='tanh'),
            keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
    model.fit(X_train_l, y_train, epochs=10, batch_size=64, verbose=0)
        lstm_test = model.predict(X_test_l).flatten()

        preds = {
            'persistence': persist_test,
            'linear': lr.predict(X_test),
            'rf': rf.predict(X_test),
            'xg': xg.predict(X_test),
            'lstm': lstm_test
        }

        # ensemble trained on validation
        preds_val = np.vstack([persist_test[:len(X_val)], lr.predict(X_val), rf.predict(X_val), xg.predict(X_val), model.predict(X_val_l).flatten()])
        ens = AdaptiveEnsemble(list(preds.keys()), eta=1.0)
        # update in chunks
        chunk = 20
        for start in range(0, preds_val.shape[1], chunk):
            end = min(start+chunk, preds_val.shape[1])
            ens.update(preds_val[:, start:end], y_val[start:end])
        preds['ensemble'] = ens.predict(np.vstack([preds[k] for k in ['persistence','linear','rf','xg','lstm']]))

        # Backtest per model
        T = len(preds['linear'])
        price_idx = np.arange(T+lags, T+lags+T)  # align to original series indices
        price_series = series[split+val_len+lags:split+val_len+lags+T]

        plt.figure(figsize=(10,6))
        for name, arr in preds.items():
            cum, pnl = backtest_signals(price_series, arr)
            plt.plot(np.arange(len(cum)), cum, label=name)
            aggregate.append({'stock': f'stock_{si}', 'model': name, 'final_pnl': float(cum[-1]) if len(cum)>0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl)>0 else 0.0})
        plt.legend()
        plt.title(f'stock_{si} cumulative PnL per model')
        plt.xlabel('time')
        plt.ylabel('cumulative PnL')
        plt.grid(False)
        plt.tight_layout()
        """Generate plots and simple PnL backtests for the multi-stock benchmark.

        This script re-runs the data generation and model predictions (same config as bench_multi_stocks)
        and computes a one-step-ahead directional strategy PnL for each model and two ensembles:
         - baseline ensemble trained from built-in models
         - crispr ensemble which augments the baseline with persisted CRISPR-accepted models from disk

        Saves CSV summary and PNG plots per stock and an aggregate CSV.
        """
        import os
        import glob
        import pickle
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_squared_error
        from sklearn.preprocessing import StandardScaler

        try:
            import xgboost as xgb
        except Exception:
            xg = None

        try:
            import tensorflow as tf
            from tensorflow import keras
            tf_available = True
        except Exception:
            tf_available = False

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


        class AdaptiveEnsemble:
            def __init__(self, model_names, eta=1.0):
                self.model_names = list(model_names)
                self.eta = eta
                self.w = np.ones(len(self.model_names)) / len(self.model_names)

            def update(self, preds_matrix, y_true):
                errs = np.mean((preds_matrix - y_true.reshape(1, -1)) ** 2, axis=1)
                self.w = self.w * np.exp(-self.eta * errs)
                self.w = self.w / (np.sum(self.w) + 1e-12)

            def predict(self, preds_matrix):
                return np.dot(self.w, preds_matrix)


        def backtest_signals(price_series, preds):
            # preds: array of predictions aligned with price_series indices (length T)
            # Generate signals s_t = sign(pred_t - price_t) (one-step ahead approach)
            # PnL per step: s_t * (price_{t+1} - price_t). Return cumulative PnL (len T-1)
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


        def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
            os.makedirs(out_dir, exist_ok=True)
            series_all = make_correlated_series(n_stocks=n_stocks, n=n)

            aggregate = []

            for si in range(n_stocks):
                series = series_all[si]
                X, y = make_lag_features(series, lags=lags)
                split = int(0.7 * len(X))
                val_len = int(0.15 * len(X))
                X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
                y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

                # persistence baseline
                persist_test = X_test[:, -1]

                # Standardize features per-stock
                scaler = StandardScaler()
                X_train_s = scaler.fit_transform(X_train)
                X_val_s = scaler.transform(X_val)
                X_test_s = scaler.transform(X_test)

                # Train baseline models
                lr = LinearRegression().fit(X_train_s, y_train)
                rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)
                if xgb is not None:
                    xg = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0).fit(X_train_s, y_train)
                else:
                    xg = None

                # LSTM baseline if available
                if tf_available:
                    X_train_l = X_train_s.reshape((X_train_s.shape[0], X_train_s.shape[1], 1))
                    X_val_l = X_val_s.reshape((X_val_s.shape[0], X_val_s.shape[1], 1))
                    X_test_l = X_test_s.reshape((X_test_s.shape[0], X_test_s.shape[1], 1))
                    model = keras.Sequential([
                        keras.layers.Input(shape=(lags, 1)),
                        keras.layers.LSTM(32, activation='tanh'),
                        keras.layers.Dense(1)
                    ])
                    model.compile(optimizer='adam', loss='mse')
                    model.fit(X_train_l, y_train, epochs=5, batch_size=64, verbose=0)
                    lstm_test = model.predict(X_test_l).flatten()
                    lstm_val = model.predict(X_val_l).flatten()
                else:
                    lstm_test = None
                    lstm_val = None

                # Build baseline predictions dict
                preds = {
                    'persistence': persist_test,
                    'linear': lr.predict(X_test_s),
                    'rf': rf.predict(X_test_s)
                }
                preds_val = [X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)]
                model_order = ['persistence', 'linear', 'rf']
                if xg is not None:
                    preds['xg'] = xg.predict(X_test_s)
                    preds_val.append(xg.predict(X_val_s))
                    model_order.append('xg')
                if lstm_test is not None:
                    preds['lstm'] = lstm_test
                    preds_val.append(lstm_val)
                    model_order.append('lstm')

                preds_val = np.vstack(preds_val)

                # Baseline ensemble trained on validation
                ens = AdaptiveEnsemble(model_order, eta=1.0)
                chunk = 20
                for start in range(0, preds_val.shape[1], chunk):
                    end = min(start + chunk, preds_val.shape[1])
                    ens.update(preds_val[:, start:end], y_val[start:end])
                baseline_ens_preds = ens.predict(np.vstack([preds[k] for k in model_order]))

                # Load persisted CRISPR models and add into candidate pool
                persisted = load_persisted_models_for_stock(model_dir, si)
                crispr_preds = dict(preds)  # copy baseline preds
                crispr_model_names = list(model_order)
                crispr_preds_val_list = [preds_val[i] for i in range(preds_val.shape[0])]

                for name, m in persisted.items():
                    try:
                        # predictions on val/test (note: some wrappers expect original scaled features)
                        # attempt using scaled features first
                        pv = m.predict(X_val_s)
                        pt = m.predict(X_test_s)
                    except Exception:
                        try:
                            pv = m.predict(X_val)
                            pt = m.predict(X_test)
                        except Exception:
                            # skip models that cannot predict
                            continue
                    crispr_preds[name] = pt
                    crispr_preds_val_list.append(pv)
                    crispr_model_names.append(name)

                # If there are extra persisted models, compute crispr ensemble weights
                if len(crispr_model_names) > len(model_order):
                    preds_val_all = np.vstack(crispr_preds_val_list)
                    ens_crispr = AdaptiveEnsemble(crispr_model_names, eta=1.0)
                    for start in range(0, preds_val_all.shape[1], chunk):
                        end = min(start + chunk, preds_val_all.shape[1])
                        ens_crispr.update(preds_val_all[:, start:end], y_val[start:end])
                    crispr_ens_preds = ens_crispr.predict(np.vstack([crispr_preds[n] for n in crispr_model_names]))
                else:
                    crispr_ens_preds = baseline_ens_preds
                    crispr_model_names = model_order

                # Backtest per model and both ensembles
                plt.figure(figsize=(10, 6))
                # align price series for backtest
                T = len(list(preds.values())[0])
                price_series = series[split + val_len + lags: split + val_len + lags + T]

                # baseline models and baseline ensemble
                for name in model_order:
                    arr = preds[name]
                    cum, pnl = backtest_signals(price_series, arr)
                    plt.plot(np.arange(len(cum)), cum, label=f'b_{name}')
                    aggregate.append({'stock': f'stock_{si}', 'model': f'b_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                cum_b, pnl_b = backtest_signals(price_series, baseline_ens_preds)
                plt.plot(np.arange(len(cum_b)), cum_b, label='b_ensemble', linewidth=2, color='black')
                aggregate.append({'stock': f'stock_{si}', 'model': 'b_ensemble', 'final_pnl': float(cum_b[-1]) if len(cum_b) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_b)) if len(pnl_b) > 0 else 0.0})

                # CRISPR-augmented models / ensemble
                for name in crispr_model_names:
                    if name in crispr_preds:
                        arr = crispr_preds[name]
                        cum, pnl = backtest_signals(price_series, arr)
                        plt.plot(np.arange(len(cum)), cum, linestyle='--', label=f'c_{name}')
                        aggregate.append({'stock': f'stock_{si}', 'model': f'c_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                cum_c, pnl_c = backtest_signals(price_series, crispr_ens_preds)
                plt.plot(np.arange(len(cum_c)), cum_c, label='c_ensemble', linewidth=2, color='tab:green')
                aggregate.append({'stock': f'stock_{si}', 'model': 'c_ensemble', 'final_pnl': float(cum_c[-1]) if len(cum_c) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_c)) if len(pnl_c) > 0 else 0.0})

                plt.legend()
                plt.title(f'stock_{si} cumulative PnL: baseline (b_) vs crispr (c_)')
                plt.xlabel('time')
                plt.ylabel('cumulative PnL')
                plt.grid(False)
                plt.tight_layout()
                """Generate plots and simple PnL backtests for the multi-stock benchmark.

                This script re-runs the data generation and model predictions (same config as bench_multi_stocks)
                and computes a one-step-ahead directional strategy PnL for each model and two ensembles:
                 - baseline ensemble trained from built-in models
                 - crispr ensemble which augments the baseline with persisted CRISPR-accepted models from disk

                Saves CSV summary and PNG plots per stock and an aggregate CSV.
                """
                import os
                import glob
                import pickle
                import numpy as np
                import pandas as pd
                import matplotlib.pyplot as plt
                from sklearn.linear_model import LinearRegression
                from sklearn.ensemble import RandomForestRegressor
                from sklearn.metrics import mean_squared_error
                from sklearn.preprocessing import StandardScaler

                try:
                    import xgboost as xgb
                except Exception:
                    xgb = None

                try:
                    import tensorflow as tf
                    from tensorflow import keras
                    tf_available = True
                except Exception:
                    tf_available = False

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


                class AdaptiveEnsemble:
                    def __init__(self, model_names, eta=1.0):
                        self.model_names = list(model_names)
                        self.eta = eta
                        self.w = np.ones(len(self.model_names)) / len(self.model_names)

                    def update(self, preds_matrix, y_true):
                        errs = np.mean((preds_matrix - y_true.reshape(1, -1)) ** 2, axis=1)
                        self.w = self.w * np.exp(-self.eta * errs)
                        self.w = self.w / (np.sum(self.w) + 1e-12)

                    def predict(self, preds_matrix):
                        return np.dot(self.w, preds_matrix)


                def backtest_signals(price_series, preds):
                    # preds: array of predictions aligned with price_series indices (length T)
                    # Generate signals s_t = sign(pred_t - price_t) (one-step ahead approach)
                    # PnL per step: s_t * (price_{t+1} - price_t). Return cumulative PnL (len T-1)
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


                def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
                    os.makedirs(out_dir, exist_ok=True)
                    series_all = make_correlated_series(n_stocks=n_stocks, n=n)

                    aggregate = []

                    for si in range(n_stocks):
                        series = series_all[si]
                        X, y = make_lag_features(series, lags=lags)
                        split = int(0.7 * len(X))
                        val_len = int(0.15 * len(X))
                        X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
                        y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

                        # persistence baseline
                        persist_test = X_test[:, -1]

                        # Standardize features per-stock
                        scaler = StandardScaler()
                        X_train_s = scaler.fit_transform(X_train)
                        X_val_s = scaler.transform(X_val)
                        X_test_s = scaler.transform(X_test)

                        # Train baseline models
                        lr = LinearRegression().fit(X_train_s, y_train)
                        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)
                        if xgb is not None:
                            xg = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0).fit(X_train_s, y_train)
                        else:
                            xg = None

                        # LSTM baseline if available
                        if tf_available:
                            X_train_l = X_train_s.reshape((X_train_s.shape[0], X_train_s.shape[1], 1))
                            X_val_l = X_val_s.reshape((X_val_s.shape[0], X_val_s.shape[1], 1))
                            X_test_l = X_test_s.reshape((X_test_s.shape[0], X_test_s.shape[1], 1))
                            model = keras.Sequential([
                                keras.layers.Input(shape=(lags, 1)),
                                keras.layers.LSTM(32, activation='tanh'),
                                keras.layers.Dense(1)
                            ])
                            model.compile(optimizer='adam', loss='mse')
                            model.fit(X_train_l, y_train, epochs=5, batch_size=64, verbose=0)
                            lstm_test = model.predict(X_test_l).flatten()
                            lstm_val = model.predict(X_val_l).flatten()
                        else:
                            lstm_test = None
                            lstm_val = None

                        # Build baseline predictions dict
                        preds = {
                            'persistence': persist_test,
                            'linear': lr.predict(X_test_s),
                            'rf': rf.predict(X_test_s)
                        }
                        preds_val = [X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)]
                        model_order = ['persistence', 'linear', 'rf']
                        if xg is not None:
                            preds['xg'] = xg.predict(X_test_s)
                            preds_val.append(xg.predict(X_val_s))
                            model_order.append('xg')
                        if lstm_test is not None:
                            preds['lstm'] = lstm_test
                            preds_val.append(lstm_val)
                            model_order.append('lstm')

                        preds_val = np.vstack(preds_val)

                        # Baseline ensemble trained on validation
                        ens = AdaptiveEnsemble(model_order, eta=1.0)
                        chunk = 20
                        for start in range(0, preds_val.shape[1], chunk):
                            end = min(start + chunk, preds_val.shape[1])
                            ens.update(preds_val[:, start:end], y_val[start:end])
                        baseline_ens_preds = ens.predict(np.vstack([preds[k] for k in model_order]))

                        # Load persisted CRISPR models and add into candidate pool
                        persisted = load_persisted_models_for_stock(model_dir, si)
                        crispr_preds = dict(preds)  # copy baseline preds
                        crispr_model_names = list(model_order)
                        crispr_preds_val_list = [preds_val[i] for i in range(preds_val.shape[0])]

                        for name, m in persisted.items():
                            try:
                                pv = m.predict(X_val_s)
                                pt = m.predict(X_test_s)
                            except Exception:
                                try:
                                    pv = m.predict(X_val)
                                    pt = m.predict(X_test)
                                except Exception:
                                    continue
                            crispr_preds[name] = pt
                            crispr_preds_val_list.append(pv)
                            crispr_model_names.append(name)

                        # If there are extra persisted models, compute crispr ensemble weights
                        if len(crispr_model_names) > len(model_order):
                            preds_val_all = np.vstack(crispr_preds_val_list)
                            ens_crispr = AdaptiveEnsemble(crispr_model_names, eta=1.0)
                            for start in range(0, preds_val_all.shape[1], chunk):
                                end = min(start + chunk, preds_val_all.shape[1])
                                ens_crispr.update(preds_val_all[:, start:end], y_val[start:end])
                            crispr_ens_preds = ens_crispr.predict(np.vstack([crispr_preds[n] for n in crispr_model_names]))
                        else:
                            crispr_ens_preds = baseline_ens_preds
                            crispr_model_names = model_order

                        # Backtest per model and both ensembles
                        plt.figure(figsize=(10, 6))
                        T = len(list(preds.values())[0])
                        price_series = series[split + val_len + lags: split + val_len + lags + T]

                        # baseline models and baseline ensemble
                        for name in model_order:
                            arr = preds[name]
                            cum, pnl = backtest_signals(price_series, arr)
                            plt.plot(np.arange(len(cum)), cum, label=f'b_{name}')
                            aggregate.append({'stock': f'stock_{si}', 'model': f'b_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                        cum_b, pnl_b = backtest_signals(price_series, baseline_ens_preds)
                        plt.plot(np.arange(len(cum_b)), cum_b, label='b_ensemble', linewidth=2, color='black')
                        aggregate.append({'stock': f'stock_{si}', 'model': 'b_ensemble', 'final_pnl': float(cum_b[-1]) if len(cum_b) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_b)) if len(pnl_b) > 0 else 0.0})

                        # CRISPR-augmented models / ensemble
                        for name in crispr_model_names:
                            if name in crispr_preds:
                                arr = crispr_preds[name]
                                cum, pnl = backtest_signals(price_series, arr)
                                plt.plot(np.arange(len(cum)), cum, linestyle='--', label=f'c_{name}')
                                aggregate.append({'stock': f'stock_{si}', 'model': f'c_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                        cum_c, pnl_c = backtest_signals(price_series, crispr_ens_preds)
                        plt.plot(np.arange(len(cum_c)), cum_c, label='c_ensemble', linewidth=2, color='tab:green')
                        aggregate.append({'stock': f'stock_{si}', 'model': 'c_ensemble', 'final_pnl': float(cum_c[-1]) if len(cum_c) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_c)) if len(pnl_c) > 0 else 0.0})

                        plt.legend()
                        plt.title(f'stock_{si} cumulative PnL: baseline (b_) vs crispr (c_)')
                        plt.xlabel('time')
                        plt.ylabel('cumulative PnL')
                        plt.grid(False)
                        plt.tight_layout()
                        """Generate plots and simple PnL backtests for the multi-stock benchmark.

                        This script re-runs the data generation and model predictions (same config as bench_multi_stocks)
                        and computes a one-step-ahead directional strategy PnL for each model and two ensembles:
                         - baseline ensemble trained from built-in models
                         - crispr ensemble which augments the baseline with persisted CRISPR-accepted models from disk

                        Saves CSV summary and PNG plots per stock and an aggregate CSV.
                        """

                        import os
                        import glob
                        import pickle
                        import numpy as np
                        import pandas as pd
                        import matplotlib.pyplot as plt
                        from sklearn.linear_model import LinearRegression
                        from sklearn.ensemble import RandomForestRegressor
                        from sklearn.preprocessing import StandardScaler

                        try:
                            import xgboost as xgb
                        except Exception:
                            xgb = None

                        try:
                            import tensorflow as tf
                            from tensorflow import keras
                            tf_available = True
                        except Exception:
                            tf_available = False

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


                        class AdaptiveEnsemble:
                            def __init__(self, model_names, eta=1.0):
                                self.model_names = list(model_names)
                                self.eta = eta
                                self.w = np.ones(len(self.model_names)) / len(self.model_names)

                            def update(self, preds_matrix, y_true):
                                errs = np.mean((preds_matrix - y_true.reshape(1, -1)) ** 2, axis=1)
                                self.w = self.w * np.exp(-self.eta * errs)
                                self.w = self.w / (np.sum(self.w) + 1e-12)

                            def predict(self, preds_matrix):
                                return np.dot(self.w, preds_matrix)


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


                        def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
                            os.makedirs(out_dir, exist_ok=True)
                            series_all = make_correlated_series(n_stocks=n_stocks, n=n)

                            aggregate = []

                            for si in range(n_stocks):
                                series = series_all[si]
                                X, y = make_lag_features(series, lags=lags)
                                split = int(0.7 * len(X))
                                val_len = int(0.15 * len(X))
                                X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
                                y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

                                persist_test = X_test[:, -1]

                                scaler = StandardScaler()
                                X_train_s = scaler.fit_transform(X_train)
                                X_val_s = scaler.transform(X_val)
                                X_test_s = scaler.transform(X_test)

                                lr = LinearRegression().fit(X_train_s, y_train)
                                rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)
                                xg = None
                                if 'xgboost' in globals():
                                    try:
                                        import xgboost as xgb
                                        xg = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0).fit(X_train_s, y_train)
                                    except Exception:
                                        xg = None

                                if tf_available:
                                    X_train_l = X_train_s.reshape((X_train_s.shape[0], X_train_s.shape[1], 1))
                                    X_val_l = X_val_s.reshape((X_val_s.shape[0], X_val_s.shape[1], 1))
                                    X_test_l = X_test_s.reshape((X_test_s.shape[0], X_test_s.shape[1], 1))
                                    model = keras.Sequential([
                                        keras.layers.Input(shape=(lags, 1)),
                                        keras.layers.LSTM(32, activation='tanh'),
                                        keras.layers.Dense(1)
                                    ])
                                    model.compile(optimizer='adam', loss='mse')
                                    model.fit(X_train_l, y_train, epochs=5, batch_size=64, verbose=0)
                                    lstm_test = model.predict(X_test_l).flatten()
                                    lstm_val = model.predict(X_val_l).flatten()
                                else:
                                    lstm_test = None
                                    lstm_val = None

                                preds = {
                                    'persistence': persist_test,
                                    'linear': lr.predict(X_test_s),
                                    'rf': rf.predict(X_test_s)
                                }
                                preds_val = [X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)]
                                model_order = ['persistence', 'linear', 'rf']
                                if xg is not None:
                                    preds['xg'] = xg.predict(X_test_s)
                                    preds_val.append(xg.predict(X_val_s))
                                    model_order.append('xg')
                                if lstm_test is not None:
                                    preds['lstm'] = lstm_test
                                    preds_val.append(lstm_val)
                                    model_order.append('lstm')

                                preds_val = np.vstack(preds_val)

                                ens = AdaptiveEnsemble(model_order, eta=1.0)
                                chunk = 20
                                for start in range(0, preds_val.shape[1], chunk):
                                    end = min(start + chunk, preds_val.shape[1])
                                    ens.update(preds_val[:, start:end], y_val[start:end])
                                baseline_ens_preds = ens.predict(np.vstack([preds[k] for k in model_order]))

                                persisted = load_persisted_models_for_stock(model_dir, si)
                                crispr_preds = dict(preds)
                                crispr_model_names = list(model_order)
                                crispr_preds_val_list = [preds_val[i] for i in range(preds_val.shape[0])]

                                for name, m in persisted.items():
                                    try:
                                        pv = m.predict(X_val_s)
                                        pt = m.predict(X_test_s)
                                    except Exception:
                                        try:
                                            pv = m.predict(X_val)
                                            pt = m.predict(X_test)
                                        except Exception:
                                            continue
                                    crispr_preds[name] = pt
                                    crispr_preds_val_list.append(pv)
                                    crispr_model_names.append(name)

                                if len(crispr_model_names) > len(model_order):
                                    preds_val_all = np.vstack(crispr_preds_val_list)
                                    ens_crispr = AdaptiveEnsemble(crispr_model_names, eta=1.0)
                                    for start in range(0, preds_val_all.shape[1], chunk):
                                        end = min(start + chunk, preds_val_all.shape[1])
                                        ens_crispr.update(preds_val_all[:, start:end], y_val[start:end])
                                    crispr_ens_preds = ens_crispr.predict(np.vstack([crispr_preds[n] for n in crispr_model_names]))
                                else:
                                    crispr_ens_preds = baseline_ens_preds
                                    crispr_model_names = model_order

                                plt.figure(figsize=(10, 6))
                                T = len(list(preds.values())[0])
                                price_series = series[split + val_len + lags: split + val_len + lags + T]

                                for name in model_order:
                                    arr = preds[name]
                                    cum, pnl = backtest_signals(price_series, arr)
                                    plt.plot(np.arange(len(cum)), cum, label=f'b_{name}')
                                    aggregate.append({'stock': f'stock_{si}', 'model': f'b_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                                cum_b, pnl_b = backtest_signals(price_series, baseline_ens_preds)
                                plt.plot(np.arange(len(cum_b)), cum_b, label='b_ensemble', linewidth=2, color='black')
                                aggregate.append({'stock': f'stock_{si}', 'model': 'b_ensemble', 'final_pnl': float(cum_b[-1]) if len(cum_b) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_b)) if len(pnl_b) > 0 else 0.0})

                                for name in crispr_model_names:
                                    if name in crispr_preds:
                                        arr = crispr_preds[name]
                                        cum, pnl = backtest_signals(price_series, arr)
                                        plt.plot(np.arange(len(cum)), cum, linestyle='--', label=f'c_{name}')
                                        aggregate.append({'stock': f'stock_{si}', 'model': f'c_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                                cum_c, pnl_c = backtest_signals(price_series, crispr_ens_preds)
                                plt.plot(np.arange(len(cum_c)), cum_c, label='c_ensemble', linewidth=2, color='tab:green')
                                aggregate.append({'stock': f'stock_{si}', 'model': 'c_ensemble', 'final_pnl': float(cum_c[-1]) if len(cum_c) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_c)) if len(pnl_c) > 0 else 0.0})

                                plt.legend()
                                plt.title(f'stock_{si} cumulative PnL: baseline (b_) vs crispr (c_)')
                                plt.xlabel('time')
                                plt.ylabel('cumulative PnL')
                                plt.grid(False)
                                plt.tight_layout()
                                """Generate plots and simple PnL backtests for the multi-stock benchmark.

                                This script re-runs the data generation and model predictions (same config as bench_multi_stocks)
                                and computes a one-step-ahead directional strategy PnL for each model and two ensembles:
                                 - baseline ensemble trained from built-in models
                                 - crispr ensemble which augments the baseline with persisted CRISPR-accepted models from disk

                                Saves CSV summary and PNG plots per stock and an aggregate CSV.
                                """

                                import os
                                import glob
                                import pickle
                                import numpy as np
                                import pandas as pd
                                import matplotlib.pyplot as plt
                                from sklearn.linear_model import LinearRegression
                                from sklearn.ensemble import RandomForestRegressor
                                from sklearn.preprocessing import StandardScaler

                                try:
                                    import xgboost as xgb
                                except Exception:
                                    xgb = None

                                try:
                                    import tensorflow as tf
                                    from tensorflow import keras
                                    tf_available = True
                                except Exception:
                                    tf_available = False

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


                                class AdaptiveEnsemble:
                                    def __init__(self, model_names, eta=1.0):
                                        self.model_names = list(model_names)
                                        self.eta = eta
                                        self.w = np.ones(len(self.model_names)) / len(self.model_names)

                                    def update(self, preds_matrix, y_true):
                                        errs = np.mean((preds_matrix - y_true.reshape(1, -1)) ** 2, axis=1)
                                        self.w = self.w * np.exp(-self.eta * errs)
                                        self.w = self.w / (np.sum(self.w) + 1e-12)

                                    def predict(self, preds_matrix):
                                        return np.dot(self.w, preds_matrix)


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


                                def run_report(n_stocks=8, n=2500, lags=20, out_dir='reports', model_dir='bench_crispr_models'):
                                    os.makedirs(out_dir, exist_ok=True)
                                    series_all = make_correlated_series(n_stocks=n_stocks, n=n)

                                    aggregate = []

                                    for si in range(n_stocks):
                                        series = series_all[si]
                                        X, y = make_lag_features(series, lags=lags)
                                        split = int(0.7 * len(X))
                                        val_len = int(0.15 * len(X))
                                        X_train, X_val, X_test = X[:split], X[split:split + val_len], X[split + val_len:]
                                        y_train, y_val, y_test = y[:split], y[split:split + val_len], y[split + val_len:]

                                        persist_test = X_test[:, -1]

                                        scaler = StandardScaler()
                                        X_train_s = scaler.fit_transform(X_train)
                                        X_val_s = scaler.transform(X_val)
                                        X_test_s = scaler.transform(X_test)

                                        lr = LinearRegression().fit(X_train_s, y_train)
                                        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)
                                        xg = None
                                        try:
                                            import xgboost as xgb
                                            xg = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0).fit(X_train_s, y_train)
                                        except Exception:
                                            xg = None

                                        if tf_available:
                                            X_train_l = X_train_s.reshape((X_train_s.shape[0], X_train_s.shape[1], 1))
                                            X_val_l = X_val_s.reshape((X_val_s.shape[0], X_val_s.shape[1], 1))
                                            X_test_l = X_test_s.reshape((X_test_s.shape[0], X_test_s.shape[1], 1))
                                            model = keras.Sequential([
                                                keras.layers.Input(shape=(lags, 1)),
                                                keras.layers.LSTM(32, activation='tanh'),
                                                keras.layers.Dense(1)
                                            ])
                                            model.compile(optimizer='adam', loss='mse')
                                            model.fit(X_train_l, y_train, epochs=5, batch_size=64, verbose=0)
                                            lstm_test = model.predict(X_test_l).flatten()
                                            lstm_val = model.predict(X_val_l).flatten()
                                        else:
                                            lstm_test = None
                                            lstm_val = None

                                        preds = {
                                            'persistence': persist_test,
                                            'linear': lr.predict(X_test_s),
                                            'rf': rf.predict(X_test_s)
                                        }
                                        preds_val = [X_val[:, -1], lr.predict(X_val_s), rf.predict(X_val_s)]
                                        model_order = ['persistence', 'linear', 'rf']
                                        if xg is not None:
                                            preds['xg'] = xg.predict(X_test_s)
                                            preds_val.append(xg.predict(X_val_s))
                                            model_order.append('xg')
                                        if lstm_test is not None:
                                            preds['lstm'] = lstm_test
                                            preds_val.append(lstm_val)
                                            model_order.append('lstm')

                                        preds_val = np.vstack(preds_val)

                                        ens = AdaptiveEnsemble(model_order, eta=1.0)
                                        chunk = 20
                                        for start in range(0, preds_val.shape[1], chunk):
                                            end = min(start + chunk, preds_val.shape[1])
                                            ens.update(preds_val[:, start:end], y_val[start:end])
                                        baseline_ens_preds = ens.predict(np.vstack([preds[k] for k in model_order]))

                                        persisted = load_persisted_models_for_stock(model_dir, si)
                                        crispr_preds = dict(preds)
                                        crispr_model_names = list(model_order)
                                        crispr_preds_val_list = [preds_val[i] for i in range(preds_val.shape[0])]

                                        for name, m in persisted.items():
                                            try:
                                                pv = m.predict(X_val_s)
                                                pt = m.predict(X_test_s)
                                            except Exception:
                                                try:
                                                    pv = m.predict(X_val)
                                                    pt = m.predict(X_test)
                                                except Exception:
                                                    continue
                                            crispr_preds[name] = pt
                                            crispr_preds_val_list.append(pv)
                                            crispr_model_names.append(name)

                                        if len(crispr_model_names) > len(model_order):
                                            preds_val_all = np.vstack(crispr_preds_val_list)
                                            ens_crispr = AdaptiveEnsemble(crispr_model_names, eta=1.0)
                                            for start in range(0, preds_val_all.shape[1], chunk):
                                                end = min(start + chunk, preds_val_all.shape[1])
                                                ens_crispr.update(preds_val_all[:, start:end], y_val[start:end])
                                            crispr_ens_preds = ens_crispr.predict(np.vstack([crispr_preds[n] for n in crispr_model_names]))
                                        else:
                                            crispr_ens_preds = baseline_ens_preds
                                            crispr_model_names = model_order

                                        plt.figure(figsize=(10, 6))
                                        T = len(list(preds.values())[0])
                                        price_series = series[split + val_len + lags: split + val_len + lags + T]

                                        for name in model_order:
                                            arr = preds[name]
                                            cum, pnl = backtest_signals(price_series, arr)
                                            plt.plot(np.arange(len(cum)), cum, label=f'b_{name}')
                                            aggregate.append({'stock': f'stock_{si}', 'model': f'b_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                                        cum_b, pnl_b = backtest_signals(price_series, baseline_ens_preds)
                                        plt.plot(np.arange(len(cum_b)), cum_b, label='b_ensemble', linewidth=2, color='black')
                                        aggregate.append({'stock': f'stock_{si}', 'model': 'b_ensemble', 'final_pnl': float(cum_b[-1]) if len(cum_b) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_b)) if len(pnl_b) > 0 else 0.0})

                                        for name in crispr_model_names:
                                            if name in crispr_preds:
                                                arr = crispr_preds[name]
                                                cum, pnl = backtest_signals(price_series, arr)
                                                plt.plot(np.arange(len(cum)), cum, linestyle='--', label=f'c_{name}')
                                                aggregate.append({'stock': f'stock_{si}', 'model': f'c_{name}', 'final_pnl': float(cum[-1]) if len(cum) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl)) if len(pnl) > 0 else 0.0})

                                        cum_c, pnl_c = backtest_signals(price_series, crispr_ens_preds)
                                        plt.plot(np.arange(len(cum_c)), cum_c, label='c_ensemble', linewidth=2, color='tab:green')
                                        aggregate.append({'stock': f'stock_{si}', 'model': 'c_ensemble', 'final_pnl': float(cum_c[-1]) if len(cum_c) > 0 else 0.0, 'mean_pnl': float(np.mean(pnl_c)) if len(pnl_c) > 0 else 0.0})

                                        plt.legend()
                                        plt.title(f'stock_{si} cumulative PnL: baseline (b_) vs crispr (c_)')
                                        plt.xlabel('time')
                                        plt.ylabel('cumulative PnL')
                                        plt.grid(False)
                                        plt.tight_layout()
                                        plt.savefig(os.path.join(out_dir, f'stock_{si}_pnl.png'))
                                        plt.close()

                                    df = pd.DataFrame(aggregate)
                                    summary = df.groupby('model').agg(final_pnl_mean=('final_pnl', 'mean'), final_pnl_std=('final_pnl', 'std')).reset_index()
                                    summary.to_csv(os.path.join(out_dir, 'ensemble_pnl_summary.csv'), index=False)
                                    df.to_csv(os.path.join(out_dir, 'ensemble_pnl_detail.csv'), index=False)
                                    print('Wrote reports to', out_dir)
                                    print(summary)


                                if __name__ == '__main__':
                                    import argparse

                                    p = argparse.ArgumentParser()
                                    p.add_argument('--n-stocks', type=int, default=8)
                                    p.add_argument('--n', type=int, default=2500)
                                    p.add_argument('--lags', type=int, default=20)
                                    p.add_argument('--out-dir', default='reports')
                                    p.add_argument('--model-dir', default='bench_crispr_models')
                                    args = p.parse_args()
                                    run_report(n_stocks=args.n_stocks, n=args.n, lags=args.lags, out_dir=args.out_dir, model_dir=args.model_dir)
