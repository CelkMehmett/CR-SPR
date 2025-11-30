"""Lightweight CI-friendly benchmark for GA evaluation speed.

This script runs a tiny synthetic benchmark comparing sequential vs simple
multiprocessing evaluation of a population with an artificially expensive
fitness function. It writes results to `benchmarks/ci_benchmark_results.csv`.

Designed for CI: small population and short sleeps so the job is quick.
"""
import time
import csv
import os
from multiprocessing import Pool

from src.editor.ga_editor import Individual


def expensive_eval(individual):
    # Simulate a modestly expensive evaluation
    time.sleep(0.01)
    # Compute a deterministic metric from the genome
    g = individual.genome.get('x', 0)
    try:
        return float(g) * 0.5
    except Exception:
        return 0.0


def sequential_eval(pop):
    t0 = time.perf_counter()
    res = [expensive_eval(ind) for ind in pop]
    t1 = time.perf_counter()
    return (t1 - t0), res


def multiprocessing_eval(pop, workers=2):
    t0 = time.perf_counter()
    with Pool(processes=workers) as p:
        res = p.map(expensive_eval, pop)
    t1 = time.perf_counter()
    return (t1 - t0), res


def make_population(n):
    pop = []
    for i in range(n):
        ind = Individual(genome={'x': float(i)}, fitness=0.0)
        pop.append(ind)
    return pop


def run_benchmark(pop_size=20, trials=3, workers=2):
    out_rows = []
    for t in range(trials):
        pop = make_population(pop_size)
        seq_time, _ = sequential_eval(pop)
        mp_time, _ = multiprocessing_eval(pop, workers=workers)
        out_rows.append({'trial': t, 'pop_size': pop_size, 'workers': workers, 'sequential_sec': seq_time, 'multiproc_sec': mp_time})
    return out_rows


def write_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keys = rows[0].keys() if rows else ['trial']
    with open(path, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(keys))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


if __name__ == '__main__':
    # Small default values to keep CI runtime short
    POP = int(os.getenv('CI_BENCH_POP', '20'))
    TRIALS = int(os.getenv('CI_BENCH_TRIALS', '3'))
    WORKERS = int(os.getenv('CI_BENCH_WORKERS', '2'))

    rows = run_benchmark(pop_size=POP, trials=TRIALS, workers=WORKERS)
    out = os.path.join(os.path.dirname(__file__), 'ci_benchmark_results.csv')
    write_csv(rows, out)
    print('Wrote benchmark results to', out)
