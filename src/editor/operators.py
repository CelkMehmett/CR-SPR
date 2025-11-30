"""Reusable GA operator implementations.

Provides selection, crossover and mutation operators that can be injected
into `GeneticAlgorithmEditor` via the pluggable operator attributes.
"""
from typing import List, Tuple
import random
import numpy as np
from .ga_editor import Individual


def tournament_selection(population: List[Individual], tournament_size: int = 3) -> Individual:
    """Select an individual using tournament selection."""
    if not population:
        raise ValueError("Population is empty")
    contenders = random.sample(population, min(tournament_size, len(population)))
    return max(contenders, key=lambda ind: ind.fitness)


def rank_selection(population: List[Individual]) -> Individual:
    """Rank selection: probability proportional to rank (low to high)."""
    if not population:
        raise ValueError("Population is empty")
    sorted_pop = sorted(population, key=lambda ind: ind.fitness)
    ranks = list(range(1, len(sorted_pop) + 1))
    total = sum(ranks)
    pick = random.uniform(0, total)
    acc = 0
    for ind, r in zip(sorted_pop, ranks):
        acc += r
        if pick <= acc:
            return ind
    return sorted_pop[-1]


def uniform_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
    """Uniform crossover: gene-by-gene random choice."""
    g1 = {}
    g2 = {}
    keys = set(parent1.genome.keys()) | set(parent2.genome.keys())
    for k in keys:
        if random.random() < 0.5:
            g1[k] = parent1.genome.get(k, parent2.genome.get(k))
            g2[k] = parent2.genome.get(k, parent1.genome.get(k))
        else:
            g1[k] = parent2.genome.get(k, parent1.genome.get(k))
            g2[k] = parent1.genome.get(k, parent2.genome.get(k))
    child1 = Individual(genome=g1)
    child2 = Individual(genome=g2)
    return child1, child2


def simulated_binary_crossover(parent1: Individual, parent2: Individual, eta: float = 15.0) -> Tuple[Individual, Individual]:
    """SBX for numeric genes; non-numeric genes are copied."""
    g1 = {}
    g2 = {}
    for k in set(parent1.genome.keys()) | set(parent2.genome.keys()):
        a = parent1.genome.get(k)
        b = parent2.genome.get(k)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > 1e-12:
            u = random.random()
            if u <= 0.5:
                beta = (2 * u) ** (1.0 / (eta + 1.0))
            else:
                beta = (1.0 / (2.0 * (1.0 - u))) ** (1.0 / (eta + 1.0))
            g1[k] = 0.5 * ((1 + beta) * a + (1 - beta) * b)
            g2[k] = 0.5 * ((1 - beta) * a + (1 + beta) * b)
        else:
            # Fallback: copy
            g1[k] = a if a is not None else b
            g2[k] = b if b is not None else a
    return Individual(genome=g1), Individual(genome=g2)


def gaussian_mutation(individual: Individual, edit_rate: float = 0.05) -> Individual:
    """Gaussian mutation applied to numeric genes."""
    ind = Individual(genome=dict(individual.genome), parent_ids=list(getattr(individual, 'parent_ids', [])))
    for k, v in list(ind.genome.items()):
        if isinstance(v, (int, float)):
            sigma = max(abs(v) * edit_rate, 1e-6)
            ind.genome[k] = v + np.random.normal(0, sigma)
        elif isinstance(v, np.ndarray):
            sigma = np.std(v) * edit_rate if np.std(v) > 0 else 1e-6
            ind.genome[k] = v + np.random.normal(0, sigma, size=v.shape)
    ind.mutation_history = list(getattr(individual, 'mutation_history', []))
    ind.mutation_history.append('gaussian')
    return ind
