"""Run a short Optuna study using the GA Optuna runner and persist results.

The script uses `src.editor.ga_experiments.run_optuna_optimization` to run a
small study and writes a one-line CSV summary with the best value and params.

MLflow is optional and guarded by the ga_experiments implementation.
"""
import csv
import argparse
import json

from src.editor.ga_experiments import run_optuna_optimization


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=5)
    parser.add_argument('--generations', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', type=str, default='benchmarks/optuna_results.csv')
    args = parser.parse_args()

    study = run_optuna_optimization(n_trials=args.trials, n_generations=args.generations, seed=args.seed)

    # Write a CSV with best_value and best_params (json-encoded)
    row = {
        'best_value': float(study.best_value) if study.best_value is not None else '',
        'best_params': json.dumps(study.best_params) if hasattr(study, 'best_params') else ''
    }

    with open(args.out, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['best_value', 'best_params'])
        writer.writeheader()
        writer.writerow(row)

    print(f"Wrote Optuna summary to: {args.out}")


if __name__ == '__main__':
    main()
