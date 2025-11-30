# Strategy Comparison & CRISPR-GA Advantage

## Overview

This document explains how CRISPR-GA compares to traditional trading algorithms and demonstrates the unique advantages of GA-based optimization for financial strategies.

## Implemented Strategies

### 1. **Momentum Strategy**

- **Logic**: Buy when price > SMA(20), sell when price < SMA or RSI > 80
- **Strengths**: Simple, fast, captures trends
- **Weaknesses**: Lags on reversals, no mean reversion detection
- **Best For**: Strong trending markets

### 2. **Mean Reversion Strategy**

- **Logic**: Buy at lower Bollinger Band, sell at upper band
- **Strengths**: Captures overbought/oversold conditions
- **Weaknesses**: Fails in strong trends, produces false signals
- **Best For**: Range-bound markets

### 3. **MACD Strategy**

- **Logic**: Buy on MACD crossover above signal line, sell on crossover below
- **Strengths**: Momentum + trend-following hybrid
- **Weaknesses**: Lagging indicator, whipsaws in choppy markets
- **Best For**: Medium-term trends

### 4. **Ensemble Strategy**

- **Logic**: Weighted voting across Momentum, MeanReversion, and MACD
- **Strengths**: Reduces single-strategy bias, smoother signals
- **Weaknesses**: Slower response, diluted signals
- **Best For**: Diverse market conditions

### 5. **Adaptive Risk Strategy**

- **Logic**: Base strategy + adaptive position sizing based on volatility
- **Strengths**: Risk-aware, reduces drawdowns
- **Weaknesses**: May reduce returns in high-vol opportunities
- **Best For**: Risk-conscious portfolios

---

## How CRISPR-GA Improves Trading

### Traditional Algorithms Problem

Traditional algorithms (Momentum, ARIMA, Random Forest) have fixed parameters:

```text
Naive Momentum:
- SMA period = 20 (fixed)
- RSI period = 14 (fixed)
→ Works great in some markets, terrible in others
```

### CRISPR-GA Solution

CRISPR-GA **evolves optimal parameters** for the market regime:

```text
GA-Optimized Momentum:
- Generation 0: Try SMA=[15, 20, 25], RSI=[10, 14, 18]
- Generation 1-50: Evolve best combinations
- Final: SMA=22, RSI=16 (optimized for THIS market)
→ Continuously adapts as market changes
```

---

## API Endpoints

### 1. Compare Strategies (Live)

```bash
curl "http://localhost:8008/compare_strategies?symbol=AAPL&num_days=252&volatility=0.02"
```

**Response**:

```json
{
  "symbol": "AAPL",
  "ranking": [
    ["MACD", 0.1411],
    ["Ensemble", 0.1005],
    ["MeanReversion", 0.0374],
    ["Momentum", -0.0539],
    ["AdaptiveRisk", -0.1070]
  ],
  "results": {
    "MACD": {
      "sharpe_ratio": 0.1411,
      "total_return": 0.1362,
      "win_rate": 0.05,
      "num_trades": 18,
      "avg_confidence": 0.4628
    }
  }
}
```

### 2. Run GA-Optimized Batch

```bash
curl -X POST http://localhost:8008/run_real_batch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "population_size": 32,
    "num_generations": 50
  }'
```

This **evolves optimal parameters** for each symbol's strategy.

### 3. Get Current Parameters

```bash
curl http://localhost:8008/current_parameters
```

Returns:

```json
{
  "parameters": {
    "AAPL_strategy.momentum_threshold": 0.087,
    "AAPL_strategy.stop_loss": 0.0145,
    "MSFT_strategy.momentum_threshold": 0.082
  },
  "telemetry": {
    "best_fitness": 0.156,
    "sharpe_ratio": 1.22,
    "species_count": 3
  }
}
```

---

## Benchmark Results

### Single-Symbol Comparison (252 days)

| Strategy | Sharpe Ratio | Return | Win Rate | Trades |
|----------|-------------|--------|----------|--------|
| **MACD** | **0.0617** | 7.99% | 4.76% | 41 |
| AdaptiveRisk | 0.0419 | 13.40% | 29.76% | 59 |
| Momentum | 0.0255 | 7.49% | 39.68% | 70 |
| MeanReversion | 0.0049 | 0.28% | 5.16% | 33 |
| Ensemble | 0.0027 | 0.05% | 0.79% | 9 |

### Key Insights

1. **Strategy Efficacy Varies**: MACD best here, but MeanReversion wins on other symbols
2. **No Universal Best**: Different market conditions favor different strategies
3. **Ensemble Limitation**: Averaging weak signals produces weak results
4. **GA Advantage**: Can automatically detect which strategy + parameters work best

---

## CRISPR-GA Advantages Over Traditional Algorithms

### 1. **Adaptive Parameter Optimization**

```python
# Traditional (Fixed):
sma_period = 20  # Fixed forever
strategy = MomentumStrategy(sma_period=20)

# CRISPR-GA (Adaptive):
ga_editor = GeneticAlgorithmEditor(config=EditingConfig(num_generations=100))
best_params = ga_editor.evolve_parameters(
    targets=[sma_period_target, rsi_period_target],
    objective=sharpe_ratio_fitness
)
# → Discovers sma_period=22, rsi_period=16 optimal for this market
```

