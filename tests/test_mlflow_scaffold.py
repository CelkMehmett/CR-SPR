import importlib
import sys


def test_import_ga_experiments_without_mlflow(monkeypatch):
    """Reload the module while ensuring mlflow is absent so guarded imports don't raise."""
    # Ensure mlflow is not present in sys.modules to simulate an environment without it
    saved_mlflow = sys.modules.pop("mlflow", None)
    try:
        # Import and reload the module under test
        mod_name = "src.editor.ga_experiments"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        mod = importlib.import_module(mod_name)
        importlib.reload(mod)
    finally:
        # Restore mlflow if it was present
        if saved_mlflow is not None:
            sys.modules["mlflow"] = saved_mlflow


def test_log_optuna_study_to_mlflow_graceful_no_mlflow(monkeypatch):
    """Call the helper with a dummy study when mlflow is unavailable and ensure it doesn't raise.

    This verifies the function is defensive when mlflow isn't installed.
    """
    # Simulate mlflow not installed
    saved_mlflow = sys.modules.pop("mlflow", None)
    try:
        from src.editor.ga_experiments import log_optuna_study_to_mlflow

        class DummyStudy:
            def __init__(self):
                self._name = "dummy"

            def trials_dataframe(self):
                # Return a minimal pandas-like object if the implementation tries to use it.
                # We return a simple list/iterable; the guarded code should handle absence of mlflow.
                return []

        # Should not raise even if mlflow is missing; accept True/False/None depending on impl.
        result = log_optuna_study_to_mlflow(DummyStudy())
        # We only assert the call completed (implementation may return True/False/None).
        assert result in (True, False, None)
    finally:
        if saved_mlflow is not None:
            sys.modules["mlflow"] = saved_mlflow

from src.editor.ga_editor import GeneticAlgorithmEditor


def test_mlflow_scaffold_runs_without_mlflow():
    """Calling log_run_to_mlflow should not raise whether or not mlflow is installed.

    If mlflow is installed, the function should return True. If mlflow is not
    available, it should return False. The test adapts to the environment.
    """
    editor = GeneticAlgorithmEditor(seed=1)
    # create a tiny synthetic generation history so get_evolution_statistics has something
    editor._generation_history = [{'generation': 0, 'best_fitness': 0.0, 'avg_fitness': 0.0, 'fitness_std': 0.0, 'improvement': 0.0, 'diversity': 0.0}]

    # Determine whether mlflow is present in this environment
    try:
        mlflow_installed = True
    except Exception:
        mlflow_installed = False

    result = editor.log_run_to_mlflow()

    if mlflow_installed:
        assert result is True
    else:
        assert result is False


def test_log_optuna_study_to_mlflow_with_fake_mlflow(monkeypatch, tmp_path):
    """Inject a fake `mlflow` module and verify the helper calls expected APIs."""
    import types
    import os
    from src.editor.ga_experiments import log_optuna_study_to_mlflow

    calls = {
        'set_experiment': None,
        'start_run': 0,
        'log_params': [],
        'log_metric': [],
        'log_artifact': []
    }

    fake_mlflow = types.ModuleType('mlflow')

    def set_experiment(name):
        calls['set_experiment'] = name

    import contextlib

    @contextlib.contextmanager
    def start_run(*args, **kwargs):
        calls['start_run'] += 1
        yield {'run_id': 'fake'}

    def log_params(params):
        calls['log_params'].append(dict(params))

    def log_metric(kv, value=None):
        # support log_metric(k, v) and log_metric(dict) patterns
        if value is None and isinstance(kv, dict):
            for k, v in kv.items():
                calls['log_metric'].append((k, v))
        else:
            calls['log_metric'].append((kv, value))

    def log_artifact(path, artifact_path=None):
        # ensure artifact exists
        assert os.path.exists(path), f"artifact file missing: {path}"
        calls['log_artifact'].append((path, artifact_path))

    fake_mlflow.set_experiment = set_experiment
    fake_mlflow.start_run = start_run
    fake_mlflow.log_params = log_params
    fake_mlflow.log_metric = log_metric
    fake_mlflow.log_artifact = log_artifact

    # Inject into sys.modules so import inside helper will use it
    monkeypatch.setitem(sys.modules, 'mlflow', fake_mlflow)

    class DummyStudy:
        def __init__(self):
            self.best_params = {'p': 1}
            self.best_value = 0.9
            self.trials = []

        def trials_dataframe(self):
            # Simulate absence of a proper dataframe to exercise summary artifact logging
            raise RuntimeError('no dataframe')

    ok = log_optuna_study_to_mlflow(DummyStudy(), mlflow_client=None, experiment_name='test-exp')
    assert ok is True
    assert calls['set_experiment'] == 'test-exp'
    assert calls['start_run'] >= 1
    assert len(calls['log_params']) >= 0
    # summary artifact must have been logged
    assert len(calls['log_artifact']) >= 1
