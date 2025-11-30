"""Genomic Bridge to LLMs: simplistic bio-tokenization utilities.

This provides deterministic mappings from floating gene values to integer tokens
and back, suitable for toy experiments and LLM embedding tests.
"""
from typing import List


def float_to_token(value: float, scale: float = 100.0) -> int:
    # scale and quantize
    return int(round(value * scale))


def token_to_float(token: int, scale: float = 100.0) -> float:
    return float(token) / scale


def genome_to_tokens(genome: dict, order: List[str] = None, scale: float = 100.0) -> List[int]:
    if order is None:
        order = sorted(genome.keys())
    return [float_to_token(genome[k], scale=scale) for k in order]


def tokens_to_genome(tokens: List[int], order: List[str], scale: float = 100.0) -> dict:
    return {name: token_to_float(tok, scale=scale) for name, tok in zip(order, tokens)}
