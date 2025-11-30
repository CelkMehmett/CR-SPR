"""
Pipeline to connect RL bandit controller (`core.rl_controller`) with
the CRISPR backtester (`core.backtest_integration`).

Behavior:
- Initialize a bandit controller over available models
- For a number of rounds: select a model, run a lightweight backtest, compute reward, update controller

This is a demo harness — in production you would provide real state, richer reward,
and persistence for learned estimates.
"""
from typing import List
import time

import sys
from pathlib import Path
# ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.rl_controller import EpsilonGreedyController, UCB1Controller, SoftmaxController
from core.backtest_integration import CRISPRBacktestIntegration
import json
import tempfile
import os

try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except Exception:
    MLFLOW_AVAILABLE = False


class RLBacktestPipeline:
    def __init__(self, symbols: List[str], models: List[str], controller_type: str = 'epsilon', **kwargs):
        self.symbols = symbols
        self.models = models
        self.integration = CRISPRBacktestIntegration()

        # create arm names as symbol|model combinations
        self.arms = [f"{s}|{m}" for s in symbols for m in models]

        if controller_type == 'epsilon':
            self.controller = EpsilonGreedyController(self.arms, epsilon=kwargs.get('epsilon', 0.1))
        elif controller_type == 'ucb':
            self.controller = UCB1Controller(self.arms, c=kwargs.get('c', 2.0))
        elif controller_type == 'softmax':
            self.controller = SoftmaxController(self.arms, tau=kwargs.get('tau', 0.5))
        else:
            raise ValueError('Unknown controller_type')

    def _parse_arm(self, arm: str):
        s, m = arm.split('|', 1)
        return s, m

    def save_checkpoint(self, path: str):
        import pickle
        state = {
            'counts': self.controller.counts,
            'values': self.controller.values,
            'arms': self.arms,
            'controller_type': type(self.controller).__name__,
            'controller_params': self._controller_params(),
            'controller_class': type(self.controller).__name__
        }
        with open(path, 'wb') as f:
            pickle.dump(state, f)

    def load_checkpoint(self, path: str):
        import pickle
        with open(path, 'rb') as f:
            state = pickle.load(f)
        # rehydrate controller: recreate controller of saved type if needed
        saved_type = state.get('controller_type')
        params = state.get('controller_params', {})
        # if types mismatch, recreate controller
        if saved_type and type(self.controller).__name__ != saved_type:
            # instantiate the right controller class
            if saved_type == 'EpsilonGreedyController':
                self.controller = EpsilonGreedyController(state.get('arms', self.arms), epsilon=params.get('epsilon', 0.1))
            elif saved_type == 'UCB1Controller':
                self.controller = UCB1Controller(state.get('arms', self.arms), c=params.get('c', 2.0))
            elif saved_type == 'SoftmaxController':
                self.controller = SoftmaxController(state.get('arms', self.arms), tau=params.get('tau', 0.5))
        # overwrite arms if present
        if 'arms' in state:
            self.arms = state['arms']
        # now overwrite counts/values
        for a, c in state.get('counts', {}).items():
            if a in self.controller.counts:
                self.controller.counts[a] = c
        for a, v in state.get('values', {}).items():
            if a in self.controller.values:
                self.controller.values[a] = v

    def _controller_params(self):
        # Extract constructor params for known controllers
        t = type(self.controller).__name__
        if t == 'EpsilonGreedyController':
            return {'epsilon': getattr(self.controller, 'epsilon', 0.1)}
        if t == 'UCB1Controller':
            return {'c': getattr(self.controller, 'c', 2.0)}
        if t == 'SoftmaxController':
            return {'tau': getattr(self.controller, 'tau', 0.5)}
        return {}

    def compute_reward_from_backtest(self, backtest_result: dict) -> float:
        """Compute a scalar reward from a comprehensive backtest result.
        Default: use simple backtest sharpe ratio (clipped to reasonable range).
        """
        try:
            sharpe = backtest_result['simple']['sharpe_ratio']
            # map sharpe to a bounded reward (e.g., -1..+1)
            reward = max(-2.0, min(2.0, float(sharpe))) / 2.0
            return reward
        except Exception:
            # fallback: small negative reward for failures
            return -0.1

    def run(self, rounds: int = 20, sleep_between: float = 0.2, use_mlflow: bool = False, light_mode: bool = False):
        mlflow_client = None
        experiment_id = None
        if use_mlflow and MLFLOW_AVAILABLE:
            mlflow.set_tracking_uri(os.environ.get('MLFLOW_TRACKING_URI', './mlruns'))
            exp_name = os.environ.get('MLFLOW_EXPERIMENT_NAME', 'RL-Controller-Pipeline')
            try:
                experiment = mlflow.get_experiment_by_name(exp_name)
                if experiment is None:
                    experiment_id = mlflow.create_experiment(exp_name)
                else:
                    experiment_id = experiment.experiment_id
                mlflow_client = MlflowClient()
            except Exception as e:
                print(f"⚠️  MLflow init failed: {e}")
                mlflow_client = None

        history = []
        for t in range(1, rounds + 1):
            arm = self.controller.select()
            symbol, model = self._parse_arm(arm)

            print(f"[Round {t}/{rounds}] Selected: {symbol} - {model} (arm={arm})")

            # run simple or comprehensive backtest depending on light_mode
            if light_mode:
                result = self.integration.run_simple_backtest_light(symbol, model)
            else:
                result = self.integration.run_comprehensive_backtest(symbol, model)
            if not result:
                reward = -0.1
                print(f"  ❌ backtest failed or missing data for {arm}, applying reward {reward}")
            else:
                reward = self.compute_reward_from_backtest(result)
                print(f"  ✅ backtest Sharpe: {result['simple']['sharpe_ratio']:.3f} -> reward {reward:.3f}")

            # optionally log to MLflow
            if use_mlflow and MLFLOW_AVAILABLE and mlflow_client is not None:
                try:
                    with mlflow.start_run(experiment_id=experiment_id, nested=False):
                        mlflow.set_tag('controller', type(self.controller).__name__)
                        mlflow.set_tag('symbol', symbol)
                        mlflow.set_tag('model', model)
                        mlflow.log_param('arm', arm)
                        mlflow.log_param('round', t)
                        mlflow.log_metric('reward', float(reward))
                        # log sharpe if available
                        try:
                            sharpe_val = float(result['simple']['sharpe_ratio'])
                            mlflow.log_metric('sharpe_ratio', sharpe_val)
                        except Exception:
                            pass

                        # save full result as artifact
                        try:
                            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                            json.dump(result or {}, tmp)
                            tmp.close()
                            mlflow.log_artifact(tmp.name, artifact_path='results')
                            os.unlink(tmp.name)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"⚠️  Failed to log to MLflow: {e}")

            # update controller
            self.controller.update(arm, reward)
            history.append({'round': t, 'arm': arm, 'reward': reward})

            time.sleep(sleep_between)

        return history


def demo():
    symbols = ['AAPL', 'GOOGL']
    models = ['naive_momentum', 'random_forest']

    pipeline = RLBacktestPipeline(symbols, models, controller_type='epsilon', epsilon=0.15)
    use_mlflow = os.environ.get('MLFLOW_ENABLE', '0') in ('1', 'true', 'True')

    # run first batch (light_mode) and save checkpoint
    history1 = pipeline.run(rounds=4, use_mlflow=use_mlflow, light_mode=True)
    ckpt = 'controller_checkpoint.pkl'
    pipeline.save_checkpoint(ckpt)
    print(f"Checkpoint saved: {ckpt}")

    # create a new pipeline and load checkpoint to resume
    pipeline2 = RLBacktestPipeline(symbols, models, controller_type='epsilon', epsilon=0.15)
    pipeline2.load_checkpoint(ckpt)
    print('Loaded checkpoint into new pipeline. Counts before resume:', pipeline2.controller.counts)

    history2 = pipeline2.run(rounds=8, use_mlflow=use_mlflow, light_mode=True)

    print('\nPipeline completed. Final Selection counts:')
    print(pipeline2.controller.counts)
    print('Estimates:')
    print(pipeline2.controller.values)


if __name__ == '__main__':
    demo()
