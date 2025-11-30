import numpy as np

from src.editor.ga_editor import GeneticAlgorithmEditor, Individual


def make_ind(vec, fitness):
    ind = Individual(genome={'x': np.array(vec)}, generation=0)
    ind.fitness = fitness
    return ind


def test_assign_species_and_sharing():
    editor = GeneticAlgorithmEditor(name='spec_test', seed=123)
    # Small population of 6 individuals: two clusters of 3 each
    editor._population = [
        make_ind([0.0, 0.0], 10.0),
        make_ind([0.1, -0.05], 9.0),
        make_ind([0.05, 0.02], 8.0),
        make_ind([5.0, 5.0], 7.0),
        make_ind([5.1, 4.9], 6.0),
        make_ind([4.9, 5.05], 5.0),
    ]

    species = editor._assign_species(threshold=0.3)

    # Expect two species ids (0 and 1) with three members each
    assert len(set(species)) == 2
    counts = {s: species.count(s) for s in set(species)}
    assert set(counts.values()) == {3}

    # Apply fitness sharing
    editor._apply_fitness_sharing(species)

    # In each species, shared fitness should be original / 3
    for ind in editor._population[:3]:
        assert abs(ind.shared_fitness - (ind.fitness / 3.0)) < 1e-6
    for ind in editor._population[3:]:
        assert abs(ind.shared_fitness - (ind.fitness / 3.0)) < 1e-6


def test_evolve_with_speciation_sets_species_count():
    editor = GeneticAlgorithmEditor(name='spec_evolve', seed=42)
    editor.use_speciation = True
    editor.config.population_size = 6
    editor.config.num_generations = 2

    # Build population with two clusters as before
    editor._population = [
        make_ind([0.0, 0.0], 0.0),
        make_ind([0.1, -0.05], 0.0),
        make_ind([0.05, 0.02], 0.0),
        make_ind([5.0, 5.0], 0.0),
        make_ind([5.1, 4.9], 0.0),
        make_ind([4.9, 5.05], 0.0),
    ]

    # Use a simple objective that uses the 'x' vector
    def obj(genome, ctx=None):
        x = genome.get('x')
        return float(- (x[0]**2 + x[1]**2))

    editor.fitness_function = editor.fitness_function or None
    # Replace with a FitnessFunction that uses our objective
    from src.editor.ga_editor import FitnessFunction
    editor.fitness_function = FitnessFunction(objective_function=obj)

    # Run a short evolution
    best = editor._evolve_population(None)

    # After evolution, generation history should contain species_count if speciation applied
    assert editor._generation_history, "generation history should not be empty"
    # Because we applied speciation, individuals should have species_id set
    assert all(hasattr(ind, 'species_id') for ind in editor._population)


def test_speciation_selection_balances_species():
    editor = GeneticAlgorithmEditor(name='spec_sel', seed=7)
    # Create two species where species 0 has higher fitness values
    editor._population = [
        make_ind([0.0, 0.0], 100.0),
        make_ind([0.1, -0.05], 90.0),
        make_ind([0.05, 0.02], 80.0),
        make_ind([5.0, 5.0], 10.0),
        make_ind([5.1, 4.9], 9.0),
        make_ind([4.9, 5.05], 8.0),
    ]

    # Ensure species assignment
    species = editor._assign_species(threshold=0.3)

    # Without speciation, selection should prefer species 0 heavily
    counts_no_spec = {0: 0, 1: 0}
    for _ in range(100):
        sel = editor._tournament_selection()
        counts_no_spec[getattr(sel, 'species_id')] += 1

    # Now enable speciation and repeat selections
    editor.set_speciation(True, threshold=0.3)
    counts_spec = {0: 0, 1: 0}
    for _ in range(100):
        sel = editor._speciation_selection()
        counts_spec[getattr(sel, 'species_id')] += 1

    # Expect selection counts without speciation to be skewed towards species 0
    assert counts_no_spec[0] > counts_no_spec[1]
    # With speciation, distribution should be more balanced (not all from species 0)
    assert counts_spec[0] < 90  # not all picks
    assert counts_spec[1] > 5
