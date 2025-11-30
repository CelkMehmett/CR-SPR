# Optuna hyperparameter tuning for CRISPR GA

This document explains how to run Optuna to tune the GA in this repository.

Prerequisites
- Python environment with `optuna` installed for full functionality.
- Optional: `mlflow` if you want to log trials.

Quick start

```bash
# install optuna (optional for full runs)
pip install optuna

# run a small example (will skip if Optuna not installed)
python scripts/run_optuna_example.py --trials 8 --generations 20
```

Details
- The example script calls `src.editor.ga_experiments.run_optuna_optimization`.
- The Optuna runner is defensive: importing `optuna` is optional for the package import,
  but running the full tuning function requires Optuna.
- When MLflow is available and `--use-mlflow` is passed, trials will be logged to MLflow.

Notes for CI
- Optuna studies can be computationally expensive. Use a minimal trial count in CI
  (e.g. 2-4 trials) and small population/generation sizes.
- Tests in this repo include a smoke test that runs the Optuna scaffold and will
  pass regardless of whether Optuna is installed (it will early-return when missing).

Example CLI

```bash
# run the convenience CLI which will run an Optuna study and attempt to log it to MLflow
python scripts/run_optuna_with_mlflow.py --trials 8 --generations 20 --mlflow-experiment "GA_Optuna"
```
