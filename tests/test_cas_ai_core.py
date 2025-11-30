import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.cas_ai import Gene, Genome, CasAICore


def _simple_evaluator(genome):
    # toy evaluator: reward is negative L2 distance to a target vector
    target = {'g1': 1.0, 'g2': -0.5, 'g3': 0.2}
    s = 0.0
    for k, v in genome.to_dict().items():
        t = target.get(k, 0.0)
        s -= (v - t) ** 2
    # map to positive-ish reward
    return float(s)


def test_cas_ai_basic_cycle():
    genes = {
        'g1': Gene('g1', 0.0, min_val=-5.0, max_val=5.0),
        'g2': Gene('g2', 0.0, min_val=-5.0, max_val=5.0),
        'g3': Gene('g3', 0.0, min_val=-5.0, max_val=5.0)
    }
    genome = Genome(genes)
    cas = CasAICore(genome, evaluator=_simple_evaluator, epsilon=0.3)

    baseline = _simple_evaluator(genome)
    # run a few iterations
    res = cas.run_experiment(iterations=8, scale=0.5)
    assert isinstance(res, list)
    # ensure ledger or gene bank recorded events
    assert cas.ledger.root() is not None or len(cas.gene_bank.failed) > 0
    # epigenetic memory should have an internal list for embeddings
    assert isinstance(cas.epigenetic_memory_list, list)
    # ensure genome values remain within bounds
    for g in cas.genome.genes.values():
        assert -5.0 <= g.value <= 5.0
