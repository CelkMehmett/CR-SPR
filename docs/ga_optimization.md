# Genetic Algorithm (GA) optimization — guide

This document summarizes how to use the `GeneticAlgorithmEditor` in this
repository, how to collect telemetry, and where to find the demo endpoints.

Quick summary

- The GA editor is implemented in `src/editor/ga_editor.py` as `GeneticAlgorithmEditor`.
- Configure GA behavior via `EditingConfig` (population_size, num_generations, mutation_rate, ...).
- Use `editor.edit(target_site, model_genome)` for single-target edits and
  `editor.batch_edit(targets, model_genome)` for co-evolution across multiple targets.
- After an evolution run, call `editor.get_evolution_statistics()` to obtain
  a rich telemetry dict containing per-generation stats and per-species telemetry
  (`species_best_per_generation` and `species_hall_of_fame`).

Telemetry shape (overview)
`get_evolution_statistics()` returns a dict with keys such as:

- `best_per_generation`: list[float]
- `avg_per_generation`: list[float]
- `diversity_per_generation`: list[float]
- `species_best_per_generation`: dict[int, list[float]]
- `species_hall_of_fame`: dict[int, list[summary]]
- `best_individual`: compact summary of the best individual
- `run_time_seconds`, `run_start_time`, `run_end_time`

Demo server integration
- The proof-of-concept demo server at `poc/presentation_v2/server.py` attaches
  the editor telemetry to the stored snapshot metadata after a run. The demo
  exposes the following endpoints useful for inspecting telemetry:
  - `/current_parameters` — quick snapshot summary (compact parameters + telemetry if available)
  - `/snapshots/<id>` — full persisted snapshot (includes `metadata.telemetry` when present)
  - `/telemetry` — returns only telemetry JSON for the latest in-memory snapshot

Frontend demo
- `poc/presentation_v2/live_demo.html` contains a simple UI. Click "Show Genome"
  to fetch `/current_parameters` and, if available, the UI will offer a "Show edit history"
  view that lazy-loads the full persisted snapshot and renders `telemetry.best_per_generation`.
- The UI also contains a small "Live telemetry" panel that attempts to fetch `/telemetry`
  and render per-species stats and a mini-plot.

MLflow and Optuna
- Optuna scaffolds are available in `src/editor/ga_experiments.py` and can be
  optionally logged to MLflow (guarded imports). See `scripts/run_optuna_with_mlflow.py`.

Enabling MLflow (optional)

- The Optuna/MLflow helpers are intentionally defensive: they will skip logging
  when MLflow is not installed. To enable MLflow logging for Optuna runs or
  demo runs, set the environment variables and run the CLI or server.

  ```bash
  # point to your MLflow tracking server and select an experiment name
  export MLFLOW_TRACKING_URI=http://localhost:5000
  export MLFLOW_EXPERIMENT="crispr-optuna"

  # Example: run the convenience Optuna+MLflow wrapper (Optuna required)
  python scripts/run_optuna_with_mlflow.py --trials 8 --generations 20 --mlflow-experiment "crispr-optuna"
  ```

  If MLflow is not installed, the helpers will return False and the run continues
  normally; no error is raised.

Examples
```python
from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.genome import FinancialGenome

editor = GeneticAlgorithmEditor(config=EditingConfig(population_size=32, num_generations=40))
# ... prepare target sites and model genome
# Run evolution
best = editor._evolve_population(context)
stats = editor.get_evolution_statistics()
print(stats['best_fitness'], stats['total_generations'])
```

Troubleshooting
- `get_evolution_statistics()` returns `{ 'status': 'No evolution history available' }` when
  no evolution has been run yet.
- MLflow and Optuna integrations are optional. If they are not installed, functions
  that attempt to use them will quietly skip logging and return False.

Notes
- The telemetry structures are purposely compact to avoid embedding large arrays in
  snapshots; use the UI endpoints which lazy-load telemetry for richer displays.
