"""Optuna + MLflow helper for GA hyperparameter tuning.

This module is safe to import; it will no-op if Optuna or MLflow aren't
installed. It provides `run_optuna_with_mlflow` which runs a small Optuna
study and logs the best trial to MLflow if available.

The implementation is intentionally minimal and guarded so it won't break
tests or environments that don't have those optional deps installed.
"""
from typing import Optional
import logging
import tempfile
import os

logger = logging.getLogger(__name__)


def _has_pkg(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def run_optuna_with_mlflow(trials: int = 8, timeout: Optional[float] = 60.0) -> None:
    """Run a small Optuna study and, if available, log the results to MLflow.

    Behavior:
    - If Optuna isn't installed: logs and returns.
    - If MLflow isn't installed: runs the study but skips MLflow logging.

    The objective used here is intentionally lightweight and uses the
    `GeneticAlgorithmEditor` to run a very short GA to produce a fitness.
    """
    if not _has_pkg('optuna'):
        logger.info('optuna not installed; skipping run_optuna_with_mlflow')
        return

    import optuna  # type: ignore

    has_mlflow = _has_pkg('mlflow')
    if has_mlflow:
        import mlflow  # type: ignore

    # Import GA editor in a guarded manner (work across different PYTHONPATH setups)
    try:
        from src.editor.ga_editor import GeneticAlgorithmEditor
    except Exception:
        try:
            from editor.ga_editor import GeneticAlgorithmEditor  # type: ignore
        except Exception:
            logger.exception('Could not import GeneticAlgorithmEditor; aborting Optuna run')
            return

    def objective(trial: "optuna.trial.Trial") -> float:  # type: ignore
        population_size = trial.suggest_int('population_size', 8, 64)
        edit_rate = trial.suggest_float('edit_rate', 0.01, 0.5)

        editor = GeneticAlgorithmEditor(name='optuna-mlflow', edit_rate=edit_rate)
        editor.config.population_size = population_size

        try:
            best = editor._evolve_population({'max_generations': 5})
            fitness = getattr(best, 'fitness', None)
            if fitness is None:
                return float('inf')
            return float(fitness)
        except Exception:
            logger.exception('Error while running GA objective')
            return float('inf')

    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=trials, timeout=timeout)

    logger.info('Optuna study completed; best_value=%s best_params=%s', study.best_value, study.best_params)

    if has_mlflow:
        try:
            import mlflow  # type: ignore
            # Create a temporary artifact (pickle the study) and log it
            try:
                import pickle
                tmpf = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
                with open(tmpf.name, 'wb') as fh:
                    pickle.dump(study, fh)
                mlflow.start_run()
                mlflow.log_params(study.best_params or {})
                mlflow.log_metric('best_value', float(study.best_value))
                mlflow.log_artifact(tmpf.name, artifact_path='optuna')
                mlflow.end_run()
                logger.info('Logged Optuna study to MLflow (artifact: %s)', tmpf.name)
            except Exception:
                logger.exception('Failed to pickle/log study to MLflow')
            finally:
                try:
                    os.unlink(tmpf.name)
                except Exception:
                    pass
        except Exception:
            logger.exception('MLflow logging failed')
