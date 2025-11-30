import math
import pytest

optuna = pytest.importorskip('optuna')

from src.editor.ga_experiments import run_optuna_optimization


def test_optuna_runs_short_study():
    # Run a tiny study to ensure the integration works. Keep it short so CI is fast.
    study = run_optuna_optimization(n_trials=3, n_generations=5, seed=42)

    assert hasattr(study, 'best_value')
    assert isinstance(study.best_value, float)
    assert not math.isnan(study.best_value)
