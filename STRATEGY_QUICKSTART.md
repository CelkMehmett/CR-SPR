# Strategy Comparison Quick Start

## 🚀 Run Demo in 30 Seconds

### 1. Start Demo Server

```bash
cd /home/mehmetcelik/crispr
python poc/presentation_v2/server.py
```

### 2. Compare Strategies (in another terminal)

```bash
# Compare on APPLE stock for 100 days with 3% volatility
curl "http://localhost:8008/compare_strategies?symbol=APPLE&num_days=100&volatility=0.03"
```

### 3. View Results

```json
{
  "symbol": "APPLE",
  "ranking": [
    ["MACD", 0.1411],
    ["Ensemble", 0.1005],
    ["MeanReversion", 0.0374],
    ["Momentum", -0.0539],
    ["AdaptiveRisk", -0.1070]
  ],
  "results": { }
}
```

## 📊 Run Full Benchmark

```bash
python scripts/benchmark_strategies.py
```

Output:

```text
=== STRATEGY COMPARISON FOR DEMO ===
Sharpe Ratio Ranking:
1. MACD: 0.0617 (Return: 7.99%, Win Rate: 4.76%, Max DD: 11.23%)
2. AdaptiveRisk: 0.0419 (Return: 13.40%, Win Rate: 29.76%, Max DD: 8.45%)
3. Momentum: 0.0255 (Return: 7.49%, Win Rate: 39.68%, Max DD: 12.34%)

=== MULTI-SYMBOL BENCHMARK ===
Symbol | MACD  | Ensemble | MeanRev | Momentum | AdaptRisk
DEMO   | 0.062 | 0.003    | 0.005   | 0.026    | 0.042
STOCK1 | 0.051 | 0.041    | 0.048   | 0.015    | 0.032
STOCK2 | 0.089 | 0.063    | 0.028   | 0.041    | 0.055
```

## 🧬 Use in Your Code

### Example 1: Run Strategies on Price Data

```python
from src.strategies.advanced_trading import (
    MomentumStrategy, MeanReversionStrategy, MacdStrategy,
    EnsembleStrategy, AdaptiveRiskStrategy, compare_strategies
)
import pandas as pd

# Your price data
price = pd.Series([100, 101.5, 102.3, 103.1, 102.8, ...])
volume = pd.Series([1000, 1200, 950, 1100, 1300, ...])

# Run single strategy
momentum = MomentumStrategy()
signals, confidence = momentum.generate_signals(price)
metrics = momentum.calculate_metrics(price, signals)
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
print(f"Win Rate: {metrics['win_rate']:.2%}")

# Compare all strategies
comparison = compare_strategies(price, volume, symbol='MYSTOCK')
for strategy_name, metrics in comparison.items():
    print(f"{strategy_name}: Sharpe={metrics['sharpe_ratio']:.4f}")
```

### Example 2: Optimize Strategy with GA

```python
from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.base_layers import TargetSite
from src.core.genome import FinancialGenome
from src.strategies.advanced_trading import MomentumStrategy

# Create GA editor
editor = GeneticAlgorithmEditor(
    name='momentum_optimizer',
    config=EditingConfig(population_size=32, num_generations=50)
)

# Define what to evolve
targets = [
    TargetSite(
        path='momentum.sma_period',
        current_value=20,
        target_value=30,
        step=0.9,
        increment=1,
        action='adjust',
        description='Optimize SMA period'
    ),
    TargetSite(
        path='momentum.rsi_period',
        current_value=14,
        target_value=20,
        step=0.9,
        increment=1,
        action='adjust',
        description='Optimize RSI period'
    )
]

# Fitness function
def fitness(edits):
    strategy = MomentumStrategy(
        sma_period=int(edits[0]),
        rsi_period=int(edits[1])
    )
    signals, conf = strategy.generate_signals(price_data)
    metrics = strategy.calculate_metrics(price_data, signals)
    # Maximize Sharpe ratio
    return metrics['sharpe_ratio']

# Run optimization
best = editor.edit(targets, {'targets': targets, 'model_genome': genome})
print(f"Optimal SMA: {best.genome['edited_values'][0]}")
print(f"Optimal RSI: {best.genome['edited_values'][1]}")
```

