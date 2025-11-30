import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.bio_token import float_to_token, token_to_float, genome_to_tokens, tokens_to_genome


def test_token_roundtrip():
    v = 0.1234
    t = float_to_token(v, scale=1000.0)
    assert isinstance(t, int)
    v2 = token_to_float(t, scale=1000.0)
    assert abs(v - v2) < 0.001


def test_genome_tokens():
    g = {'a': 0.1, 'b': -0.2, 'c': 1.23}
    order = ['a','b','c']
    toks = genome_to_tokens(g, order=order, scale=100.0)
    g2 = tokens_to_genome(toks, order, scale=100.0)
    assert all(abs(g[k] - g2[k]) < 0.02 for k in order)
