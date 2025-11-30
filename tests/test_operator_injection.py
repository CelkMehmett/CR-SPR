import pytest
from src.editor.ga_editor import GeneticAlgorithmEditor, Individual


def test_operator_injection_side_effect(tmp_path):
    # Create editor with deterministic seed
    editor = GeneticAlgorithmEditor(seed=123)
    editor.config.population_size = 2
    editor.config.num_generations = 1
    editor.config.crossover_rate = 0.0
    editor.config.mutation_rate = 0.0

    # Prepare a tiny population with known fitnesses
    editor._population = [
        Individual(genome={'x': 0}, fitness=0.0),
        Individual(genome={'x': 1}, fitness=1.0)
    ]
    editor._best_individual = editor._population[1]

    # Side-effect counter
    called = {'selection': 0, 'crossover': 0, 'mutation': 0}

    def custom_selection():
        called['selection'] += 1
        # Always pick the first individual
        return editor._population[0]

    def custom_crossover(p1, p2):
        called['crossover'] += 1
        return p1, p2

    def custom_mutation(ind, ctx):
        called['mutation'] += 1
        return ind

    # Inject operators
    editor.selection_operator = custom_selection
    editor.crossover_operator = custom_crossover
    editor.mutation_operator = custom_mutation

    # Run evolution (will call injected operators)
    best = editor._evolve_population({'dummy': True})

    # Verify side-effects occurred
    assert called['selection'] > 0, "Selection operator was not called"
    # Crossover and mutation may not be called depending on rates; ensure no exceptions
    assert best is not None

    # Ensure editor state remains consistent
    assert isinstance(editor._population, list)
    assert len(editor._population) == editor.config.population_size


if __name__ == '__main__':
    pytest.main([__file__])
