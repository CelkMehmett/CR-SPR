"""POC runner for a minimal self-healing CRISPR-FinAI system (Phase 1).

Flow:
1. Load data (CSV or synthetic)
2. Build features
3. Detect drift
4. If drift: run GA editor to tune a simple threshold-based signal
5. Evaluate before/after and log edit
"""
from __future__ import annotations
import argparse
import os
import numpy as np
import pandas as pd

from core.data_loader import load_csv, infer_ohlcv
from core.features import build_features
from core.drift_detector import detect_isolationforest
from core.backtest import simple_backtest
from core.edit_logger import log_edit
from agents.editor_ga import SimpleGAEditor


def synthetic_price(n=500):
    rng = np.random.RandomState(42)
    steps = rng.normal(loc=0.0003, scale=0.01, size=n)
    price = 100 + np.cumsum(steps)
    idx = pd.bdate_range(end=pd.Timestamp.today(), periods=n)
    return pd.Series(price, index=idx)


def baseline_signal(price: pd.Series, sma_window: int = 20) -> pd.Series:
    sma = price.rolling(sma_window).mean()
    return (price > sma).astype(int)


def evaluate_params(price: pd.Series, params: np.ndarray) -> float:
    # params expected: [sma_window], but GA works with floats -> round
    sma_w = int(max(2, round(params[0])))
    sig = baseline_signal(price, sma_w)
    _, metrics = simple_backtest(price, sig)
    return metrics.get('sharpe', 0.0)


def run(args):
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    if args.csv is None:
        price = synthetic_price(500)
    else:
        df = load_csv(args.csv)
        df = infer_ohlcv(df)
        price = df['Close']

    feats = build_features(pd.DataFrame({'Close': price}))
    is_drift, diag = detect_isolationforest(feats)
    print('drift_detected=', is_drift, diag)

    # baseline evaluation
    base_sig = baseline_signal(price, 20)
    _, metrics_before = simple_backtest(price, base_sig)

    if not is_drift:
        print('No drift detected; nothing to edit. Metrics:', metrics_before)
        return

    # GA editor: tune sma_window between 2 and 100
    editor = SimpleGAEditor(num_genes=1, gene_space=[{'low': 2, 'high': 100}], pop_size=8, generations=6)
    best_sol, best_fit = editor.edit(lambda x: evaluate_params(price, x))
    best_param = int(round(best_sol[0]))

    new_sig = baseline_signal(price, best_param)
    _, metrics_after = simple_backtest(price, new_sig)

    log_path = os.path.join(out_dir, 'edits.log')
    log_edit(log_path, {'sma': 20}, {'sma': best_param}, metrics_before, metrics_after)

    print('GA found param:', best_param, 'fit(sharpe)=', best_fit)
    print('metrics_before=', metrics_before)
    print('metrics_after=', metrics_after)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv', default=None)
    p.add_argument('--out_dir', default='poc_results')
    args = p.parse_args()
    run(args)


if __name__ == '__main__':
    main()
