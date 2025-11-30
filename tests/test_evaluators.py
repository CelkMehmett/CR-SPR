from src.editor.evaluators import evaluate_population


def simple_fitness(ind, context):
    # Individual may be an object with .fitness_pre or a raw numeric
    try:
        return float(getattr(ind, 'fitness_pre', ind))
    except Exception:
        return None


def test_evaluate_population_sync():
    pop = [0, 1, 2, 3, 4]
    res = evaluate_population(pop, simple_fitness, context=None, workers=1)
    assert res == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_evaluate_population_parallel():
    pop = [0, 1, 2, 3, 4]
    # Use 2 workers for parallel
    res = evaluate_population(pop, simple_fitness, context=None, workers=2)
    assert res == [0.0, 1.0, 2.0, 3.0, 4.0]
