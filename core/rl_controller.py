"""
Lightweight RL Controller (bandit-style) for dynamic model selection.

Includes:
- EpsilonGreedyController
- UCB1Controller
- SoftmaxController

Provides a small simulation demo at the bottom to validate behavior.
"""
from __future__ import annotations
import math
import random
from typing import List, Dict, Tuple


class BanditController:
    """Base class for simple multi-armed bandit controllers.

    Arms correspond to models. Controllers maintain estimates and select arms.
    """

    def __init__(self, arms: List[str]):
        if not arms:
            raise ValueError("arms must be a non-empty list")
        self.arms = list(arms)
        self.counts = dict.fromkeys(self.arms, 0)
        self.values = dict.fromkeys(self.arms, 0.0)  # estimated reward

    def select(self) -> str:
        raise NotImplementedError()

    def update(self, arm: str, reward: float):
        """Update internal estimates for given arm with observed reward."""
        if arm not in self.arms:
            raise KeyError(f"Unknown arm: {arm}")
        self.counts[arm] += 1
        n = self.counts[arm]
        # incremental mean
        self.values[arm] += (reward - self.values[arm]) / n

    def get_estimates(self) -> Dict[str, float]:
        return dict(self.values)


class EpsilonGreedyController(BanditController):
    def __init__(self, arms: List[str], epsilon: float = 0.1):
        super().__init__(arms)
        if not (0.0 <= epsilon <= 1.0):
            raise ValueError("epsilon must be between 0 and 1")
        self.epsilon = epsilon

    def select(self) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.arms)
        # pick best estimated value (tie-break randomly)
        best_val = max(self.values.values())
        best_arms = [a for a, v in self.values.items() if v == best_val]
        return random.choice(best_arms)


class UCB1Controller(BanditController):
    def __init__(self, arms: List[str], c: float = 2.0):
        super().__init__(arms)
        if c <= 0:
            raise ValueError("c must be positive")
        self.c = c
        self.total_counts = 0

    def select(self) -> str:
        # initially play each arm once
        for a in self.arms:
            if self.counts[a] == 0:
                return a

        self.total_counts = sum(self.counts.values())
        best_score = None
        best_arm = None
        for a in self.arms:
            avg = self.values[a]
            bonus = self.c * math.sqrt(math.log(max(1, self.total_counts)) / self.counts[a])
            score = avg + bonus
            if best_score is None or score > best_score:
                best_score = score
                best_arm = a

        return best_arm


class SoftmaxController(BanditController):
    def __init__(self, arms: List[str], tau: float = 0.5):
        super().__init__(arms)
        if tau <= 0:
            raise ValueError("tau must be positive")
        self.tau = tau

    def select(self) -> str:
        # compute softmax probabilities
        vals = list(self.values.values())
        maxv = max(vals)
        exps = [math.exp((v - maxv) / self.tau) for v in vals]
        s = sum(exps)
        probs = [e / s for e in exps]
        return random.choices(self.arms, weights=probs, k=1)[0]


# -----------------------------
# Demo simulation: synthetic model returns
def simulate(controller: BanditController, true_means: Dict[str, float], rounds: int = 500) -> Dict[str, any]:
    """Run a simulation where each arm generates rewards ~ N(true_mean, 0.1).

    Returns summary with selections and cumulative rewards.
    """
    history: List[Tuple[int, str, float]] = []
    cumulative = 0.0
    for t in range(1, rounds + 1):
        arm = controller.select()
        mu = true_means[arm]
        reward = random.gauss(mu, 0.1)
        controller.update(arm, reward)
        cumulative += reward
        history.append((t, arm, reward))

    summary = {
        "rounds": rounds,
        "total_reward": cumulative,
        "counts": dict(controller.counts),
        "estimates": dict(controller.values),
    }
    return summary


if __name__ == "__main__":
    # Demo: three models with different true means (A>B>C)
    arms = ["naive_momentum", "arima", "random_forest"]
    true_means = {
        "naive_momentum": 0.15,
        "arima": 0.08,
        "random_forest": 0.12
    }

    print("Demo: Epsilon-Greedy (epsilon=0.1)")
    eg = EpsilonGreedyController(arms, epsilon=0.1)
    res = simulate(eg, true_means, rounds=500)
    print(res)

    print("\nDemo: UCB1 (c=2.0)")
    ucb = UCB1Controller(arms, c=2.0)
    res2 = simulate(ucb, true_means, rounds=500)
    print(res2)

    print("\nDemo: Softmax (tau=0.3)")
    sm = SoftmaxController(arms, tau=0.3)
    res3 = simulate(sm, true_means, rounds=500)
    print(res3)
