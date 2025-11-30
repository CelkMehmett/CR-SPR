"""Quick diagnostic to inspect prediction distributions for each model on synthetic stocks.

Prints basic stats (mean/std/min/max/unique count) for test predictions.
"""
import numpy as np
import sys
import pathlib

# ensure repository root is on sys.path for local imports
ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from tensorflow import keras

np.random.seed(0)

# reuse data generators from bench scripts for consistency
from scripts.bench_multi_stocks import make_correlated_series, make_lag_features

series_all = make_correlated_series(n_stocks=2, n=800)
for si in range(2):
    series = series_all[si]
    X, y = make_lag_features(series, lags=20)
    split = int(0.7 * len(X))
    X_train, X_val, X_test = X[:split], X[split:split+int(0.15*len(X))], X[split+int(0.15*len(X)):]
    y_train, y_val, y_test = y[:split], y[split:split+int(0.15*len(X))], y[split+int(0.15*len(X)):]

    # persistence
    persist_test = X_test[:, -1]

    lr = LinearRegression().fit(X_train, y_train)
    rf = RandomForestRegressor(n_estimators=20, random_state=42).fit(X_train, y_train)
    xg = xgb.XGBRegressor(n_estimators=20, random_state=42, verbosity=0).fit(X_train, y_train)

    # small LSTM
    X_train_l = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test_l = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
    model = keras.Sequential([
        keras.layers.Input(shape=(20,1)),
        keras.layers.LSTM(16),
        keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_train_l, y_train, epochs=3, batch_size=64, verbose=0)

    preds = {
        'persistence': persist_test,
        'linear': lr.predict(X_test),
        'rf': rf.predict(X_test),
        'xg': xg.predict(X_test),
        'lstm': model.predict(X_test_l).flatten()
    }

    print('Stock', si)
    for name, arr in preds.items():
        print(name, 'mean', arr.mean(), 'std', arr.std(), 'min', arr.min(), 'max', arr.max(), 'unique', len(np.unique(np.round(arr,6))))
    print('\n')
