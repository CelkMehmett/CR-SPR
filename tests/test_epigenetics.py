import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.epigenetics import EpigeneticMemory


def test_epigenetic_memory_basic():
    mem = EpigeneticMemory()
    assert mem.mean_embedding() is None
    mem.add([0.1, -0.2, 0.3], {'gene': 'g1'})
    mem.add([0.0, 0.0, 0.5], {'gene': 'g2'})
    mean = mem.mean_embedding()
    assert isinstance(mean, list)
    assert len(mean) == 3
    scores = mem.similarity_scores([0.1, -0.2, 0.3])
    assert isinstance(scores, list)
    inf = mem.influence_for_genes(['g1','g2','g3'])
    assert all(k in inf for k in ['g1','g2','g3'])
