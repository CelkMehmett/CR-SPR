"""Small CLI to run the Optuna GA hyperparameter optimizer example.

This script is intentionally lightweight and defensive: it will detect whether
Optuna (and optionally MLflow) are installed and print helpful instructions
if not. Use it as a quick manual runner locally.

Example:
    python scripts/run_optuna_example.py --trials 8 --generations 20
"""
import argparse
import logging

from src.editor.ga_experiments import run_optuna_optimization

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Run Optuna hyperparameter tuning for the GA editor')
    parser.add_argument('--trials', type=int, default=8)
    parser.add_argument('--generations', type=int, default=20)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--use-mlflow', action='store_true', help='Attempt to log trials to MLflow if available')
    parser.add_argument('--mlflow-experiment', type=str, default=None)
    args = parser.parse_args()

    try:
        study = run_optuna_optimization(
            editor_factory=None,
            n_trials=args.trials,
            n_generations=args.generations,
            seed=args.seed,
            use_mlflow=args.use_mlflow,
            mlflow_experiment=args.mlflow_experiment
        )
        print('Optuna study completed. Best params:')
        try:
            print(study.best_params)
        except Exception:
            print('Study returned but best_params not available (unexpected)')
    except ImportError as e:
        logger.error('Optuna is not installed: %s', e)
        logger.info('Install Optuna with: pip install optuna')
    except Exception as e:
        logger.exception('Optuna run failed: %s', e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
