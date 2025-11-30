
from src.editor.ga_experiments import run_optuna_smoke


def test_optuna_scaffold_runs_without_optuna():
    """Calling run_optuna_smoke should not raise whether or not optuna is installed.

    If Optuna is installed, the function will run a small study; otherwise it
    logs and returns early. The test ensures the call is safe.
    """
    # Should not raise
    run_optuna_smoke(trials=2, timeout=5)
    assert True
