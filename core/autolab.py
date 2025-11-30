"""Autonomous Lab Mode: orchestrator for self-run experiments.

Runs CasAICore experiments autonomously, logs entries using narrator, and
reacts to drift detector callbacks by launching additional exploration cycles.
"""
from typing import Any, Dict, List
import threading
import time

from core.cas_ai import CasAICore
from core.narrator import explain_with_llm, LLMHook
from core.drift_detector import DriftDetector
from core.merkle_ledger import MerkleLedger


class AutoLab:
    def __init__(self, cas: CasAICore, drift_detector: DriftDetector = None, llm: LLMHook = None, ledger: MerkleLedger = None):
        self.cas = cas
        self.drift = drift_detector or DriftDetector()
        self.llm = llm
        self.running = False
        self.thread: threading.Thread = None
        self.log: List[Dict[str, Any]] = []
        self.ledger = ledger or MerkleLedger()

        # register drift callback to trigger extra experiments
        self.drift.register_callback(self._on_drift)

    def _on_drift(self, baseline: float, current: float):
        # on drift, run a short exploratory experiment
        entry = {'reason': 'drift_trigger', 'baseline': baseline, 'current': current, 'ts': time.time()}
        self.log.append(entry)
        try:
            self.ledger.append(entry)
        except Exception:
            pass
        # run quick exploration
        self.cas.run_experiment(iterations=3, scale=0.3)

    def step(self):
        # run one cycle and log narrated summary
        res = self.cas.run_one_cycle()
        if res.get('committed'):
            entry = res['entry']
            text = explain_with_llm(entry, self.llm)
            rec = {'entry': entry, 'summary': text}
            self.log.append(rec)
            try:
                self.ledger.append(rec)
            except Exception:
                pass
            # feed reward into drift detector
            self.drift.add(entry.get('reward', 0.0))
        else:
            rec = res.get('recorded')
            self.log.append({'rejected': rec})
        return res

    def ledger_root(self):
        return self.ledger.root()

    def run(self, interval: float = 0.2):
        self.running = True

        def loop():
            while self.running:
                try:
                    self.step()
                except Exception:
                    pass
                time.sleep(interval)

        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
