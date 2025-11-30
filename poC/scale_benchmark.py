"""Scale benchmark across multiple tickers with optional drift-aware edits.

This script uses components from Phase1: feature builder, drift detector, simple edits,
and the existing signal generators in `poc.compare_algorithms`.
"""
from __future__ import annotations
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

from poc.compare_algorithms import download_yfinance, naive_momentum_signal, arima_signal, rf_signal
from core.features import build_features
from core.drift_detector import detect_isolationforest
from core.backtest import simple_backtest
from agents.editor_ga import SimpleGAEditor
import numpy as np
import warnings
warnings.filterwarnings('ignore')


def run(symbols, start, end, out_dir='poc/scale_results', apply_edits=True):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    quick = bool(int(os.environ.get('QUICK', '0')))
    ga_reports_path = os.path.join(out_dir, 'ga_reports.jsonl')
    # clear previous
    try:
        open(ga_reports_path, 'w').close()
    except Exception:
        pass
    for s in symbols:
        print('Processing', s)
        df = download_yfinance(s, start=start, end=end)
        if 'Close' not in df.columns:
            print('Skipping', s, 'no Close')
            continue
        # coerce close series
        price = df['Close']
        if isinstance(price, pd.DataFrame):
            if s in price.columns:
                price = price[s]
            else:
                price = price.iloc[:, 0]
        price = price.squeeze()

        feats = build_features(pd.DataFrame({'Close': price}))
        is_drift, diag = detect_isolationforest(feats)
        print(' drift:', is_drift, diag)

        models = {
            'naive_momentum': naive_momentum_signal,
            'arima': arima_signal,
            'random_forest': rf_signal,
        }

        for name, fn in models.items():
            sig = fn(price)

            # If drift and edits enabled, run GA-based repair for each model
            if apply_edits and is_drift:
                if name == 'naive_momentum':
                    # tune sma window
                    if quick:
                        editor = SimpleGAEditor(num_genes=1, gene_space=[{'low': 2, 'high': 80}], pop_size=4, generations=2)
                    else:
                        editor = SimpleGAEditor(num_genes=1, gene_space=[{'low': 2, 'high': 80}], pop_size=6, generations=4)

                    def eval_naive(x: np.ndarray) -> float:
                        w = int(round(float(x[0])))
                        w = max(2, min(200, w))
                        sig_c = (price > price.rolling(w).mean()).astype(int)
                        _, m = simple_backtest(price, sig_c)
                        return float(m.get('sharpe', 0.0))

                    best_sol, best_fit = editor.edit(eval_naive)
                    # log GA report
                    with open(ga_reports_path, 'a') as gf:
                        import json
                        gf.write(json.dumps({'symbol': s, 'model': name, 'best_sol': best_sol.tolist(), 'best_fit': best_fit}) + '\n')
                    best_w = int(round(best_sol[0]))
                    sig = (price > price.rolling(best_w).mean()).astype(int)
                elif name == 'arima':
                    # tune (p,d,q) in small ranges p:0-3,d:0-1,q:0-3
                    if quick:
                        editor = SimpleGAEditor(num_genes=3, gene_space=[{'low': 0, 'high': 3}, {'low': 0, 'high': 1}, {'low': 0, 'high': 3}], pop_size=6, generations=2)
                    else:
                        editor = SimpleGAEditor(num_genes=3, gene_space=[{'low': 0, 'high': 3}, {'low': 0, 'high': 1}, {'low': 0, 'high': 3}], pop_size=8, generations=4)

                    def eval_arima(x: np.ndarray) -> float:
                        p = int(round(float(x[0])))
                        d = int(round(float(x[1])))
                        q = int(round(float(x[2])))
                        p = max(0, min(5, p))
                        d = max(0, min(2, d))
                        q = max(0, min(5, q))
                        # build signal by walk-forward ARIMA with this order
                        try:
                            from statsmodels.tsa.arima.model import ARIMA
                        except Exception:
                            return 0.0
                        n = len(price.dropna())
                        if n < 60:
                            return 0.0
                        signals = pd.Series(0, index=price.index)
                        window = min(250, max(20, n // 2))
                        for idx in range(window, n):
                            train = price.dropna().iloc[idx - window:idx]
                            try:
                                model = ARIMA(train, order=(p, d, q))
                                res = model.fit(method_kwargs={'warn_convergence': False})
                                pred = res.forecast(steps=1)
                                pred_val = float(pred.iloc[0]) if hasattr(pred, 'iloc') else float(pred[0])
                                last_obs = float(train.iloc[-1])
                                label = price.index[idx]
                                signals.loc[label] = 1 if pred_val > last_obs else 0
                            except Exception:
                                continue
                        _, m = simple_backtest(price, signals)
                        return float(m.get('sharpe', 0.0))

                    best_sol, best_fit = editor.edit(eval_arima)
                    with open(ga_reports_path, 'a') as gf:
                        import json
                        gf.write(json.dumps({'symbol': s, 'model': name, 'best_sol': [int(round(float(x))) for x in best_sol.tolist()], 'best_fit': best_fit}) + '\n')
                    # rebuild final signal with best params
                    pbest, dbest, qbest = [int(round(float(v))) for v in best_sol]
                    # create final arima signal
                    try:
                        from statsmodels.tsa.arima.model import ARIMA
                        n = len(price.dropna())
                        signals = pd.Series(0, index=price.index)
                        window = min(250, max(20, n // 2))
                        for idx in range(window, n):
                            train = price.dropna().iloc[idx - window:idx]
                            try:
                                model = ARIMA(train, order=(pbest, dbest, qbest))
                                res = model.fit(method_kwargs={'warn_convergence': False})
                                pred = res.forecast(steps=1)
                                pred_val = float(pred.iloc[0]) if hasattr(pred, 'iloc') else float(pred[0])
                                last_obs = float(train.iloc[-1])
                                label = price.index[idx]
                                signals.loc[label] = 1 if pred_val > last_obs else 0
                            except Exception:
                                continue
                        sig = signals.fillna(0)
                    except Exception:
                        # fallback to original sig
                        sig = fn(price)
                elif name == 'random_forest':
                    if quick:
                        editor = SimpleGAEditor(num_genes=2, gene_space=[{'low': 10, 'high': 200}, {'low': 1, 'high': 20}], pop_size=6, generations=2)
                    else:
                        editor = SimpleGAEditor(num_genes=2, gene_space=[{'low': 10, 'high': 200}, {'low': 1, 'high': 20}], pop_size=8, generations=4)

                    def eval_rf(x: np.ndarray) -> float:
                        n_est = int(round(float(x[0])))
                        max_d = int(round(float(x[1])))
                        # build features and train RF walk-forward similar to rf_signal
                        try:
                            from sklearn.ensemble import RandomForestClassifier
                        except Exception:
                            return 0.0
                        df = pd.DataFrame({'price': price})
                        df['ret'] = df['price'].pct_change()
                        for i in range(1, 6):
                            df[f'lag_{i}'] = df['ret'].shift(i)
                        df['sma_5'] = df['price'].rolling(5).mean()
                        df['sma_20'] = df['price'].rolling(20).mean()
                        df['sma_diff'] = df['sma_5'] - df['sma_20']
                        df = df.dropna()
                        if df.empty or len(df) < 50:
                            return 0.0
                        preds = pd.Series(0, index=df.index)
                        features = [c for c in df.columns if c.startswith('lag_')] + ['sma_diff']
                        min_train = min(100, max(20, int(len(df) * 0.5)))
                        for i in range(min_train, len(df)):
                            train_idx = df.index[:i]
                            test_idx = df.index[i:i + 1]
                            X_train = df.loc[train_idx, features].copy()
                            y_train = (df['price'].shift(-1) > df['price']).astype(int).loc[train_idx]
                            valid_idx = X_train.dropna().index.intersection(y_train.dropna().index)
                            X_train = X_train.loc[valid_idx]
                            y_train = y_train.loc[valid_idx]
                            if len(X_train) < 20:
                                continue
                            try:
                                clf = RandomForestClassifier(n_estimators=max(1, n_est), max_depth=max_d if max_d>0 else None, random_state=42)
                                clf.fit(X_train.values, y_train.values)
                                p = clf.predict(df.loc[test_idx, features].fillna(0).values)
                                preds.loc[test_idx] = int(p[0])
                            except Exception:
                                continue
                        sig_c = pd.Series(0, index=price.index)
                        sig_c.loc[preds.index] = preds
                        _, m = simple_backtest(price, sig_c.fillna(0))
                        return float(m.get('sharpe', 0.0))

                    best_sol, best_fit = editor.edit(eval_rf)
                    with open(ga_reports_path, 'a') as gf:
                        import json
                        gf.write(json.dumps({'symbol': s, 'model': name, 'best_sol': [int(round(float(x))) for x in best_sol.tolist()], 'best_fit': best_fit}) + '\n')
                    nbest, dbest = [int(round(float(v))) for v in best_sol]
                    # build final RF signal with best params
                    try:
                        from sklearn.ensemble import RandomForestClassifier
                        df = pd.DataFrame({'price': price})
                        df['ret'] = df['price'].pct_change()
                        for i in range(1, 6):
                            df[f'lag_{i}'] = df['ret'].shift(i)
                        df['sma_5'] = df['price'].rolling(5).mean()
                        df['sma_20'] = df['price'].rolling(20).mean()
                        df['sma_diff'] = df['sma_5'] - df['sma_20']
                        df = df.dropna()
                        preds = pd.Series(0, index=df.index)
                        features = [c for c in df.columns if c.startswith('lag_')] + ['sma_diff']
                        min_train = min(100, max(20, int(len(df) * 0.5)))
                        for i in range(min_train, len(df)):
                            train_idx = df.index[:i]
                            test_idx = df.index[i:i + 1]
                            X_train = df.loc[train_idx, features].copy()
                            y_train = (df['price'].shift(-1) > df['price']).astype(int).loc[train_idx]
                            valid_idx = X_train.dropna().index.intersection(y_train.dropna().index)
                            X_train = X_train.loc[valid_idx]
                            y_train = y_train.loc[valid_idx]
                            if len(X_train) < 20:
                                continue
                            try:
                                clf = RandomForestClassifier(n_estimators=max(1, nbest), max_depth=dbest if dbest>0 else None, random_state=42)
                                clf.fit(X_train.values, y_train.values)
                                p = clf.predict(df.loc[test_idx, features].fillna(0).values)
                                preds.loc[test_idx] = int(p[0])
                            except Exception:
                                continue
                        sig = pd.Series(0, index=price.index)
                        sig.loc[preds.index] = preds
                    except Exception:
                        sig = fn(price)

            rets, metrics = simple_backtest(price, sig)
            rows.append({'symbol': s, 'model': name, **metrics})
            # save returns per symbol-model
            try:
                rets.to_frame(name='returns').to_parquet(os.path.join(out_dir, f'{s}_{name}_returns.parquet'))
            except Exception:
                rets.to_frame('returns').to_csv(os.path.join(out_dir, f'{s}_{name}_returns.csv'))

    res = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, 'scale_compare_results.csv')
    res.to_csv(csv_path, index=False)

    # simple plot: Sharpe by model grouped by symbol
    pivot = res.pivot(index='symbol', columns='model', values='sharpe')
    ax = pivot.plot.bar(rot=0, figsize=(8, 5), title='Sharpe by model and symbol')
    plt.tight_layout()
    plt_path = os.path.join(out_dir, 'sharpe_by_model.png')
    plt.savefig(plt_path)
    print('Saved results to', csv_path, 'and plot to', plt_path)
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--symbols', nargs='+', required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    p.add_argument('--out_dir', default='poc/scale_results')
    p.add_argument('--no_edits', dest='no_edits', action='store_true')
    args = p.parse_args()
    res = run(args.symbols, args.start, args.end, out_dir=args.out_dir, apply_edits=not args.no_edits)
    print(res)


if __name__ == '__main__':
    main()
