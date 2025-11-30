"""
Background RL pipeline service.

Provides start/stop/status for a single worker that runs RLBacktestPipeline jobs.
Saves checkpoints into SQLite via rl_checkpoint.
"""
import threading
import time
import pickle
from typing import Optional

from core.rl_backtest_pipeline import RLBacktestPipeline
from core.rl_checkpoint import save_checkpoint, init_db


class RLService:
    def __init__(self, db_path: str = './rl_checkpoints.db'):
        self.db_path = db_path
        self.worker: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.pipeline: Optional[RLBacktestPipeline] = None

    def start(self, symbols, models, controller_type='epsilon', rounds=100, light_mode=True, checkpoint_name='default'):
        if self.worker and self.worker.is_alive():
            raise RuntimeError('Worker already running')

        def target():
            self.pipeline = RLBacktestPipeline(symbols, models, controller_type=controller_type)
            # run in small batches and save checkpoint periodically
            batch = 10
            completed = 0
            while not self._stop.is_set() and completed < rounds:
                to_run = min(batch, rounds - completed)
                self.pipeline.run(rounds=to_run, use_mlflow=False, light_mode=light_mode)
                # save full pipeline controller state
                state = {
                    'arms': self.pipeline.arms,
                    'controller_type': type(self.pipeline.controller).__name__,
                    'controller_params': self.pipeline._controller_params(),
                    'counts': self.pipeline.controller.counts,
                    'values': self.pipeline.controller.values
                }
                state_blob = pickle.dumps(state)
                save_checkpoint(self.db_path, checkpoint_name, state_blob)
                completed += to_run
                time.sleep(0.1)

        init_db(self.db_path)
        self._stop.clear()
        self.worker = threading.Thread(target=target, daemon=True)
        self.worker.start()

    def stop(self):
        if self.worker and self.worker.is_alive():
            self._stop.set()
            self.worker.join(timeout=5)

    def status(self):
        return {
            'running': bool(self.worker and self.worker.is_alive()),
            'pipeline': {'arms': self.pipeline.arms} if self.pipeline else None
        }
