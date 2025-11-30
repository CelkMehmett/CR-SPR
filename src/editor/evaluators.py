"""Evaluation helpers for parallel and distributed fitness evaluation.

This module provides a lightweight local parallel evaluator using
multiprocessing.Pool and a small adapter interface so the editor can
call an evaluator uniformly. A Ray adapter is implemented in a separate
module and imported only if available.

API:
- evaluate_population(population, fitness_fn, context, workers=4)
    -> returns list of fitness values in same order as population
"""
from typing import List, Callable, Any
import multiprocessing
import os
import logging

logger = logging.getLogger(__name__)


def _worker_eval(args):
    ind, fitness_fn, context = args
    try:
        return fitness_fn(ind, context)
    except Exception:
        logger.exception('Worker evaluation failed')
        return None


def evaluate_population(population: List[Any], fitness_fn: Callable[[Any, dict], float], context: dict = None, workers: int = None) -> List[float]:
    """Evaluate population in parallel using multiprocessing.Pool.

    Args:
        population: list of individuals (opaque to this module)
        fitness_fn: callable(individual, context) -> numeric fitness
        context: additional context passed to fitness_fn
        workers: number of worker processes. If None, uses cpu_count() // 2 or 1.

    Returns:
        list of fitness values (float or None for failed evaluations)
    """
    if context is None:
        context = {}

    if workers is None:
        workers = max(1, (os.cpu_count() or 1) // 2)

    # Short-circuit single-worker synchronous path for simplicity in tests
    if workers <= 1:
        out = []
        for ind in population:
            try:
                out.append(fitness_fn(ind, context))
            except Exception:
                logger.exception('Synchronous evaluation failed')
                out.append(None)
        return out

    # Build args list
    args = [(ind, fitness_fn, context) for ind in population]

    try:
        with multiprocessing.Pool(processes=workers) as pool:
            results = pool.map(_worker_eval, args)
        return results
    except Exception:
        logger.exception('Parallel evaluation failed; falling back to synchronous')
        out = []
        for ind in population:
            try:
                out.append(fitness_fn(ind, context))
            except Exception:
                logger.exception('Fallback synchronous evaluation failed')
                out.append(None)
        return out
