"""Compare multiprocessing evaluator vs Ray evaluator (if available).

This lightweight benchmark runs a synthetic expensive fitness over a small
population and measures wall-clock time for different backends/workers.
Results are written to `benchmarks/ray_vs_mp_results.csv`.

The script is defensive: if Ray is not installed, Ray rows are recorded as
skipped rather than failing.
"""
import time
import csv
import argparse
import numpy as np
from typing import List

from src.editor.evaluators import evaluate_population


def expensive_fitness(individual, ctx):
    # individual is a numpy vector; do a moderate amount of work
    x = individual
    # simulate CPU work: a few matrix ops and a loop
    s = 0.0
    for _ in range(8):
        s += float(np.dot(x, x) / (np.linalg.norm(x) + 1e-6))
        x = np.tanh(x * 1.0001)
    return -s


def _worker_wrapper(ind, ctx):
    # simple wrapper to keep a top-level callable for multiprocessing/pickling
    return expensive_fitness(ind, ctx)


def run_mp(population: List[np.ndarray], workers: int):
    start = time.time()
    # Pass a top-level callable to avoid multiprocessing pickling issues
    fitnesses = evaluate_population(population, _worker_wrapper, context=None, workers=workers)
    return time.time() - start, fitnesses


def run_ray(population: List[np.ndarray]):
    try:
        from src.editor.evaluators_ray import evaluate_population_ray
    except Exception:
        return None, None

    start = time.time()
    try:
        fitnesses = evaluate_population_ray(population, _worker_wrapper, context=None, batch_size=32, reuse_actors=False)
        return time.time() - start, fitnesses
    except Exception:
        # Ray not available or evaluation failed
        return None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--population', type=int, default=50)
    parser.add_argument('--dim', type=int, default=64)
    parser.add_argument('--workers', type=str, default='1,2,4')
    parser.add_argument('--out', type=str, default='benchmarks/ray_vs_mp_results.csv')
    args = parser.parse_args()

    pop_size = args.population
    dim = args.dim
    workers_list = [int(x) for x in args.workers.split(',') if x.strip()]

    # Create synthetic population
    population = [np.random.normal(0, 1.0, size=(dim,)) for _ in range(pop_size)]

    rows = []

    # Multiprocessing runs
    for w in workers_list:
        t, _ = run_mp(population, workers=w)
        rows.append({'backend': 'multiprocessing', 'workers': w, 'time_s': t, 'note': ''})

    # Ray run (single entry) - record skipped if not available
    ray_time, _ = run_ray(population)
    if ray_time is None:
        rows.append({'backend': 'ray', 'workers': 'auto', 'time_s': None, 'note': 'ray_not_available'})
    else:
        rows.append({'backend': 'ray', 'workers': 'auto', 'time_s': ray_time, 'note': ''})

    # Write CSV
    out_path = args.out
    with open(out_path, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['backend', 'workers', 'time_s', 'note'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote benchmark results to: {out_path}")


if __name__ == '__main__':
    main()
