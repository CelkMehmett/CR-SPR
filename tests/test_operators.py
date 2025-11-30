import numpy as np
from src.editor.operators import (
    tournament_selection,
    rank_selection,
    uniform_crossover,
    simulated_binary_crossover,
    gaussian_mutation,
)
from src.editor.ga_editor import Individual


def make_pop():
    return [Individual(genome={'x': float(i)}, fitness=float(i)) for i in range(5)]


def test_tournament_selection():
    pop = make_pop()
    chosen = tournament_selection(pop, tournament_size=2)
    assert chosen in pop


def test_rank_selection():
    pop = make_pop()
    chosen = rank_selection(pop)
    assert chosen in pop


def test_uniform_crossover():
    p1 = Individual(genome={'a': 1, 'b': 2})
    p2 = Individual(genome={'a': 10, 'b': 20})
    c1, c2 = uniform_crossover(p1, p2)
    assert isinstance(c1, Individual)
    assert isinstance(c2, Individual)
    assert set(c1.genome.keys()) == set(p1.genome.keys())


def test_sbx_and_gaussian():
    p1 = Individual(genome={'a': 1.0, 'b': np.array([1.0, 2.0])})
    p2 = Individual(genome={'a': 2.0, 'b': np.array([2.0, 3.0])})
    c1, c2 = simulated_binary_crossover(p1, p2)
    assert isinstance(c1, Individual)
    assert isinstance(c2, Individual)

    mutated = gaussian_mutation(p1, edit_rate=0.1)
    assert isinstance(mutated, Individual)
    assert 'gaussian' in mutated.mutation_history
