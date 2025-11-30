"""CRISPR Ethics Layer: rule-based governance for mutations.

Provides a small, auditable policy engine that approves or rejects proposed
mutations before they're committed.
"""
from typing import Dict, Any, Tuple, List, Callable


class EthicsChecker:
    def __init__(self):
        # list of rule functions that accept (edit, validation, genome) and return (bool, reason)
        self.rules: List[Callable[[Dict[str, Any], Dict[str, Any], Any], Tuple[bool, str]]] = []
        # default rules
        self.add_rule(self._max_delta_rule(1.0))

    def add_rule(self, fn: Callable[[Dict[str, Any], Dict[str, Any], Any], Tuple[bool, str]]):
        self.rules.append(fn)

    def _max_delta_rule(self, max_delta: float):
        def rule(edit: Dict[str, Any], validation: Dict[str, Any], genome) -> Tuple[bool, str]:
            old = float(edit.get('old', 0.0))
            new = float(edit.get('new', 0.0))
            if abs(new - old) > max_delta:
                return False, f'delta too large ({abs(new-old):.3f} > {max_delta})'
            return True, 'ok'
        return rule

    def approve(self, edit: Dict[str, Any], validation: Dict[str, Any], genome) -> Tuple[bool, str]:
        for r in self.rules:
            ok, reason = r(edit, validation, genome)
            if not ok:
                return False, reason
        return True, 'approved'
