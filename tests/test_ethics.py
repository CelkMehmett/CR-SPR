import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.ethics import EthicsChecker


def test_ethics_default_rule():
    ec = EthicsChecker()
    # edit with small delta should pass
    ok, reason = ec.approve({'old': 0.0, 'new': 0.5}, {}, None)
    assert ok
    # large delta should be rejected
    ok2, reason2 = ec.approve({'old': 0.0, 'new': 5.0}, {}, None)
    assert not ok2
