"""Optuna experiment runner for GeneticAlgorithmEditor.

Provides a small, safe Optuna integration to tune a handful of GA
hyperparameters. The implementation is defensive: Optuna and MLflow are
optional (imports are guarded) so the module can be imported on systems
without those packages installed.

The runner uses a lightweight default editor factory that instantiates
`GeneticAlgorithmEditor` and seeds a small synthetic population so the
GA can be exercised without depending on external model code.
"""
from typing import Callable, Dict, Optional, Any
import logging
import random
import numpy as np

logger = logging.getLogger(__name__)


def _import_optuna():
    try:
        import optuna
        return optuna
    except Exception:
        return None


def _import_mlflow():
    try:
        import mlflow
        return mlflow
    except Exception:
        return None


def _default_editor_factory(params: Dict[str, Any], seed: Optional[int] = None):
    """Create a minimal GeneticAlgorithmEditor instance configured by params.

    This factory constructs an editor and populates it with a small synthetic
    numeric population so the evolution loop can run quickly for tuning tests.
    """
    # Delay imports to avoid hard dependency at module import time
    from .ga_editor import GeneticAlgorithmEditor, EditingConfig, Individual

    cfg = EditingConfig(
        population_size=int(params.get('population_size', 20)),
        num_generations=int(params.get('num_generations', 20)),
        mutation_rate=float(params.get('mutation_rate', 0.1)),
        crossover_rate=float(params.get('crossover_rate', 0.8)),
        elitism_ratio=float(params.get('elitism_ratio', 0.1)),
    )

    editor = GeneticAlgorithmEditor(name="optuna_temp", config=cfg, seed=seed)

    # Create a simple synthetic population: each genome is a small numeric vector
    editor._population = []
    dim = int(params.get('genome_dim', 3))
    for _ in range(editor.config.population_size):
        vec = np.random.normal(0, 1.0, size=(dim,))
        ind = Individual(genome={'x': vec}, generation=0)
        # Evaluate initial fitness
        ind.fitness = editor.fitness_function.evaluate(ind, None)
        editor._population.append(ind)

    # Initialize best individual
    if editor._population:
        editor._population.sort(key=lambda x: x.fitness, reverse=True)
        editor._best_individual = editor._population[0]

    return editor


def run_optuna_optimization(editor_factory: Optional[Callable[[Dict[str, Any], Optional[int]], Any]] = None,
                            n_trials: int = 20,
                            n_generations: int = 30,
                            seed: Optional[int] = None,
                            use_mlflow: bool = False,
                            mlflow_experiment: Optional[str] = None) -> Any:
    """Run a short Optuna study to tune GA hyperparameters.

    Args:
        editor_factory: callable(params: dict, seed) -> GeneticAlgorithmEditor.
                        If None, a default lightweight factory is used.
        n_trials: number of Optuna trials to run.
        n_generations: number of generations to run the GA for each trial.
        seed: RNG seed for reproducibility.
        use_mlflow: when True, attempts to log params/metrics to MLflow (if installed).
        mlflow_experiment: optional experiment name to create/select in MLflow.

    Returns:
        The Optuna Study object (if Optuna is available). Raises ImportError if
        Optuna is not installed.
    """
    optuna = _import_optuna()
    if optuna is None:
        raise ImportError('optuna is required to run hyperparameter optimization; install optuna to use this feature')

    mlflow = _import_mlflow() if use_mlflow else None

    # Seed deterministic behavior for reproducibility
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    editor_factory = editor_factory or _default_editor_factory

    def objective(trial):
        params = {
            'population_size': trial.suggest_int('population_size', 10, 50),
            'mutation_rate': trial.suggest_float('mutation_rate', 0.01, 0.5),
            'crossover_rate': trial.suggest_float('crossover_rate', 0.5, 1.0),
            'elitism_ratio': trial.suggest_float('elitism_ratio', 0.0, 0.3),
            'genome_dim': trial.suggest_int('genome_dim', 2, 6),
            'num_generations': n_generations
        }

        # Build editor and run a short evolution
        try:
            editor = editor_factory(params, seed)
            # Ensure the editor configuration matches suggested params
            editor.config.num_generations = n_generations
            editor.config.population_size = int(params['population_size'])
            editor.config.mutation_rate = float(params['mutation_rate'])
            editor.config.crossover_rate = float(params['crossover_rate'])

            best = editor._evolve_population(None)

            best_fitness = float(getattr(best, 'fitness', float('-inf')))

            # Optionally log to MLflow
            if mlflow is not None:
                try:
                    if mlflow_experiment:
                        mlflow.set_experiment(mlflow_experiment)
                    with mlflow.start_run(nested=True):
                        mlflow.log_params(params)
                        mlflow.log_metric('best_fitness', best_fitness)
                except Exception:
                    logger.exception('Failed to log to MLflow')

            return best_fitness

        except Exception as e:
            logger.exception('Optuna trial failed: %s', e)
            # Return a very poor fitness so Optuna can continue
            return float('-1e9')

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    return study


__all__ = ['run_optuna_optimization']


