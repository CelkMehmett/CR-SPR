"""GuideRNA Generator: lightweight meta-learner.

This module provides a small heuristic/meta-learner that consumes:
- bandit statistics (counts, values)
- epigenetic memory embeddings

and suggests a ranked list of genes to edit next. It's intentionally
lightweight (no heavy dependencies) and suitable for unit testing.
"""
from typing import List, Dict
import math


def score_from_bandit(arms: List[str], counts: Dict[str, int], values: Dict[str, float]) -> Dict[str, float]:
    scores = {}
    total = sum(counts.get(a, 0) for a in arms) + 1
    for a in arms:
        # prefer arms with high value and moderate exploration score
        v = values.get(a, 0.0)
        c = counts.get(a, 0)
        exploration = math.sqrt(math.log(total) / (1 + c))
        scores[a] = v + 0.5 * exploration
    return scores


def influence_from_epigenetics(arms: List[str], epigenetic_memory: List[List[float]]) -> Dict[str, float]:
    # simple influence: if many embeddings exist, compute mean absolute activation
    if not epigenetic_memory:
        return dict.fromkeys(arms, 0.0)
    # collapse embeddings to a single scalar per arm via hashing-like mapping
    # deterministic but simple: sum over embedding elements modded by arm index
    mean_emb = [sum(col) / len(epigenetic_memory) for col in zip(*epigenetic_memory)]
    out = {}
    for i, a in enumerate(arms):
        # map mean_emb to a score biased by arm index
        s = sum(abs(x) for x in mean_emb) * (1.0 / (1 + i))
        out[a] = s
    return out


def suggest_genes(arms: List[str], counts: Dict[str, int], values: Dict[str, float], epigenetic_memory: List[List[float]], top_k: int = 3) -> List[str]:
    bandit_scores = score_from_bandit(arms, counts, values)
    epi_scores = influence_from_epigenetics(arms, epigenetic_memory)
    combined = {}
    for a in arms:
        combined[a] = 0.7 * bandit_scores.get(a, 0.0) + 0.3 * epi_scores.get(a, 0.0)
    ranked = sorted(arms, key=lambda x: combined.get(x, 0.0), reverse=True)
    return ranked[:min(top_k, len(ranked))]
