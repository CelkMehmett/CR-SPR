import os
import tempfile
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.rl_backtest_pipeline import RLBacktestPipeline


def test_save_and_load_checkpoint_roundtrip():
    symbols = ['S1']
    models = ['m1', 'm2']
    pipeline = RLBacktestPipeline(symbols, models, controller_type='epsilon', epsilon=0.2)

    # simulate some updates
    a = pipeline.arms[0]
    pipeline.controller.update(a, 0.5)
    pipeline.controller.update(a, 0.2)

    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    path = tmp.name
    try:
        pipeline.save_checkpoint(path)
        # create a fresh pipeline with a different controller type
        p2 = RLBacktestPipeline(symbols, models, controller_type='ucb', c=1.5)
        p2.load_checkpoint(path)
        # after load, controller should be epsilon (saved type)
        assert type(p2.controller).__name__ == type(pipeline.controller).__name__
        # counts and values should be restored at least for known arms
        for arm in pipeline.arms:
            assert arm in p2.controller.counts
            assert p2.controller.counts[arm] == pipeline.controller.counts[arm]
            assert abs(p2.controller.values[arm] - pipeline.controller.values[arm]) < 1e-6
    finally:
        os.unlink(path)
