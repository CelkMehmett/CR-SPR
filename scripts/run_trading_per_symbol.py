#!/usr/bin/env python3
"""
Run paper trading for each symbol with simulated GA-optimized weights.
Generates per-symbol trading results and equity curves.

This script simulates trading for each symbol independently, 
fetching price data and generating buy/sell signals based on momentum.
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

TRADING_RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'per_symbol_trading')

# Symbols to trade
SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'TSLA', 'META', 'NFLX', 'ADBE', 'JPM',
    'BAC', 'XOM', 'CVX', 'DIS', 'INTC',
    'KO', 'PFE', 'VZ', 'WMT', 'GLD',
]


def run_paper_trading_for_symbol(symbol: str, days: int = 30, initial_capital: int = 50000) -> dict:
    """
    Run paper trading for a single symbol using momentum-based signals.
    """
    print(f"  {symbol:6s}...", end=' ')
    sys.stdout.flush()

    loader = MarketDataLoader()
    sim = PaperTradingSimulator(initial_capital=initial_capital)

    try:
        # Fetch price data
        data = loader.fetch_historical_data(symbol, days=days)
        prices = loader.get_price_series(data)

        if len(prices) < 5:
            print(f"✗ Insufficient data")
            return {
                'symbol': symbol,
                'success': False,
                'error': 'Insufficient price data',
            }

        # Paper trading loop with momentum signals
        equity_values = [initial_capital]
        equity_times = [data.index[0]]
        trades_log = []
        position_held = False

        for i in range(1, len(prices)):
            price = float(prices.iloc[i])
            prev_price = float(prices.iloc[i - 1])

            # Calculate momentum (simple: price change %)
            momentum = (price - prev_price) / prev_price if prev_price > 0 else 0

            # Generate signal: threshold-based
            momentum_threshold = 0.005  # 0.5% threshold
            if momentum > momentum_threshold and not position_held:
                signal = 1  # BUY
                confidence = min(0.9, abs(momentum) * 100)
            elif momentum < -momentum_threshold and position_held:
                signal = -1  # SELL
                confidence = min(0.9, abs(momentum) * 100)
            else:
                signal = 0  # HOLD
                confidence = 0.5

            # Process signal
            if signal != 0:
                def quantity_fn(conf, cash, p):
                    risk = initial_capital * 0.02  # risk 2% per trade
                    qty = max(1, int((risk * conf) / p))
                    return qty

                order = sim.process_signal(symbol, signal, confidence, price, quantity_fn=quantity_fn)
                if order:
                    position_held = (signal == 1)
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
            'initial_capital': initial_capital,
            'final_value': performance.get('current_value', initial_capital),
            'total_return': performance.get('total_return', 0.0),
            'num_trades': len(trades_log),
            'equity_curve': {
                'times': [str(t) for t in equity_times],
                'values': equity_values,
            },
            'trades': trades_log,  # ALL trades
            'win_rate': performance.get('win_rate', 0.0),
            'pnl': performance.get('unrealized_pnl', 0.0),
        }

        ret_pct = result['total_return'] * 100
        print(f"✓ Return: {ret_pct:+7.2f}% | Trades: {result['num_trades']}")
        return result

    except Exception as e:
        print(f"✗ {str(e)[:40]}")
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
        plt.figure(figsize=(12, 4))
        times = pd.to_datetime(equity_times)
        plt.plot(times, equity_values, linewidth=2.5, color='#667eea')
        plt.fill_between(times, equity_values, alpha=0.15, color='#667eea')
        
        # Add final value annotation
        final_val = equity_values[-1]
        initial_val = equity_values[0]
        ret_pct = ((final_val - initial_val) / initial_val) * 100
        
        plt.title(f'{symbol} - Paper Trading Equity Curve (Return: {ret_pct:+.2f}%)', 
                 fontsize=13, fontweight='bold')
        plt.xlabel('Date', fontsize=11)
        plt.ylabel('Portfolio Value ($)', fontsize=11)
        plt.grid(True, alpha=0.2, linestyle='--')
        plt.tight_layout()

        filename = f'{symbol}_equity.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        return filepath
    except Exception as e:
        return None


def main():
    print(f"\n{'='*70}")
    print(f"Per-Symbol Paper Trading Simulation")
    print(f"{'='*70}\n")

    os.makedirs(TRADING_RESULTS_DIR, exist_ok=True)

    print(f"Running paper trading for {len(SYMBOLS)} symbols...\n")

    all_trading_results = []
    successful = 0

    for symbol in SYMBOLS:
        trading_result = run_paper_trading_for_symbol(symbol, days=60, initial_capital=50000)
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

    # Write summary and rankings
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_symbols': len(SYMBOLS),
        'successful_trades': successful,
        'top_gainers': sorted(
            [r for r in all_trading_results if r['success']],
            key=lambda x: x.get('total_return', 0),
            reverse=True
        )[:5],
        'top_traders': sorted(
            [r for r in all_trading_results if r['success']],
            key=lambda x: x.get('num_trades', 0),
            reverse=True
        )[:5],
    }

    summary_path = os.path.join(TRADING_RESULTS_DIR, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2, default=str)

    print(f"Wrote summary to: {summary_path}")

    # Print summary
    print(f"\n{'='*70}")
    print(f"Paper Trading Complete: {successful}/{len(SYMBOLS)} successful")
    print(f"{'='*70}\n")

    if summary['top_gainers']:
        print("🏆 Top 5 Gainers:")
        for i, perf in enumerate(summary['top_gainers'], 1):
            ret = perf.get('total_return', 0) * 100
            symbol = perf.get('symbol', '?')
            print(f"  {i}. {symbol:6s} | Return: {ret:+7.2f}% | Trades: {perf.get('num_trades', 0):3d}")

    if summary['top_traders']:
        print("\n📊 Most Active (Most Trades):")
        for i, perf in enumerate(summary['top_traders'], 1):
            ret = perf.get('total_return', 0) * 100
            symbol = perf.get('symbol', '?')
            print(f"  {i}. {symbol:6s} | Trades: {perf.get('num_trades', 0):3d} | Return: {ret:+7.2f}%")

    print(f"\nPer-symbol results saved to: {TRADING_RESULTS_DIR}/")
    print(f"Open live_demo.html to view results.\n")


if __name__ == '__main__':
    main()
