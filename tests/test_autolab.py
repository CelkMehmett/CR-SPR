import os
import sys
import time

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.cas_ai import Gene, Genome, CasAICore
from core.autolab import AutoLab
from core.narrator import LLMHook


def _simple_evaluator(genome):
    target = {'g1': 1.0, 'g2': -0.5}
    s = 0.0
    for k, v in genome.to_dict().items():
        t = target.get(k, 0.0)
        s -= (v - t) ** 2
    return float(s)


def test_autolab_runs_steps():
    genes = {
        'g1': Gene('g1', 0.0, min_val=-5.0, max_val=5.0),
        'g2': Gene('g2', 0.0, min_val=-5.0, max_val=5.0)
    }
    genome = Genome(genes)
    cas = CasAICore(genome, evaluator=_simple_evaluator, epsilon=0.3)
    lab = AutoLab(cas, llm=LLMHook(callable_obj=lambda p: 'OK'))
    # run a few manual steps
    for _ in range(4):
        r = lab.step()
        assert isinstance(r, dict)
    # start background run for a short while
    lab.run(interval=0.05)
    time.sleep(0.2)
    lab.stop()
    assert len(lab.log) > 0
