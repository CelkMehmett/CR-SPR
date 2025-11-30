#!/usr/bin/env python3
"""
Run paper trading simulations for each symbol using its per-symbol GA weights.
Generates individual trading results and equity curves for each symbol.

Output: per-symbol trading results with equity curves and metrics.
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd
import matplotlib.pyplot as plt
from src.trading.paper_trader import PaperTradingSimulator
from src.data.market_data import MarketDataLoader

PER_SYMBOL_DIR = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'snapshots', 'per_symbol_results')
TRADING_RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'per_symbol_trading')


def find_latest_ga_result_for_symbol(symbol: str, results_dir: str) -> dict:
    """
    Find the latest GA result JSON for a given symbol.
    """
    if not os.path.exists(results_dir):
        return None

    matching_files = [
        f for f in os.listdir(results_dir)
        if f.endswith('.json') and symbol in f and f != 'summary.json'
    ]

    if not matching_files:
        return None

    # Sort by timestamp (latest first)
    matching_files.sort(reverse=True)
    filepath = os.path.join(results_dir, matching_files[0])

    with open(filepath, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def run_paper_trading_for_symbol(symbol: str, ga_result: dict, days: int = 30) -> dict:
    """
    Run paper trading for a single symbol using GA-optimized weights.
    """
    print(f"\n  Paper trading for {symbol}...", end=' ')

    loader = MarketDataLoader()
    sim = PaperTradingSimulator(initial_capital=50000)

    try:
        # Fetch price data
        data = loader.fetch_historical_data(symbol, days=days)
        prices = loader.get_price_series(data)

        if len(prices) < 2:
            print(f"✗ Not enough price data")
            return {
                'symbol': symbol,
                'success': False,
                'error': 'Insufficient price data',
            }

        # Extract GA weights to generate signals (simple momentum-based)
        weight_history = ga_result.get('weight_history', {})
        weights_series = weight_history.get('weights', {}).get(symbol, [])

        # Generate signals based on weight trend
        equity_values = [50000]
        equity_times = [data.index[0]]
        trades_log = []

        for i in range(1, len(prices)):
            price = float(prices.iloc[i])
            prev_price = float(prices.iloc[i - 1])

            # Simple momentum signal: positive momentum = buy, negative = sell
            momentum = (price - prev_price) / prev_price if prev_price > 0 else 0

            # Get confidence from GA weight if available
            weight_idx = min(i - 1, len(weights_series) - 1)
            confidence = 0.5  # default
            if weight_idx >= 0 and weight_idx < len(weights_series):
                w = weights_series[weight_idx]
                if w is not None:
                    confidence = min(1.0, max(0.1, abs(w)))

            # Generate signal
            if momentum > 0.001:
                signal = 1  # BUY
            elif momentum < -0.001:
                signal = -1  # SELL
            else:
                signal = 0  # HOLD

            # Process signal
            if signal != 0:
                def quantity_fn(conf, cash, p):
                    risk = 50000 * 0.02  # risk 2% per trade
                    qty = max(1, int((risk * conf) / p))
                    return qty

                order = sim.process_signal(symbol, signal, confidence, price, quantity_fn=quantity_fn)
                if order:
                    trades_log.append({
                        'date': str(data.index[i]),
                        'signal': signal,
                        'price': price,
                        'confidence': confidence,
                    })

            # Update prices and record equity
            current_prices = {symbol: price}
            sim.update_prices(current_prices)
            portfolio_value = sim.portfolio.get_portfolio_value(current_prices)
            equity_values.append(portfolio_value)
            equity_times.append(data.index[i])

        # Get final performance
        final_prices = {symbol: float(prices.iloc[-1])}
        sim.update_prices(final_prices)
        performance = sim.get_performance()

        result = {
            'symbol': symbol,
            'success': True,
            'initial_capital': 50000,
            'final_value': performance.get('current_value', 50000),
            'total_return': performance.get('total_return', 0.0),
            'num_trades': len(trades_log),
            'equity_curve': {
                'times': [str(t) for t in equity_times],
                'values': equity_values,
            },
            'trades': trades_log[:10],  # first 10 trades
            'win_rate': performance.get('win_rate', 0.0),
        }

        print(f"✓ Return: {result['total_return']*100:.2f}% | Trades: {result['num_trades']}")
        return result

    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        return {
            'symbol': symbol,
            'success': False,
            'error': str(e),
        }


def plot_symbol_equity(symbol: str, equity_times: List[str], equity_values: List[float], output_dir: str):
    """
    Create an equity curve plot for a symbol.
    """
    try:
        plt.figure(figsize=(10, 4))
        times = pd.to_datetime(equity_times)
        plt.plot(times, equity_values, linewidth=2, color='#667eea')
        plt.fill_between(times, equity_values, alpha=0.2, color='#667eea')
        plt.title(f'{symbol} - Paper Trading Equity Curve', fontsize=12, fontweight='bold')
        plt.xlabel('Date', fontsize=10)
        plt.ylabel('Portfolio Value ($)', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        filename = f'{symbol}_equity.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        return filepath
    except Exception as e:
        print(f"    ⚠ Could not create plot: {e}")
        return None


def main():
    print(f"\n{'='*70}")
    print(f"Per-Symbol Paper Trading Simulation")
    print(f"{'='*70}\n")

    os.makedirs(TRADING_RESULTS_DIR, exist_ok=True)

    # Get list of available per-symbol GA results
    if not os.path.exists(PER_SYMBOL_DIR):
        print(f"Error: per-symbol GA results directory not found: {PER_SYMBOL_DIR}")
        print("Run: python3 scripts/run_ga_per_symbol.py first")
        return

    # Find all symbols with GA results
    symbols_with_results = set()
    for filename in os.listdir(PER_SYMBOL_DIR):
        if filename.endswith('_ga_result.json'):
            # Extract symbol from filename
            parts = filename.split('_')
            if len(parts) >= 2:
                symbol = parts[-3]  # format: timestamp_SYMBOL_ga_result.json
                if symbol.isupper():
                    symbols_with_results.add(symbol)

    symbols_with_results = sorted(list(symbols_with_results))
    print(f"Found GA results for {len(symbols_with_results)} symbols: {', '.join(symbols_with_results)}\n")

    # Run paper trading for each symbol
    all_trading_results = []
    successful = 0

    for symbol in symbols_with_results:
        ga_result = find_latest_ga_result_for_symbol(symbol, PER_SYMBOL_DIR)
        if not ga_result or not ga_result.get('success', False):
            print(f"  Skipping {symbol}: GA result not available")
            continue

        trading_result = run_paper_trading_for_symbol(symbol, ga_result)
        all_trading_results.append(trading_result)

        if trading_result['success']:
            successful += 1

            # Plot equity curve
            eq_data = trading_result.get('equity_curve', {})
            if eq_data.get('times') and eq_data.get('values'):
                plot_path = plot_symbol_equity(
                    symbol,
                    eq_data['times'],
                    eq_data['values'],
                    TRADING_RESULTS_DIR
                )
                if plot_path:
                    trading_result['equity_plot'] = plot_path

    # Persist individual results
    print(f"\nSaving per-symbol trading results...")
    for result in all_trading_results:
        if result['success']:
            symbol = result['symbol']
            filename = f'{symbol}_trading_result.json'
            filepath = os.path.join(TRADING_RESULTS_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as fh:
                json.dump(result, fh, indent=2, default=str)

    # Write summary
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_symbols': len(symbols_with_results),
        'successful_trades': successful,
        'results': all_trading_results,
        'top_performers': sorted(
            [r for r in all_trading_results if r['success']],
            key=lambda x: x.get('total_return', 0),
            reverse=True
        )[:5],
    }

    summary_path = os.path.join(TRADING_RESULTS_DIR, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2, default=str)

    print(f"\nWrote summary to: {summary_path}")

    # Print summary
    print(f"\n{'='*70}")
    print(f"Paper Trading Complete: {successful}/{len(symbols_with_results)} successful")
    print(f"{'='*70}\n")

    if summary['top_performers']:
        print("Top 5 Performers:")
        for i, perf in enumerate(summary['top_performers'], 1):
            ret = perf.get('total_return', 0) * 100
            symbol = perf.get('symbol', '?')
            print(f"  {i}. {symbol:6s} | Return: {ret:+7.2f}% | Trades: {perf.get('num_trades', 0)}")

    print(f"\nPer-symbol results saved to: {TRADING_RESULTS_DIR}/")


if __name__ == '__main__':
    main()
