"""Surrogate-assisted evaluation helpers (optional LightGBM/Sklearn).

This module provides a small, defensive wrapper to train a regression
surrogate model that maps flattened numeric genome vectors to fitness.
It is optional: if LightGBM or scikit-learn are not available, the API
returns None or raises ImportError depending on caller preference.

API:
  is_surrogate_available() -> bool
  train_surrogate(population: List[Individual]) -> model or None
  predict_surrogate(model, population: List[Individual]) -> List[float]

The implementation is deliberately small and safe to import in CI/dev
environments that don't have ML libraries installed.
"""
from typing import Any, List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


def _import_lightgbm():
    try:
        import lightgbm as lgb  # type: ignore

        return lgb
    except Exception:
        return None


def _import_sklearn():
    try:
        from sklearn.ensemble import RandomForestRegressor  # type: ignore

        return RandomForestRegressor
    except Exception:
        return None


def is_surrogate_available() -> bool:
    """Return True when at least one supported estimator is importable."""
    return _import_lightgbm() is not None or _import_sklearn() is not None


def _genome_to_vector(genome: dict) -> Optional[np.ndarray]:
    vec = []
    for k, v in genome.items():
        if isinstance(v, (int, float)):
            vec.append(float(v))
        elif isinstance(v, np.ndarray):
            try:
                flat = v.flatten().astype(float)
                vec.extend(flat.tolist())
            except Exception:
                continue
        # skip non-numeric
    if not vec:
        return None
    return np.array(vec, dtype=float)


def _build_design_matrix(population: List[Any]):
    X = []
    y = []
    for ind in population:
        v = _genome_to_vector(ind.genome)
        if v is None:
            continue
        X.append(v)
        y.append(float(getattr(ind, 'fitness', 0.0)))

    if not X:
        return None, None

    # pad to equal length
    max_len = max(x.shape[0] for x in X)
    Xmat = np.zeros((len(X), max_len), dtype=float)
    for i, x in enumerate(X):
        Xmat[i, : x.shape[0]] = x
    return Xmat, np.array(y, dtype=float)


def train_surrogate(population: List[Any], max_estimators: int = 50) -> Optional[Any]:
    """Train a surrogate regressor on the given population.

    Returns a fitted model instance or None if no supported library is
    available or there is insufficient numeric data.
    """
    X, y = _build_design_matrix(population)
    if X is None or y is None or len(y) < 3:
        logger.debug('Insufficient data to train surrogate (need >=3 examples)')
        return None

    lgb = _import_lightgbm()
    if lgb is not None:
        try:
            model = lgb.LGBMRegressor(n_estimators=max_estimators)
            model.fit(X, y)
            return model
        except Exception:
            logger.exception('LightGBM training failed; falling back')

    SkR = _import_sklearn()
    if SkR is not None:
        try:
            model = SkR(n_estimators= max(10, min(200, max_estimators)))
            model.fit(X, y)
            return model
        except Exception:
            logger.exception('Sklearn RandomForest training failed')

    logger.info('No surrogate backend available or training failed')
    return None


def predict_surrogate(model: Any, population: List[Any]) -> Optional[List[float]]:
    """Predict fitness for a list of individuals using the surrogate model.

    Returns a list of floats or None if model is None or predictions fail.
    """
    if model is None:
        return None
    X, _ = _build_design_matrix(population)
    if X is None:
        return None
    try:
        preds = model.predict(X)
        return [float(p) for p in preds]
    except Exception:
        logger.exception('Surrogate predict failed')
        return None
