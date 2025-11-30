"""Quick benchmark for financial time-series forecasting comparing several models.

Produces a small CSV with metrics and prints a summary.

Models:
- Persistence (y_t = y_{t-1})
- Linear Regression (lags)
- RandomForestRegressor
- XGBoost (sklearn API)
- Simple LSTM (TensorFlow)

This is synthetic data for speed and reproducibility.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import xgboost as xgb
from tensorflow import keras

np.random.seed(42)

def make_series(n=2000, freq=1.0):
    t = np.arange(n)
    trend = 0.0005 * t
    season = 0.02 * np.sin(2 * np.pi * t / 50) + 0.01 * np.sin(2 * np.pi * t / 200)
    noise = 0.01 * np.random.randn(n)
    series = 1.0 + trend + season + noise
    return series


def make_lag_features(series, lags=10):
    X = []
    y = []
    for i in range(lags, len(series)):
        X.append(series[i-lags:i])
        y.append(series[i])
    return np.array(X), np.array(y)


def persistence_predict(last_values, h=1):
    return np.repeat(last_values[-1:], h)


def eval_preds(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    # directional accuracy
    dir_acc = np.mean((np.sign(y_pred[1:] - y_pred[:-1]) == np.sign(y_true[1:] - y_true[:-1])).astype(float))
    return {'mse': mse, 'mae': mae, 'dir_acc': dir_acc}


def run():
    series = make_series(2500)
    lags = 20
    X, y = make_lag_features(series, lags=lags)
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    results = []

    # Persistence baseline
    last = X_test[:, -1]
    y_pred = last
    results.append(('persistence', eval_preds(y_test, y_pred)))

    # Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_test)
    results.append(('linear', eval_preds(y_test, y_pred)))

    # Random Forest
    rf = RandomForestRegressor(n_estimators=50, random_state=42)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    results.append(('random_forest', eval_preds(y_test, y_pred)))

    # XGBoost
    xg = xgb.XGBRegressor(n_estimators=50, random_state=42, verbosity=0)
    xg.fit(X_train, y_train)
    y_pred = xg.predict(X_test)
    results.append(('xgboost', eval_preds(y_test, y_pred)))

    # LSTM (simple)
    X_train_l = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test_l = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
    model = keras.Sequential([
        keras.layers.Input(shape=(lags, 1)),
        keras.layers.LSTM(32, activation='tanh'),
        keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_train_l, y_train, epochs=5, batch_size=64, verbose=0)
    y_pred = model.predict(X_test_l).flatten()
    results.append(('lstm', eval_preds(y_test, y_pred)))

    # Save results to CSV
    rows = []
    for name, metrics in results:
        rows.append({'model': name, **metrics})
    df = pd.DataFrame(rows)
    out = 'bench_results.csv'
    df.to_csv(out, index=False)
    print(df)
    print('\nWrote', out)

if __name__ == '__main__':
    run()
