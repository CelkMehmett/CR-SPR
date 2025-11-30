import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.guidrna import suggest_genes


def test_guidrna_suggests_top_k():
    arms = ['g1', 'g2', 'g3', 'g4']
    counts = {'g1': 10, 'g2': 1, 'g3': 5, 'g4': 0}
    values = {'g1': 0.1, 'g2': 0.5, 'g3': 0.0, 'g4': -0.2}
    epigenetic_memory = [[0.1]*8, [0.2]*8]
    s = suggest_genes(arms, counts, values, epigenetic_memory, top_k=2)
    assert isinstance(s, list)
    assert len(s) == 2
    # ensure suggestions are among arms
    assert all(x in arms for x in s)
