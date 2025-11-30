"""Benchmark across multiple (simulated) stocks and implement an adaptive ensemble (CRISPR-inspired)

The script:
- simulates M correlated stock time series
- creates lag features and trains models per stock
- evaluates models and an adaptive ensemble that updates weights based on recent validation loss
- prints and writes results to `bench_multi_results.csv`

This demonstrates how an adaptive ensemble (a lightweight 'CRISPR' controller) can improve directional accuracy and MSE across stocks.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import xgboost as xgb
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
import warnings
import argparse

warnings.filterwarnings('ignore')

np.random.seed(42)


def make_correlated_series(n_stocks=5, n=2000, base_noise=0.01):
    t = np.arange(n)
    base = 1.0 + 0.0005 * t + 0.02 * np.sin(2 * np.pi * t / 50)
    series = []
    for i in range(n_stocks):
        # each stock has slight idiosyncratic noise and small independent seasonality
        noise = base_noise * (1 + 0.5 * np.random.randn()) * np.random.randn(n)
        idio = 0.01 * np.sin(2 * np.pi * t / (50 + i*5))
        series.append(base + idio + noise)
    return np.array(series)  # shape (n_stocks, n)


def make_lag_features(series, lags=20):
    X = []
    y = []
    for i in range(lags, len(series)):
        X.append(series[i-lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)


def directional_accuracy(y_true, y_pred):
    return np.mean((np.sign(y_pred[1:] - y_pred[:-1]) == np.sign(y_true[1:] - y_true[:-1])).astype(float))


class AdaptiveEnsemble:
    """Simple multiplicative weights ensemble that adapts online using recent loss.
    Weights are updated per-stock based on model squared error on a sliding window of validation data.
    """
    def __init__(self, model_names, eta=0.5):
        self.model_names = list(model_names)
        self.eta = eta
        self.w = np.ones(len(self.model_names)) / len(self.model_names)

    def update(self, preds_matrix, y_true):
        # preds_matrix: (n_models, n_samples)
        # compute mse per model on these samples
        errs = np.mean((preds_matrix - y_true.reshape(1, -1))**2, axis=1)
        # multiplicative weight update
        self.w = self.w * np.exp(-self.eta * errs)
        self.w = self.w / (np.sum(self.w) + 1e-12)

    def predict(self, preds_matrix):
        # weighted average
        return np.dot(self.w, preds_matrix)


def run_simulation(n_stocks=5, n=2000, lags=20):
    series_all = make_correlated_series(n_stocks=n_stocks, n=n)
    overall_rows = []

    # For each stock, train models on its series. We'll then build an ensemble per stock
    for si in range(n_stocks):
        series = series_all[si]
        X, y = make_lag_features(series, lags=lags)
        split = int(0.7 * len(X))
        X_train, X_val, X_test = X[:split], X[split:split+int(0.15*len(X))], X[split+int(0.15*len(X)):]
        y_train, y_val, y_test = y[:split], y[split:split+int(0.15*len(X))], y[split+int(0.15*len(X)):]

        # Train models
        # Persistence baseline: predict last observed value
        persist_val = X_val[:, -1]
        persist_test = X_test[:, -1]

        # Standardize lag features per-stock
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)
        X_test_s = scaler.transform(X_test)

        lr = LinearRegression().fit(X_train_s, y_train)
        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42).fit(X_train_s, y_train)
        xg = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0).fit(X_train_s, y_train)

        # LSTM per-stock (small, few epochs)
        # For LSTM, use standardized features
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
        lstm_val = model.predict(X_val_l).flatten()
        lstm_test = model.predict(X_test_l).flatten()

        model_names = ['persistence', 'linear', 'rf', 'xg', 'lstm']
        preds_val = np.vstack([persist_val, lr.predict(X_val), rf.predict(X_val), xg.predict(X_val), lstm_val])
        preds_test = np.vstack([persist_test, lr.predict(X_test), rf.predict(X_test), xg.predict(X_test), lstm_test])

        # Evaluate individual models on test
        metrics = {}
        for i, name in enumerate(model_names):
            mse = mean_squared_error(y_test, preds_test[i])
            mae = mean_absolute_error(y_test, preds_test[i])
            dir_acc = directional_accuracy(y_test, preds_test[i])
            metrics[name] = (mse, mae, dir_acc)

        # Build adaptive ensemble: initialize on validation preds
        ensemble = AdaptiveEnsemble(model_names, eta=1.0)
        # We'll do online updates using validation data in chunks
        chunk = 20
        for start in range(0, preds_val.shape[1], chunk):
            end = min(start+chunk, preds_val.shape[1])
            ensemble.update(preds_val[:, start:end], y_val[start:end])
        # apply ensemble to test preds
        ens_pred = ensemble.predict(preds_test)
        mse_e = mean_squared_error(y_test, ens_pred)
        mae_e = mean_absolute_error(y_test, ens_pred)
        dir_e = directional_accuracy(y_test, ens_pred)

        # Best individual
        best_name = min(model_names, key=lambda n: metrics[n][0])

        overall_rows.append({
            'stock': f'stock_{si}',
            'best_model': best_name,
            'best_mse': metrics[best_name][0],
            'best_mae': metrics[best_name][1],
            'best_dir_acc': metrics[best_name][2],
            'ens_mse': mse_e,
            'ens_mae': mae_e,
            'ens_dir_acc': dir_e,
            'ens_weights': ','.join([f'{w:.2f}' for w in ensemble.w])
        })

    df = pd.DataFrame(overall_rows)
    out = 'bench_multi_results.csv'
    df.to_csv(out, index=False)
    print(df)
    print('\nWrote', out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-stocks', type=int, default=7)
    args = parser.parse_args()
    run_simulation(n_stocks=args.n_stocks)
