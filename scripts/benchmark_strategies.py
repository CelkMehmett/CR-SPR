"""Compare CRISPR-GA optimized strategies vs. traditional algorithms.

This script demonstrates how CRISPR GA can optimize trading strategies
and compares results against naive momentum, ARIMA, and other algorithms.
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Setup paths FIRST
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pandas as pd
import numpy as np

from src.strategies.advanced_trading import (
    compare_strategies, rank_strategies, MomentumStrategy, EnsembleStrategy
)
from src.eval.backtest import simple_backtest

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def generate_synthetic_price_data(num_days: int = 252, start_price: float = 100.0, drift: float = 0.0005, volatility: float = 0.02) -> pd.Series:
    """Generate synthetic price data for testing."""
    returns = np.random.normal(drift, volatility, num_days)
    prices = start_price * np.exp(np.cumsum(returns))
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')
    return pd.Series(prices, index=dates)


def run_strategy_comparison(symbol: str = 'TEST', num_days: int = 252) -> Dict[str, Any]:
    """Run comparison of different trading strategies.

    Returns:
        Dictionary with benchmark results
    """
    logger.info(f'Generating {num_days} days of synthetic price data for {symbol}...')
    price = generate_synthetic_price_data(num_days)

    logger.info('Running strategy comparison...')
    results = compare_strategies(price, symbol=symbol)

    logger.info('Ranking strategies by Sharpe ratio...')
    ranking = rank_strategies(results)

    logger.info('\n' + '=' * 60)
    logger.info('STRATEGY COMPARISON RESULTS')
    logger.info('=' * 60)

    for i, (name, score) in enumerate(ranking, 1):
        metrics = results[name]
        logger.info(
            f'\n{i}. {name} (Sharpe: {score:.4f})\n'
            f'   Total Return: {metrics.get("total_return", 0):.2%}\n'
            f'   Win Rate: {metrics.get("win_rate", 0):.2%}\n'
            f'   Max Drawdown: {metrics.get("max_drawdown", 0):.4f}\n'
            f'   Num Trades: {metrics.get("num_trades", 0)}\n'
            f'   Avg Confidence: {metrics.get("avg_confidence", 0):.3f}'
        )

    logger.info('\n' + '=' * 60)
    logger.info('KEY INSIGHTS')
    logger.info('=' * 60)

    best_name, best_score = ranking[0]
    logger.info(f'✅ Best Strategy: {best_name} (Sharpe: {best_score:.4f})')

    # Calculate performance gap
    if len(ranking) > 1:
        worst_name, worst_score = ranking[-1]
        gap_pct = ((best_score - worst_score) / abs(worst_score)) * 100 if worst_score != 0 else 0
        logger.info(f'📈 Performance Gap: {gap_pct:.1f}% better than {worst_name}')

    # Ensemble outperformance
    if 'Ensemble' in results:
        ensemble_sharpe = results['Ensemble']['sharpe_ratio']
        momentum_sharpe = results.get('Momentum', {}).get('sharpe_ratio', 0)
        if momentum_sharpe > 0:
            outperf = ((ensemble_sharpe - momentum_sharpe) / momentum_sharpe) * 100
            logger.info(f'🎯 Ensemble: {outperf:+.1f}% vs. Momentum')

    logger.info('\n' + '=' * 60)
    logger.info('HOW CRISPR-GA IMPROVES THIS')
    logger.info('=' * 60)
    logger.info('''
1. Parameter Optimization: GA tuned (band_period, std_dev, lookback, etc.)
2. Adaptive Weighting: GA learns optimal strategy weights in Ensemble
3. Market Regime Detection: GA detects when strategies work best
4. Risk Adjustment: GA optimizes position sizing based on volatility
5. Multi-Asset Co-evolution: GA coordinates strategies across assets

CRISPR Advantage over traditional algorithms:
- Naive Momentum: No adaptation to market conditions
- ARIMA: Assumes linear trends (fails in regimes)
- Random Forest: No online learning (works on historical data only)
- GA: Evolves continuously, adapts to new market data, multi-objective
    ''')

    return {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'num_days': num_days,
        'results': results,
        'ranking': ranking
    }


def run_multi_symbol_benchmark(symbols: list = None, num_days: int = 252) -> Dict[str, Any]:
    """Run benchmark across multiple symbols."""
    if symbols is None:
        symbols = ['TECH', 'BANK', 'ENERGY', 'RETAIL']

    all_results = {}
    for symbol in symbols:
        logger.info(f'\n{"=" * 60}\nProcessing {symbol}...\n{"=" * 60}')
        result = run_strategy_comparison(symbol, num_days)
        all_results[symbol] = result

    # Aggregate metrics
    logger.info('\n' + '=' * 80)
    logger.info('MULTI-SYMBOL SUMMARY')
    logger.info('=' * 80)

    strategy_scores = {}
    for symbol, result in all_results.items():
        for name, score in result['ranking']:
            if name not in strategy_scores:
                strategy_scores[name] = []
            metrics = result['results'][name]
            strategy_scores[name].append(metrics.get('sharpe_ratio', 0))

    logger.info('\nAverage Sharpe Ratio Across Symbols:')
    for name in sorted(strategy_scores.keys(), key=lambda x: np.mean(strategy_scores[x]), reverse=True):
        avg_sharpe = np.mean(strategy_scores[name])
        std_sharpe = np.std(strategy_scores[name])
        logger.info(f'  {name:20s}: {avg_sharpe:.4f} ± {std_sharpe:.4f}')

    return all_results


if __name__ == '__main__':
    # Run single-symbol comparison
    logger.info('Starting CRISPR Strategy Benchmark...\n')
    single_result = run_strategy_comparison(symbol='DEMO', num_days=252)

    # Optional: multi-symbol
    logger.info('\n\nRunning multi-symbol benchmark...\n')
    multi_results = run_multi_symbol_benchmark(symbols=['STOCK1', 'STOCK2', 'STOCK3'], num_days=252)

    # Save results
    output_file = os.path.join(REPO_ROOT, 'strategy_comparison_results.json')
    with open(output_file, 'w') as f:
        # Convert to JSON-serializable format
        json_data = {
            'timestamp': datetime.now().isoformat(),
            'single_symbol_result': {
                'ranking': single_result['ranking'],
                'results_summary': {k: {k2: str(v2) if not isinstance(v2, (int, float)) else v2
                                         for k2, v2 in v.items()} 
                                   for k, v in single_result['results'].items()}
            }
        }
        json.dump(json_data, f, indent=2)
    logger.info(f'\n✅ Results saved to {output_file}')
