"""Genetic Algorithm based parameter editor.

Biological note: analogous to CRISPR cutting and inserting new parameter sequences.
"""
from __future__ import annotations
from typing import Callable, Tuple
import numpy as np


try:
    import pygad

    class SimpleGAEditor:
        """Simple GA editor that optimizes a small hyperparameter vector using pygad when available."""

        def __init__(self, num_genes: int, gene_space=None, pop_size: int = 10, generations: int = 5):
            self.num_genes = num_genes
            self.gene_space = gene_space
            self.pop_size = pop_size
            self.generations = generations

        def edit(self, evaluator: Callable[[np.ndarray], float]) -> Tuple[np.ndarray, float]:
            # pygad expects a fitness function with signature (ga_instance, solution, sol_idx)
            def fitness_func(ga, solution, sol_idx):
                return float(evaluator(np.array(solution)))

            ga = pygad.GA(num_generations=self.generations,
                          num_parents_mating=max(1, int(self.pop_size / 2)),
                          fitness_func=fitness_func,
                          sol_per_pop=self.pop_size,
                          num_genes=self.num_genes,
                          gene_space=self.gene_space,
                          mutation_percent_genes=20)
            ga.run()
            best_sol, best_idx, best_fit = ga.best_solution()
            return np.array(best_sol), float(best_fit)

except Exception:
    # Fallback lightweight evolutionary search if pygad isn't installed.
    class SimpleGAEditor:
        """Fallback simple evolutionary search: random restarts + mutation.

        This is intentionally small and deterministic (seeded) for tests.
        """

        def __init__(self, num_genes: int, gene_space=None, pop_size: int = 10, generations: int = 5):
            self.num_genes = num_genes
            # gene_space can be list of dicts with 'low' and 'high' or None
            self.gene_space = gene_space
            self.pop_size = pop_size
            self.generations = generations
            self.rng = np.random.RandomState(42)

        def _sample(self):
            vals = []
            if self.gene_space is None:
                return self.rng.uniform(-1, 1, size=self.num_genes)
            for g in self.gene_space:
                if isinstance(g, dict) and 'low' in g and 'high' in g:
                    vals.append(self.rng.uniform(g['low'], g['high']))
                else:
                    vals.append(self.rng.uniform(-1, 1))
            return np.array(vals)

        def edit(self, evaluator: Callable[[np.ndarray], float]) -> Tuple[np.ndarray, float]:
            # init population
            pop = [self._sample() for _ in range(self.pop_size)]
            fitness = [evaluator(p) for p in pop]
            best_idx = int(np.argmax(fitness))
            best = pop[best_idx]
            best_fit = fitness[best_idx]

            for gen in range(self.generations):
                # create children by mutating best
                children = []
                for _ in range(self.pop_size):
                    child = best.copy()
                    # gaussian mutation
                    child = child + self.rng.normal(scale=0.1, size=self.num_genes)
                    # clip to gene space if provided
                    if self.gene_space is not None:
                        for i, g in enumerate(self.gene_space):
                            if isinstance(g, dict) and 'low' in g and 'high' in g:
                                child[i] = np.clip(child[i], g['low'], g['high'])
                    children.append(child)
                # evaluate children
                fitness_c = [evaluator(c) for c in children]
                idx = int(np.argmax(fitness_c))
                if fitness_c[idx] > best_fit:
                    best_fit = fitness_c[idx]
                    best = children[idx]

            return np.array(best), float(best_fit)
