import numpy as np

from src.editor.ga_editor import GeneticAlgorithmEditor, Individual


def make_ind(vec, fitness, age=0):
    ind = Individual(genome={'x': np.array(vec)}, generation=0)
    ind.fitness = fitness
    ind.age = age
    return ind


def test_age_pruning_and_hof_integration():
    editor = GeneticAlgorithmEditor(name='age_test', seed=1)
    editor.config.population_size = 6
    editor.config.max_individual_age = 2

    # Create population where some individuals are old
    editor._population = [
        make_ind([0, 0], 10.0, age=3),  # should be pruned
        make_ind([0.1, 0.0], 9.0, age=1),
        make_ind([0.2, -0.1], 8.0, age=2),
        make_ind([5.0, 5.0], 7.0, age=4),  # pruned
        make_ind([5.1, 4.9], 6.0, age=0),
        make_ind([4.9, 5.05], 5.0, age=2),
    ]

    # Prepare best individual
    editor._best_individual = max(editor._population, key=lambda x: x.fitness)

    # Run a single evolution iteration by invoking _evolve_population with num_generations=1
    editor.config.num_generations = 1
    editor._evolve_population(None)

    # After pruning, no individual should have age > max_individual_age
    assert all(getattr(ind, 'age', 0) <= editor.config.max_individual_age for ind in editor._population)

    # Hall of fame should contain pruned high-fitness individuals (at least one)
    assert isinstance(editor.hall_of_fame, list)
    assert len(editor.hall_of_fame) >= 1