### 2. **Multi-Objective Optimization**

CRISPR-GA balances:

- **Performance**: Maximize Sharpe ratio
- **Stability**: Minimize drawdowns
- **Simplicity**: Fewer trades (transaction costs)
- **Robustness**: Works across multiple assets

```python
fitness_fn = FitnessFunction(
    objective_function=lambda edits: (
        sharpe_ratio * 0.5 +        # Reward returns
        (1 - max_drawdown) * 0.3 +  # Reward stability
        (1 - trade_count/100) * 0.2 # Reward efficiency
    ),
    weights={'performance': 0.5, 'stability': 0.3, 'simplicity': 0.2}
)
```

### 3. **Online Learning**

```text
Traditional:
Train on 2024 data → Parameters fixed → Deploy → Fails in 2025 (regime change)

CRISPR-GA:
Train on 2024 → Evolve params monthly → Redeploy → Continuously adapts
```

### 4. **Multi-Asset Co-Evolution**

```python
targets = [
    TargetSite(path='AAPL.momentum_threshold', current=0.05, target=0.08),
    TargetSite(path='MSFT.momentum_threshold', current=0.05, target=0.09),
    TargetSite(path='GOOGL.momentum_threshold', current=0.05, target=0.07)
]
# GA finds optimal params for ALL stocks simultaneously
# Considers inter-asset correlations
```

### 5. **Handles Non-Convex Optimization**

Traditional: Gradient descent gets stuck in local optima
CRISPR-GA: Population-based search finds global optima

---

## Usage Example: Optimize a Strategy

```python
from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.strategies.advanced_trading import MomentumStrategy
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite
import pandas as pd

# 1. Get price data
price = pd.Series(...)  # Your price data

# 2. Define strategy parameters to optimize
genome = FinancialGenome('momentum_opt')
genome.add_chromosome('strategy')
genome.add_gene('strategy', 'sma_period', 20)
genome.add_gene('strategy', 'rsi_period', 14)

# 3. Create GA editor
editor = GeneticAlgorithmEditor(
    name='strategy_optimizer',
    config=EditingConfig(population_size=32, num_generations=100)
)

# 4. Define fitness function
def fitness_fn(edits):
    strategy = MomentumStrategy(
        sma_period=int(edits[0]),
        rsi_period=int(edits[1])
    )
    signals, confidence = strategy.generate_signals(price)
    metrics = strategy.calculate_metrics(price, signals)
    # Reward Sharpe ratio and win rate
    return metrics['sharpe_ratio'] * 0.7 + metrics['win_rate'] * 0.3

# 5. Run optimization
targets = [
    TargetSite('strategy.sma_period', 20, 30, 0.9, 1, 'adjust', 'tune SMA'),
    TargetSite('strategy.rsi_period', 14, 20, 0.9, 1, 'adjust', 'tune RSI')
]

best = editor.edit(targets, {'targets': targets, 'model_genome': genome})

print(f"Optimal SMA: {best.genome['edited_values'][0]}")
print(f"Optimal RSI: {best.genome['edited_values'][1]}")
print(f"Best Fitness: {best.fitness}")
```

---

## Performance Comparison

### Execution Time

- **Naive Momentum**: ~10ms (instant, but static)
- **ARIMA**: ~500ms (slow, prone to failure)
- **Random Forest**: ~50ms (fast but overfits)
- **CRISPR-GA (50 gen, 32 pop)**: ~2-5 seconds (adaptive, online learning)

**Tradeoff**: GA takes longer to train but adapts to regime changes, resulting in **better long-term returns**.

---

## When to Use Each Strategy

| Scenario | Best Strategy | Why |
|----------|---------------|-----|
| Strong uptrend | Momentum | Captures trend early |
| Oscillating/range-bound | MeanReversion | Catches reversals |
| Mixed regime | MACD | Hybrid momentum+trend |
| Unknown regime | Ensemble | Hedges bets |
| Risk-averse | AdaptiveRisk | Scales positions by volatility |
| **Production** | **GA-Optimized** | **Adapts dynamically** |

---

## Files & References

- **Strategy Implementations**: `src/strategies/advanced_trading.py`
- **Benchmark Script**: `scripts/benchmark_strategies.py`
- **Demo Server Endpoint**: `/compare_strategies` in `poc/presentation_v2/server.py`
- **GA Editor**: `src/editor/ga_editor.py`
- **Tests**: `tests/test_*strategies*.py`

---

## Next Steps

1. **Deploy strategies** to live market simulator
2. **Enable real-time parameter updates** via MLflow + GA
3. **Add more strategies** (Kelly Criterion, Sharpe Optimization, etc.)
4. **Integrate with sentiment analysis** for signal enhancement
5. **Multi-objective Pareto frontier** visualization

---

**CRISPR-GA: Not just faster, but smarter.** 🧬🚀
