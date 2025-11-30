CI Benchmark
============

This folder contains a lightweight CI-friendly benchmark script designed to
measure very small workloads (suitable for running on CI runners).

Usage (locally):

```bash
python benchmarks/ci_benchmark.py
```

Environment variables:
- `CI_BENCH_POP` - population size (default 20)
- `CI_BENCH_TRIALS` - number of trials (default 3)
- `CI_BENCH_WORKERS` - number of worker processes when using multiprocessing (default 2)

Output:
- `benchmarks/ci_benchmark_results.csv` (CSV with timing per trial)

Note: This is intentionally small to keep CI costs low. For full benchmarking,
use `benchmarks/run_benchmark.py` or the other benchmark harnesses in the repo.
Benchmark harness

Run the small benchmark to compare serial and parallel evaluation performance:

python3 benchmarks/run_benchmark.py

Notes:
- The benchmark uses a synthetic CPU-bound fitness function. Adjust `pop_size` and `work` in the script for longer/shorter runs.
- The `evaluate_population` function uses `multiprocessing.Pool` for parallel evaluation; set `workers` to tune concurrency.
