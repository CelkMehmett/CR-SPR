#!/usr/bin/env python3
"""Example CLI to run an Optuna study and optionally log results to MLflow.

This script is intentionally lightweight and guarded: Optuna and MLflow are
optional. If Optuna is not installed the script will exit with a helpful message.
"""
import argparse
import logging
import sys
import os

# Ensure repository root is on sys.path so src imports work regardless of cwd
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run Optuna study for GA and optionally log to MLflow')
    parser.add_argument('--trials', type=int, default=8, help='Number of Optuna trials')
    parser.add_argument('--generations', type=int, default=20, help='Number of GA generations per trial')
    parser.add_argument('--seed', type=int, default=None, help='Random seed (optional)')
    parser.add_argument('--mlflow-experiment', type=str, default=None, help='MLflow experiment name to log study')
    parser.add_argument('--show-best', action='store_true', help='Print best params/value at the end')

    args = parser.parse_args(argv)

    try:
        from src.editor.ga_experiments import run_optuna_with_mlflow
    except Exception as e:
        logging.error('Failed to import Optuna runner: %s', e)
        logging.error('Ensure you have the repository on PYTHONPATH and optuna installed for full functionality.')
        sys.exit(2)

    study = run_optuna_with_mlflow(n_trials=args.trials, n_generations=args.generations, seed=args.seed, mlflow_experiment=args.mlflow_experiment)

    if study is None:
        logging.error('Study did not complete or Optuna is not available')
        sys.exit(1)

    if args.show_best:
        try:
            logging.info('Best params: %s', getattr(study, 'best_params', None))
            logging.info('Best value: %s', getattr(study, 'best_value', None))
        except Exception:
            pass

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
