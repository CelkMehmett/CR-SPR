"""Small benchmark harness comparing serial vs parallel evaluation

Usage (from repository root):
    python3 benchmarks/run_benchmark.py

It uses `src.editor.evaluators.evaluate_population` and a synthetic
CPU-bound fitness function to measure wall-clock time for evaluation of a
population.
"""
import time
import math
import argparse
import csv
from collections.abc import Sequence
from src.editor.evaluators import evaluate_population


def expensive_fitness(x, context=None):
    # Synthetic CPU-bound workload: compute a sum of sines over many iterations
    n = context.get('work', 20000) if context else 20000
    s = 0.0
    v = float(x)
    for i in range(n):
        s += math.sin(v * (i + 1)) * math.cos(v / (i + 1))
    return s


def run_once(pop_size: int, work: int, workers_list: Sequence[int]):
    pop = list(range(pop_size))
    context = {'work': work}

    print(f"Benchmark: pop_size={pop_size}, work={work}")
    results = {}
    samples = {}
    for workers in workers_list:
        t0 = time.perf_counter()
        # pass a top-level function so it can be pickled by multiprocessing
        out = evaluate_population(pop, expensive_fitness, context, workers=workers)
        t1 = time.perf_counter()
        dt = t1 - t0
        results[workers] = dt
        samples[workers] = out
        print(f" workers={workers:2d} -> time={dt:.3f}s (sample output[0]={out[0]:.3f})")

    # Simple speedup printout
    base = results.get(list(workers_list)[0])
    for workers, t in results.items():
        print(f" workers={workers:2d} speedup={base / t:.2f}")

    return results, samples


def run(pop_size=20, work=20000, workers_list=(1, 2, 4), reps: int = 1, out_csv: str = None):
    all_rows = []
    for rep in range(1, reps + 1):
        print(f"\n=== REP {rep}/{reps} ===")
        results, samples = run_once(pop_size, work, workers_list)
        for w, t in results.items():
            all_rows.append({'rep': rep, 'pop_size': pop_size, 'work': work, 'workers': w, 'time': t})

    if out_csv:
        with open(out_csv, 'w', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=['rep', 'pop_size', 'work', 'workers', 'time'])
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"Wrote results to {out_csv}")

    return all_rows


def parse_workers(s: str):
    parts = [p.strip() for p in s.split(',') if p.strip()]
    return [int(p) for p in parts]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark serial vs parallel evaluation')
    parser.add_argument('--population', type=int, default=20, help='population size')
    parser.add_argument('--work', type=int, default=15000, help='work parameter for synthetic fitness')
    parser.add_argument('--workers', type=str, default='1,2,4', help='comma-separated worker counts')
    parser.add_argument('--reps', type=int, default=1, help='repetitions per configuration')
    parser.add_argument('--out', type=str, default=None, help='CSV file to write results to')
    args = parser.parse_args()

    workers_list = parse_workers(args.workers)
    run(pop_size=args.population, work=args.work, workers_list=workers_list, reps=args.reps, out_csv=args.out)
