"""Minimal metrics helpers with Prometheus client optional dependency.

Exports:
- Counter(name, documentation, labelnames=()) -> object with .inc(amount=1)

If `prometheus_client` is available, it uses real counters; otherwise returns a no-op implementation.
"""
from collections.abc import Iterable


class _NoopCounter:
    def __init__(self, *args, **kwargs):
        pass

    def labels(self, *args, **kwargs):
        return self

    def inc(self, amount=1):
        return None


try:
    from prometheus_client import Counter as _PromCounter

    def Counter(name: str, documentation: str, labelnames: Iterable[str] = ()):  # type: ignore
        if labelnames:
            return _PromCounter(name, documentation, list(labelnames))
        return _PromCounter(name, documentation)

except Exception:
    Counter = lambda *a, **k: _NoopCounter()
