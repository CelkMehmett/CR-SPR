from src.editor.ga_editor import GeneticAlgorithmEditor, Individual


def test_ga_parallel_evaluation_flag():
    editor = GeneticAlgorithmEditor(seed=1)
    editor.config.population_size = 4
    editor.config.num_generations = 1

    # Create a tiny initial population
    editor._population = [Individual(genome={'x': float(i)}, fitness=0.0) for i in range(editor.config.population_size)]

    # Use a simple fitness function that reads genome['x']
    class SimpleFitness:
        def evaluate(self, individual, context=None):
            return float(individual.genome.get('x', 0.0))

    editor.fitness_function = SimpleFitness()

    # Enable parallel evaluation but use workers=1 to ensure deterministic synchronous path in tests
    editor.set_parallel_evaluation(True, workers=1)

    best = editor._evolve_population({'dummy': True})

    assert best is not None
    assert isinstance(editor._population, list)
    assert all(hasattr(ind, 'fitness') for ind in editor._population)
