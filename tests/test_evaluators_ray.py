import pytest

from src.editor import evaluators_ray


def test_evaluate_population_ray_import_behavior():
    """If Ray is not installed, evaluate_population_ray should raise ImportError.

    If Ray is installed in the environment, this test will perform a simple
    remote evaluation to verify the function runs end-to-end.
    """
    try:
        import ray  # type: ignore

        ray_available = True
    except Exception:
        ray_available = False

    if not ray_available:
        with pytest.raises(ImportError):
            evaluators_ray.evaluate_population_ray([], lambda a, b: 0.0)
    else:
        # simple sanity check when ray is present
        pop = [1, 2, 3]

        def fitness(x, ctx):
            return float(x * 2)

        results = evaluators_ray.evaluate_population_ray(pop, fitness, context=None, ray_address=None)
        assert isinstance(results, list)
        assert results == [2.0, 4.0, 6.0]
