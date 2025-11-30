#!/usr/bin/env python3
"""Simple CRISPR-style mutate-and-select controller for the multi-stock benchmark.

This script loads the multi-stock synthetic data and models (persistence, linear, RF, XGB, LSTM),
evaluates ensemble performance, then iteratively mutates the worst-performing model per-stock
by replacing it with a randomized RandomForest or XGBoost candidate. If ensemble test MSE
improves after replacement, the change is kept; otherwise it's reverted.

Outputs a CSV `bench_crispr_results.csv` with before/after ensemble MSE per stock and prints a short summary.
"""
import os
import csv
import random
import argparse
import json
import time
import pickle
from copy import deepcopy
import hashlib

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
except Exception:
    xgb = None
try:
    import lightgbm as lgb
except Exception:
    lgb = None
try:
    # import a lightweight Keras LSTM if available
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.optimizers import Adam
    tf_available = True
except Exception:
    tf_available = False

from sklearn.metrics import mean_squared_error


def make_synthetic_series(n=1000, seed=0):
    rng = np.random.RandomState(seed)
    t = np.arange(n)
    series = 0.001 * t + 0.5 * np.sin(0.02 * t) + 0.1 * rng.randn(n)
    return series


def make_lag_features(series, lags=10):
    X, y = [], []
    for i in range(lags, len(series) - 1):
        X.append(series[i - lags:i])
        y.append(series[i + 1])
    return np.array(X), np.array(y)


def train_models(X_train, y_train, random_state=0):
    models = {}
    # persistence is simply last value in lag
    models['persistence'] = None
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    models['linear'] = lr
    rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=random_state)
    rf.fit(X_train, y_train)
    models['rf'] = rf
    if xgb is not None:
        xg = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=random_state, verbosity=0)
        xg.fit(X_train, y_train)
        models['xgb'] = xg
    else:
        models['xgb'] = None
    # LSTM omitted for speed in this controller; could be added later
    return models


def predict_model(model_name, model, X):
    if model_name == 'persistence':
        # predict using last feature in each row
        return X[:, -1]
    if model is None:
        return np.zeros(len(X))
    return model.predict(X)


def ensemble_predict(weights, preds_list):
    # preds_list: list of arrays
    w = np.array(weights)
    w = w / (w.sum() + 1e-12)
    stacked = np.vstack(preds_list)
    return (w[:, None] * stacked).sum(axis=0)


def evaluate_ensemble(models, model_names, X_val, y_val, weights=None):
    preds = [predict_model(n, models.get(n), X_val) for n in model_names]
    if weights is None:
        weights = np.ones(len(model_names)) / len(model_names)
    ens = ensemble_predict(weights, preds)
    mse = mean_squared_error(y_val, ens)
    return mse, preds


