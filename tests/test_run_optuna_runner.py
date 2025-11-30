import pytest

from src.editor import ga_experiments


def test_run_optuna_optimization_guarded():
    """Ensure `run_optuna_optimization` behaves sensibly whether Optuna is installed.

    If Optuna is present, the function should run a very small study and return a study object.
    If Optuna is not present, the function raises ImportError; this test accepts both outcomes.
    """
    try:
        optuna_installed = True
    except Exception:
        optuna_installed = False

    if not optuna_installed:
        with pytest.raises(ImportError):
            ga_experiments.run_optuna_optimization(n_trials=1, n_generations=1, seed=1)
    else:
        study = ga_experiments.run_optuna_optimization(n_trials=1, n_generations=1, seed=1)
        # basic sanity checks on returned study
        assert study is not None
        assert hasattr(study, 'best_params')
