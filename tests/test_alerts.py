import sys
import os
# ensure project root is on sys.path for pytest
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.alerts import Alert, AlertManager


def test_alert_safe_eval_and_unsafe():
    am = AlertManager()
    # safe conditions
    am.register(Alert('a', 'metrics.get("sharpe",0) < 1.0', channels=['log']))
    am.register(Alert('b', 'metrics["sharpe"] < 1.0', channels=['log']))
    # unsafe condition should not be allowed to execute
    am.register(Alert('u', '__import__("os").system("echo hi")', channels=['log']))

    # when sharpe present both a and b should trigger
    hits = am.evaluate({'sharpe': 0.8})
    assert 'a' in hits
    assert 'b' in hits
    assert 'u' not in hits

    # when sharpe missing, a uses metrics.get default -> should trigger; b should not
    hits2 = am.evaluate({})
    assert 'a' in hits2
    assert 'b' not in hits2
    assert 'u' not in hits2
