import numpy as np
from src.editor.ga_editor import GeneticAlgorithmEditor, Individual


def make_population_identical(n, value=1.0):
    pop = []
    for i in range(n):
        ind = Individual(genome={'g': float(value)}, fitness=0.0)
        pop.append(ind)
    return pop


def make_population_varied(n):
    pop = []
    for i in range(n):
        v = float(i)
        ind = Individual(genome={'g': np.array([v, v + 1.0])}, fitness=float(v))
        pop.append(ind)
    return pop


def test_compute_population_diversity_identical():
    editor = GeneticAlgorithmEditor(seed=123)
    pop = make_population_identical(5, value=2.0)
    d = editor._compute_population_diversity(pop)
    assert isinstance(d, float)
    assert d == 0.0


def test_compute_population_diversity_varied():
    editor = GeneticAlgorithmEditor(seed=123)
    pop = make_population_varied(5)
    d = editor._compute_population_diversity(pop)
    assert isinstance(d, float)
    assert d > 0.0


def test_adapt_mutation_rate_on_low_diversity():
    editor = GeneticAlgorithmEditor(seed=42)
    # ensure baseline
    editor.config.mutation_rate = 0.05
    editor._base_mutation_rate = 0.05

    # Simulate recent good improvements so strategy switch isn't triggered
    editor._generation_history = [{'improvement': 1e-3}] * 5

    # Low diversity scenario
    stats = {'generation': 0, 'improvement': 0.0, 'diversity': 0.0}
    prev = editor.config.mutation_rate
    editor._adapt_strategies(stats)
    assert editor.config.mutation_rate >= prev
    assert editor.config.mutation_rate > 0.05


def test_decay_mutation_rate_towards_baseline_on_high_diversity():
    editor = GeneticAlgorithmEditor(seed=42)
    editor.config.mutation_rate = 0.3
    editor._base_mutation_rate = 0.05
    editor._generation_history = [{'improvement': 1e-3}] * 5

    stats = {'generation': 0, 'improvement': 0.0, 'diversity': 1.0}
    prev = editor.config.mutation_rate
    editor._adapt_strategies(stats)
    assert editor.config.mutation_rate < prev
    assert editor.config.mutation_rate >= editor._base_mutation_rate
