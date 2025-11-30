"""
Portfolio optimization helpers.

Includes:
- mean_variance_optimize: maximize Sharpe via random search (small demo-friendly)
- risk_parity_weights: approximate risk-parity allocation
- kelly_fraction: compute Kelly fraction from mean/var

This is a lightweight module intended for demo and integration; for
production use, replace random-search with convex/QP solver.
"""
from typing import Dict
import numpy as np


def portfolio_return(weights: np.ndarray, returns: np.ndarray) -> float:
    """Compute portfolio mean return given asset returns (T x N)."""
    mean = returns.mean(axis=0)
    return float(np.dot(weights, mean))


def portfolio_vol(weights: np.ndarray, returns: np.ndarray) -> float:
    cov = np.cov(returns, rowvar=False)
    return float(np.sqrt(weights.T @ cov @ weights))


def sharpe_ratio(weights: np.ndarray, returns: np.ndarray, risk_free: float = 0.0) -> float:
    mu = portfolio_return(weights, returns)
    vol = portfolio_vol(weights, returns)
    if vol == 0:
        return 0.0
    return (mu - risk_free) / vol


def mean_variance_optimize(returns: np.ndarray, n_iter: int = 20000, risk_free: float = 0.0) -> Dict:
    """Simple random-search mean-variance optimizer that returns max Sharpe weights.

    returns: numpy array T x N
    """
    T, N = returns.shape
    best = {'sharpe': -1e9, 'weights': None}
    rng = np.random.default_rng(42)
    for _ in range(n_iter):
        w = rng.random(N)
        w = w / w.sum()
        s = sharpe_ratio(w, returns, risk_free)
        if s > best['sharpe']:
            best['sharpe'] = s
            best['weights'] = w

    return best


def risk_parity_weights(returns: np.ndarray, max_iter: int = 1000, tol: float = 1e-6) -> Dict:
    """Approximate risk parity weights using iterative scaling.

    Returns normalized weights that attempt to equalize asset risk contributions.
    """
    cov = np.cov(returns, rowvar=False)
    N = cov.shape[0]
    w = np.ones(N) / N
    for i in range(max_iter):
        sigma_p = np.sqrt(w.T @ cov @ w)
        # risk contributions
        rc = (w * (cov @ w)) / sigma_p
        # desired equal risk contributions
        target = np.full(N, sigma_p / N)
        # adjustment
        grad = rc - target
        # simple update
        w = w - 0.1 * grad
        w = np.maximum(w, 1e-8)
        w = w / w.sum()
        if np.linalg.norm(grad) < tol:
            break

    return {'weights': w, 'iterations': i}


def kelly_fraction(mu: np.ndarray, sigma2: np.ndarray) -> np.ndarray:
    """Compute Kelly fraction for independent assets (approx): f* = mu / sigma2

    mu: expected returns vector
    sigma2: variances vector
    """
    f = mu / sigma2
    # clip to reasonable values
    f = np.clip(f, -1.0, 1.0)
    return f


def demo():
    # synthetic returns: 3 assets
    rng = np.random.default_rng(1)
    T = 504
    mu = np.array([0.12 / 252, 0.08 / 252, 0.15 / 252])  # daily means
    sig = np.array([0.18, 0.22, 0.25]) / np.sqrt(252)
    returns = rng.normal(mu, sig, size=(T, 3))

    print("Running mean-variance optimizer (random search)...")
    best = mean_variance_optimize(returns, n_iter=5000)
    print(f"Best Sharpe: {best['sharpe']:.3f}")
    print(f"Weights: {best['weights']}")

    print("\nRisk parity (approx)...")
    rp = risk_parity_weights(returns)
    print(f"RP Weights: {rp['weights']} (iter {rp['iterations']})")

    print("\nKelly fractions (approx)...")
    mu_ann = returns.mean(axis=0) * 252
    var = returns.var(axis=0) * 252
    kf = kelly_fraction(mu_ann, var)
    print(f"Kelly fractions: {kf}")


if __name__ == '__main__':
    demo()