### Example 3: Real-time Updates

```python
from src.strategies.advanced_trading import AdaptiveRiskStrategy
import pandas as pd
import time

strategy = AdaptiveRiskStrategy()

while True:
    # Fetch latest price
    latest_price = fetch_price()  # Your data source
    price_series.append(latest_price)
    
    # Generate signal
    signals, confidence = strategy.generate_signals(
        pd.Series(price_series[-100:])  # Last 100 periods
    )
    
    if signals[-1] != 0:  # Buy or sell signal
        print(f"Signal: {signals[-1]}, Confidence: {confidence[-1]:.2%}")
        # Execute trade
        place_order(signal=signals[-1], size=calculate_size(confidence[-1]))
    
    time.sleep(60)  # Check every minute
```

## 📈 Strategy Selection Guide

| Your Scenario | Recommended Strategy | Reason |
|---------------|----------------------|--------|
| Strong trend expected | **Momentum** | Fast capture of directional moves |
| Range-bound market | **MeanReversion** | Catches reversals |
| Uncertain regime | **MACD** | Hybrid of trend + momentum |
| High uncertainty | **Ensemble** | Hedges across all approaches |
| Risk-averse trading | **AdaptiveRisk** | Scales position by volatility |
| Production system | **GA-Optimized** | Adapts automatically to regime |

## 🔧 Advanced: Custom Strategy

```python
from src.strategies.advanced_trading import AdvancedTradingStrategy
import pandas as pd
import numpy as np

class MyCustomStrategy(AdvancedTradingStrategy):
    def generate_signals(self, price):
        """Generate buy (1), sell (-1), hold (0) signals"""
        # Your logic here
        signals = np.zeros(len(price))
        confidence = np.zeros(len(price))
        
        # Example: Buy when price crosses 50-day MA
        ma50 = price.rolling(50).mean()
        signals[price > ma50] = 1
        signals[price < ma50] = -1
        
        confidence = np.abs(price - ma50) / ma50  # Distance from MA
        
        return signals, confidence
    
    def calculate_metrics(self, price, signals):
        """Calculate performance metrics"""
        # Your calculation here (or use parent's)
        return super().calculate_metrics(price, signals)

# Use it
strategy = MyCustomStrategy()
signals, confidence = strategy.generate_signals(price)
metrics = strategy.calculate_metrics(price, signals)
```

## 📚 API Reference

### Compare Strategies Endpoint

**URL**: `GET /compare_strategies`

**Query Parameters**:

- `symbol` (string): Stock symbol (default: "DEMO")
- `num_days` (int): Number of days to simulate (default: 252)
- `volatility` (float): Volatility parameter (default: 0.02)

**Response**:

```json
{
  "symbol": "AAPL",
  "num_days": 252,
  "ranking": [
    ["MACD", 0.1411],
    ["Ensemble", 0.1005]
  ],
  "results": {
    "MACD": {
      "sharpe_ratio": 0.1411,
      "total_return": 0.1362,
      "win_rate": 0.05,
      "max_drawdown": 0.193,
      "num_trades": 18,
      "avg_confidence": 0.4628
    }
  }
}
```

### Files Reference

- **Strategies**: `src/strategies/advanced_trading.py`
- **Benchmark**: `scripts/benchmark_strategies.py`
- **Server**: `poc/presentation_v2/server.py`
- **Documentation**: `docs/STRATEGY_COMPARISON.md`

## 🎯 Next Steps

1. **Compare strategies** on your own price data
2. **Identify best strategy** for your market regime
3. **Integrate with GA** to auto-optimize parameters
4. **Monitor performance** and retrain monthly
5. **Deploy to production** with confidence scoring

---

**Questions?** Check `docs/STRATEGY_COMPARISON.md` for detailed explanations.

**Issues?** Run tests: `pytest tests/ -v`

**Performance tips**:

- Use `volatility=0.01-0.03` for realistic scenarios
- Increase `num_days` to 500+ for robust backtests
- Use Ensemble when regime is uncertain
- Use MACD for confirmed trends
