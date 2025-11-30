"""Epigenetic memory: store embeddings and provide simple retrieval/influence.

This module keeps a small in-memory memory of embeddings extracted from successful
mutations and provides utilities to query similar embeddings and compute influence
scores for genes.
"""
from typing import List, Dict, Any, Optional
import math


class EpigeneticMemory:
    def __init__(self):
        self.embeddings: List[List[float]] = []
        self.meta: List[Dict[str, Any]] = []

    def add(self, emb: List[float], meta: Optional[Dict[str, Any]] = None):
        self.embeddings.append(emb)
        self.meta.append(meta or {})

    def mean_embedding(self) -> Optional[List[float]]:
        if not self.embeddings:
            return None
        d = len(self.embeddings[0])
        out = [0.0] * d
        for e in self.embeddings:
            for i in range(d):
                out[i] += e[i]
        n = len(self.embeddings)
        return [x / n for x in out]

    def similarity_scores(self, emb: List[float]) -> List[float]:
        # cosine similarity to each stored embedding
        def norm(v):
            return math.sqrt(sum(x*x for x in v))
        nv = norm(emb)
        out = []
        for e in self.embeddings:
            ne = norm(e)
            if nv == 0 or ne == 0:
                out.append(0.0)
            else:
                dot = sum(x*y for x, y in zip(emb, e))
                out.append(dot / (nv * ne))
        return out

    def influence_for_genes(self, arms: List[str]) -> Dict[str, float]:
        # simple heuristic: use mean embedding magnitude to bias earlier arms
        mean = self.mean_embedding()
        if mean is None:
            return dict.fromkeys(arms, 0.0)
        mag = sum(abs(x) for x in mean)
        out = {}
        for i, a in enumerate(arms):
            out[a] = mag / (1 + i)
        return out