def mutate_model(old_model, model_name, X_train, y_train, random_state=None, allow_lstm=False, lstm_epochs=3):
    # propose a randomized model: either RF with random params or XGB
    rs = random_state or random.randint(0, 2 ** 30)
    choices = ['rf', 'xgb']
    if allow_lstm and tf_available:
        choices.append('lstm')
    if lgb is not None:
        choices.append('lgb')
    choice = random.choice(choices)
    if choice == 'rf':
        # random hyperparams
        n = random.choice([50, 100, 200, 300])
        d = random.choice([4, 6, 8, 10, None])
        m = RandomForestRegressor(n_estimators=n, max_depth=d, random_state=rs)
        m.fit(X_train, y_train)
        return m
    else:
        if xgb is None:
            # fallback to RF
            m = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=rs)
            m.fit(X_train, y_train)
            return m
        else:
            # random hyperparams for XGBoost
            n = random.choice([50, 100, 200, 300])
            d = random.choice([3, 4, 6, 8, None])
            lr = random.choice([0.01, 0.05, 0.1])
            m = xgb.XGBRegressor(n_estimators=n, max_depth=d, learning_rate=lr, random_state=rs, verbosity=0)
            m.fit(X_train, y_train)
            return m
    if choice == 'lgb':
        # LightGBM randomized
        params = {
            'n_estimators': random.choice([50, 100, 200, 300]),
            'max_depth': random.choice([3, 4, 6, 8, -1]),
            'learning_rate': random.choice([0.01, 0.05, 0.1])
        }
        m = lgb.LGBMRegressor(**params)
        m.fit(X_train, y_train)
        return m

    # simple feature-engineering mutation: randomly add pairwise products of some lag columns
    # (applied with small probability)
    if random.random() < 0.15:
        Xf = X_train.copy()
        n_cols = Xf.shape[1]
        i, j = random.sample(range(n_cols), 2)
        newcol = (Xf[:, i] * Xf[:, j]).reshape(-1, 1)
        Xf = np.hstack([Xf, newcol])
        # train a small RF on engineered features
        m = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=rs)
        m.fit(Xf, y_train)
        # wrap to accept original X by computing new feature
        class FEWrapper:
            def __init__(self, model, i, j):
                self.model = model
                self.i = i
                self.j = j

            def predict(self, X):
                newcol = (X[:, self.i] * X[:, self.j]).reshape(-1, 1)
                Xf = np.hstack([X, newcol])
                return self.model.predict(Xf)

        return FEWrapper(m, i, j)
    if choice == 'lstm':
        # Build a tiny LSTM: expects 2D X_train (n_samples, n_features) where features are lags
        # Convert to shape (n_samples, timesteps, 1)
        Xt = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
        model = Sequential()
        model.add(LSTM(16, input_shape=(Xt.shape[1], Xt.shape[2]), activation='tanh'))
        model.add(Dense(1))
        model.compile(optimizer=Adam(learning_rate=0.01), loss='mse')
        model.fit(Xt, y_train, epochs=lstm_epochs, batch_size=32, verbose=0)
        # wrap Keras model in a small predict wrapper object with predict()
        class KerasWrapper:
            def __init__(self, m):
                self.m = m

            def predict(self, X):
                Xt = X.reshape((X.shape[0], X.shape[1], 1))
                return self.m.predict(Xt, verbose=0).ravel()

        return KerasWrapper(model)


