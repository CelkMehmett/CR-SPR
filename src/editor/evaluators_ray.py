"""Ray adapter for evaluation.

Provides a slightly more robust adapter that supports batching and optional
actor reuse. The module intentionally keeps the Ray dependency optional; when
Ray is not present the call will raise ImportError so callers can fallback to
other evaluators.
"""
from typing import List, Callable, Any, Optional


def evaluate_population_ray(population: List[Any],
                            fitness_fn: Callable[[Any, dict], float],
                            context: dict = None,
                            ray_address: Optional[str] = None,
                            batch_size: int = 64,
                            reuse_actors: bool = False,
                            timeout: Optional[float] = None):
    """Evaluate a population using Ray remote tasks.

    Args:
        population: list of individuals (opaque to Ray)
        fitness_fn: callable(individual, context) -> float
        context: optional context dict passed to each evaluation
        ray_address: Ray address string or None (auto)
        batch_size: number of remote tasks to submit per batch
        reuse_actors: when True, use simple actor workers to avoid repeated
                      function serialization overhead (best-effort)
        timeout: optional timeout in seconds for ray.get

    Returns:
        list of fitness floats in the same order as population

    Raises:
        ImportError: when Ray is not installed
    """
    try:
        import ray
    except Exception:
        raise ImportError('ray is not installed')

    if context is None:
        context = {}

    # Initialize Ray if not already initialized. Use ignore_reinit_error to be safe.
    try:
        ray.init(address=ray_address or 'auto', ignore_reinit_error=True)
        _started_ray_here = True
    except Exception:
        # If connecting to an external cluster fails, attempt to init a local runtime
        try:
            ray.init(ignore_reinit_error=True)
            _started_ray_here = True
        except Exception:
            _started_ray_here = False

    # If reuse_actors is requested, create simple worker actors that call the fitness
    if reuse_actors:
        @ray.remote
        class _Worker:
            def __init__(self):
                pass

            def eval(self, ind, ctx):
                return fitness_fn(ind, ctx)

        # Create a small pool of actors (bounded by batch_size)
        num_workers = max(1, min(len(population), max(1, batch_size)))
        actors = [_Worker.remote() for _ in range(num_workers)]

        # Round-robin schedule
        futures = []
        for i, ind in enumerate(population):
            actor = actors[i % len(actors)]
            futures.append(actor.eval.remote(ind, context))

        # Wait and gather
        try:
            results = ray.get(futures, timeout=timeout)
        finally:
            # Best-effort: don't shutdown the cluster (caller may want to reuse)
            pass

        return results

    # Otherwise, submit tasks in batches using a plain remote function
    @ray.remote
    def _eval_remote(ind, ctx):
        return fitness_fn(ind, ctx)

    results: List[float] = []
    i = 0
    try:
        while i < len(population):
            batch = population[i:i + batch_size]
            futures = [_eval_remote.remote(ind, context) for ind in batch]
            batch_results = ray.get(futures, timeout=timeout)
            results.extend(batch_results)
            i += batch_size
    finally:
        # Do not forcibly shutdown Ray here; the caller may rely on an existing
        # cluster/driver. If we started Ray in this call and the user didn't
        # explicitly request reuse, attempt to shut it down to free resources.
        try:
            if _started_ray_here:
                try:
                    ray.shutdown()
                except Exception:
                    pass
        except NameError:
            pass

    return results