def log_optuna_study_to_mlflow(study: Any, mlflow_client: Optional[Any] = None, experiment_name: Optional[str] = None) -> bool:
    """Log an Optuna Study summary and trials as an artifact to MLflow (guarded).

    Args:
        study: Optuna Study instance
        mlflow_client: optional mlflow module instance (if None, will attempt import)
        experiment_name: optional MLflow experiment name to select/create

    Returns:
        True if logging succeeded (or was attempted), False if MLflow not available.
    """
    try:
        mlflow = mlflow_client
        if mlflow is None:
            try:
                import mlflow  # type: ignore
                mlflow = mlflow
            except Exception:
                logger.info('MLflow not available; skipping study logging')
                return False

        # Prepare summary
        summary = {
            'best_params': getattr(study, 'best_params', None),
            'best_value': float(getattr(study, 'best_value', float('nan'))),
            'n_trials': len(getattr(study, 'trials', [])) if hasattr(study, 'trials') else None,
            'direction': getattr(study, 'direction', None)
        }

        # If possible, get a trials dataframe
        trials_df = None
        try:
            trials_df = study.trials_dataframe()
        except Exception:
            try:
                import pandas as pd
                trials_df = pd.DataFrame([{
                    'number': t.number,
                    'value': getattr(t, 'value', None),
                    'params': getattr(t, 'params', None),
                    'state': str(getattr(t, 'state', None))
                } for t in getattr(study, 'trials', [])])
            except Exception:
                trials_df = None

        # Start MLflow run and log
        try:
            if experiment_name:
                try:
                    mlflow.set_experiment(experiment_name)
                except Exception:
                    logger.exception('Failed to set MLflow experiment %s', experiment_name)

            with mlflow.start_run() as run:
                try:
                    mlflow.log_params({'n_trials': summary.get('n_trials', 0)})
                except Exception:
                    logger.exception('Failed to log MLflow params for study')

                try:
                    mlflow.log_metric('best_value', float(summary.get('best_value', float('nan'))))
                except Exception:
                    logger.exception('Failed to log MLflow metric best_value')

                # Persist summary and trials as artifacts
                try:
                    import json
                    import tempfile
                    tmp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                    json.dump(summary, tmp, default=str)
                    tmp.flush(); tmp.close()
                    mlflow.log_artifact(tmp.name, artifact_path='optuna_study')
                except Exception:
                    logger.exception('Failed to log study summary artifact to MLflow')

                if trials_df is not None:
                    try:
                        import tempfile
                        tmpcsv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
                        trials_df.to_csv(tmpcsv.name, index=False)
                        tmpcsv.close()
                        mlflow.log_artifact(tmpcsv.name, artifact_path='optuna_study')
                    except Exception:
                        logger.exception('Failed to log trials dataframe artifact to MLflow')

            return True
        except Exception:
            logger.exception('Failed to create MLflow run for study')
            return False
    except Exception:
        logger.exception('Unexpected error in log_optuna_study_to_mlflow')
        return False


def run_optuna_with_mlflow(*, n_trials: int = 20, n_generations: int = 20, seed: Optional[int] = None, mlflow_experiment: Optional[str] = None) -> Optional[Any]:
    """Run an Optuna study and attempt to log the full study to MLflow (if available).

    This convenience wrapper uses `run_optuna_optimization` and then calls
    `log_optuna_study_to_mlflow` to persist study-level artifacts.
    """
    try:
        study = run_optuna_optimization(n_trials=n_trials, n_generations=n_generations, seed=seed, use_mlflow=False)
    except Exception:
        logger.exception('Failed to run optuna optimization')
        return None

    # Attempt to log the study as a single artifact/run in MLflow
    try:
        ok = log_optuna_study_to_mlflow(study, mlflow_client=None, experiment_name=mlflow_experiment)
        if ok:
            logger.info('Optuna study logged to MLflow')
    except Exception:
        logger.exception('Failed to log optuna study to MLflow')

    return study
"""Optuna experiment runner for GA hyperparameter tuning.

This module provides a small, safe-to-import runner that will use Optuna
(if available) to tune a handful of GA hyperparameters. It is intentionally
lightweight and guarded so the repository and tests don't require Optuna
unless the user opts in.

Usage:
    from src.editor.ga_experiments import run_optuna_smoke
    run_optuna_smoke(trials=8)

The runner will use `GeneticEditor` from `src/editor/ga_editor.py` and
save checkpoints using the editor's `save_checkpoint` method.
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def _has_optuna():
    try:
        return True
    except Exception:
        return False


def run_optuna_smoke(trials: int = 8, timeout: Optional[float] = 30.0) -> None:
    """Run a short Optuna study to tune GA hyperparameters.

    If Optuna is not installed this function logs a message and returns.
    The objective is intentionally cheap: run a tiny GA for a handful of
    generations and return the best fitness as the value to minimize.
    """
    if not _has_optuna():
        logger.info("Optuna not installed; skipping Optuna smoke run.")
        return

    import optuna  # type: ignore
    # Importing local GeneticAlgorithmEditor
    try:
        from src.editor.ga_editor import GeneticAlgorithmEditor
    except Exception:
        try:
            # Fallback import path used in some test runners
            from editor.ga_editor import GeneticAlgorithmEditor  # type: ignore
        except Exception:
            logger.exception("Failed importing GeneticAlgorithmEditor; cannot run Optuna smoke")
            return

    def objective(trial: "optuna.trial.Trial") -> float:  # type: ignore
        # Define search space
        population_size = trial.suggest_int('population_size', 8, 64)
        edit_rate = trial.suggest_float('edit_rate', 0.01, 0.5)

        # Small, fast GA run
        editor = GeneticAlgorithmEditor(name='optuna-smoke', edit_rate=edit_rate)
        editor.config.population_size = population_size

        # Run a tiny evolution (keep inexpensive)
        try:
            best = editor._evolve_population({'max_generations': 5})
            # If best individual has .fitness attribute, use it; otherwise, return a default
            fitness = getattr(best, 'fitness', None)
            if fitness is None:
                return float('inf')
            return float(fitness)
        except Exception:
            logger.exception('Optuna objective failed during GA run')
            return float('inf')

    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=trials, timeout=timeout)

    logger.info('Optuna smoke study finished. Best params: %s', study.best_params)


if __name__ == '__main__':
    # Simple CLI smoke runner
    run_optuna_smoke(trials=4, timeout=20.0)