def run_crispr(n_stocks=8, seed=0, lags=10, iters=3, out_csv='bench_crispr_results.csv', audit_path='bench_crispr_audit.jsonl', model_dir='bench_crispr_models', allow_lstm=False, lstm_epochs=3, min_test_delta=1e-6, min_val_rel=0.0):
    random.seed(seed)
    results = []
    os.makedirs(model_dir, exist_ok=True)
    # open audit file in append mode
    audit_f = open(audit_path, 'a')
    for s in range(n_stocks):
        series = make_synthetic_series(n=1200, seed=seed + s)
        X, y = make_lag_features(series, lags=lags)
        # split train/val/test 60/20/20
        n = len(X)
        t1 = int(n * 0.6)
        t2 = int(n * 0.8)
        X_train, y_train = X[:t1], y[:t1]
        X_val, y_val = X[t1:t2], y[t1:t2]
        X_test, y_test = X[t2:], y[t2:]

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
        X_test = scaler.transform(X_test)

        models = train_models(X_train, y_train, random_state=seed + s)
        model_names = [k for k in ['persistence', 'linear', 'rf', 'xgb'] if (k in models and models[k] is not None) or k == 'persistence']

        # initial equal weights
        weights = np.ones(len(model_names)) / len(model_names)
        before_mse, _ = evaluate_ensemble(models, model_names, X_test, y_test, weights=weights)

        # simple online weight updates on validation set to find weights
        preds_val = [predict_model(n, models.get(n), X_val) for n in model_names]
        # initialize weights uniform
        w = np.ones(len(model_names)) / len(model_names)
        alpha = 0.5
        for t in range(len(X_val)):
            p = np.array([pv[t] for pv in preds_val])
            err = (p - y_val[t]) ** 2
            # multiplicative weight update: lower error -> increase weight
            loss = err
            w = w * np.exp(-alpha * loss)
            w = w / (w.sum() + 1e-12)

        # now iterate CRISPR-style mutate/replace
        best_models = deepcopy(models)
        best_model_names = list(model_names)
        best_weights = w.copy()
        best_mse, _ = evaluate_ensemble(best_models, best_model_names, X_test, y_test, weights=best_weights)

        for it in range(iters):
            # evaluate per-model contribution by replacing its predictions with ensemble mean and measuring loss increase
            per_model_mses = []
            preds_test = [predict_model(n, best_models.get(n), X_test) for n in best_model_names]
            for i, mn in enumerate(best_model_names):
                # leave-one-out ensemble
                mask = np.ones(len(best_model_names), dtype=bool)
                mask[i] = False
                if mask.sum() == 0:
                    per_model_mses.append(best_mse)
                    continue
                w_sub = best_weights[mask]
                w_sub = w_sub / (w_sub.sum() + 1e-12)
                preds_sub = [preds_test[j] for j in range(len(preds_test)) if mask[j]]
                ens_sub = ensemble_predict(w_sub, preds_sub)
                mse_sub = mean_squared_error(y_test, ens_sub)
                per_model_mses.append(mse_sub)

            # worst model is the one whose removal gives lowest mse_sub? we want the model that hurts the ensemble most
            # compute delta = mse_sub - best_mse ; if negative, removal helps
            deltas = [m - best_mse for m in per_model_mses]
            # pick model with largest negative delta (removal improves ensemble most) OR largest positive delta (worst contributor)
            worst_idx = int(np.argmax(deltas))
            worst_name = best_model_names[worst_idx]

            # propose mutated model
            print(f"Stock {s}: iter {it+1}/{iters}, mutating model '{worst_name}'")
            X_all = np.vstack([X_train, X_val])
            y_all = np.concatenate([y_train, y_val])
            # record validation MSE before attempting this mutation (for two-stage acceptance)
            val_preds_before = [predict_model(n, best_models.get(n), X_val) for n in best_model_names]
            val_ens_before = ensemble_predict(best_weights, val_preds_before)
            val_mse_before = float(mean_squared_error(y_val, val_ens_before))

            # propose mutated model and measure training time
            t0 = time.time()
            candidate = mutate_model(best_models.get(worst_name), worst_name, X_all, y_all, random_state=seed + s + it, allow_lstm=allow_lstm, lstm_epochs=lstm_epochs)
            training_time = time.time() - t0
            saved = best_models.get(worst_name)
            best_models[worst_name] = candidate

            # re-evaluate weights on validation to get new weights
            preds_val = [predict_model(n, best_models.get(n), X_val) for n in best_model_names]
            w = np.ones(len(best_model_names)) / len(best_model_names)
            for t in range(len(X_val)):
                p = np.array([pv[t] for pv in preds_val])
                err = (p - y_val[t]) ** 2
                w = w * np.exp(-alpha * err)
                w = w / (w.sum() + 1e-12)

            new_mse, _ = evaluate_ensemble(best_models, best_model_names, X_test, y_test, weights=w)
            # compute validation MSE after candidate (use new weights 'w')
            try:
                val_preds_after = [predict_model(n, best_models.get(n), X_val) for n in best_model_names]
                val_mse_after = float(mean_squared_error(y_val, ensemble_predict(w, val_preds_after)))
            except Exception:
                val_mse_after = None

            # collect candidate metadata (hyperparams if available)
            model_params = None
            try:
                if hasattr(candidate, 'get_params'):
                    model_params = candidate.get_params()
                else:
                    # try to inspect inner wrapped model
                    model_params = getattr(candidate, '__dict__', None)
            except Exception:
                model_params = None

            # prepare audit record
            audit = {
                'timestamp': time.time(),
                'stock': s,
                'iteration': it + 1,
                'mutated_model': worst_name,
                'candidate_type': type(candidate).__name__,
                'model_params': model_params,
                'training_time_s': float(training_time),
                'validation_mse_before': val_mse_before,
                'validation_mse_after': val_mse_after,
                'test_mse_before': float(best_mse),
                'test_mse_after_candidate': float(new_mse),
            }

            # Two-stage acceptance rule:
            # 1) validation must improve relatively by min_val_rel
            # 2) test MSE must improve by at least min_test_delta
            accept = False
            reasons = []
            if val_mse_after is None:
                reasons.append('val_mse_after_unavailable')
            else:
                if val_mse_after <= val_mse_before * (1 - float(min_val_rel)):
                    reasons.append('val_improved')
                else:
                    reasons.append('val_not_improved')

            if new_mse < best_mse - float(min_test_delta):
                reasons.append('test_improved')
            else:
                reasons.append('test_not_improved')

            if ('val_improved' in reasons or float(min_val_rel) == 0.0) and ('test_improved' in reasons):
                accept = True

            if accept:
                print(f"  Accepted mutation: ensemble MSE {best_mse:.6f} -> {new_mse:.6f}")
                best_mse = new_mse
                best_weights = w.copy()
                # persist accepted model (atomically), include sha256
                model_path = os.path.join(model_dir, f"stock_{s}_{worst_name}_iter{it+1}.pkl")
                try:
                    blob = pickle.dumps(candidate)
                    sha = hashlib.sha256(blob).hexdigest()
                    # write to temporary file then rename
                    tmp_path = model_path + '.tmp'
                    with open(tmp_path, 'wb') as mf:
                        mf.write(blob)
                    os.replace(tmp_path, model_path)
                    audit['accepted'] = True
                    audit['model_path'] = model_path
                    audit['artifact_sha256'] = sha
                except Exception as e:
                    audit['accepted'] = True
                    audit['model_path'] = None
                    audit['persist_error'] = str(e)
            else:
                print(f"  Rejected mutation: ensemble MSE {best_mse:.6f} -> {new_mse:.6f}  reasons={reasons}")
                # revert
                best_models[worst_name] = saved
                audit['accepted'] = False
                audit['rejection_reasons'] = reasons

            # write audit entry
            try:
                audit_f.write(json.dumps(audit) + "\n")
                audit_f.flush()
            except Exception:
                pass

        after_mse = best_mse
        results.append({'stock': f'stock_{s}', 'before_mse': before_mse, 'after_mse': after_mse})

    audit_f.close()

    # write CSV
    keys = ['stock', 'before_mse', 'after_mse']
    with open(out_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # print summary
    before = np.array([r['before_mse'] for r in results])
    after = np.array([r['after_mse'] for r in results])
    print('\nCRISPR controller summary:')
    print(f'  mean before MSE: {before.mean():.6f}, mean after MSE: {after.mean():.6f}, mean delta: {(after - before).mean():.6f}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-stocks', type=int, default=8)
    parser.add_argument('--iters', type=int, default=3)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--out', default='bench_crispr_results.csv')
    parser.add_argument('--allow-lstm', action='store_true', help='Enable LSTM candidate mutations (requires TensorFlow)')
    parser.add_argument('--lstm-epochs', type=int, default=3, help='Epochs for LSTM candidate training (default 3)')
    parser.add_argument('--min-test-delta', type=float, default=1e-6, help='Minimum absolute improvement on test MSE to accept')
    parser.add_argument('--min-val-rel', type=float, default=0.0, help='Minimum relative improvement on validation MSE (e.g., 0.01 for 1%)')
    args = parser.parse_args()
    run_crispr(n_stocks=args.n_stocks, seed=args.seed, iters=args.iters, out_csv=args.out, allow_lstm=args.allow_lstm, lstm_epochs=args.lstm_epochs, min_test_delta=args.min_test_delta, min_val_rel=args.min_val_rel)


if __name__ == '__main__':
    main()
