"""
Integration module: Connect Advanced Backtester with CRISPR models
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.advanced_backtester import (
    AdvancedBacktester,
    BacktestConfig
)


class CRISPRBacktestIntegration:
    """
    Integrates Advanced Backtester with CRISPR-FinAI models.
    """

    def __init__(self, data_dir: str = "poc/scale_results_quick"):
        self.data_dir = Path(data_dir)
        self.results_file = self.data_dir / "scale_compare_results.csv"
        self.config = BacktestConfig(
            initial_capital=100000.0,
            commission=0.001,
            slippage=0.0005,
            train_window=252,
            test_window=63,
            step_size=21,
            n_simulations=1000
        )
        self.backtester = AdvancedBacktester(self.config)

    def load_model_data(self, symbol: str, model: str) -> Optional[pd.DataFrame]:
        """Load historical data for a specific symbol/model."""
        # In production, load actual historical data
        # For now, generate synthetic data based on model characteristics

        if not self.results_file.exists():
            return None

        df = pd.read_csv(self.results_file)
        model_row = df[(df['symbol'] == symbol) & (df['model'] == model)]

        if model_row.empty:
            return None

        # Generate synthetic returns matching model characteristics
        sharpe = model_row['sharpe'].values[0]
        volatility = model_row['volatility'].values[0]

        # Approximate annual return from Sharpe
        annual_return = sharpe * volatility
        daily_return = annual_return / 252

        # Generate 2 years of daily returns
        n_days = 504  # ~2 years
        np.random.seed(hash(symbol + model) % 2**32)

        returns = np.random.normal(daily_return, volatility / np.sqrt(252), n_days)
        dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

        data = pd.DataFrame({
            'date': dates,
            'returns': returns,
            'symbol': symbol,
            'model': model
        })

        return data

    def run_comprehensive_backtest(self,
                                   symbol: str,
                                   model: str) -> Optional[Dict]:
        """
        Run comprehensive backtest including simple, walk-forward, and Monte Carlo.
        """
        print(f"\n{'='*60}")
        print(f"📊 Running Comprehensive Backtest: {symbol} - {model}")
        print(f"{'='*60}")

        # Load data
        data = self.load_model_data(symbol, model)
        if data is None:
            print(f"❌ No data found for {symbol}/{model}")
            return None

        returns = data['returns'].values
        dates = data['date']

        # Generate simple momentum signals
        signals = self._generate_signals(returns)

        # 1. Simple Backtest
        print("\n1️⃣  Simple Backtest...")
        simple_result = self.backtester.run_simple_backtest(returns, signals, dates)

        # 2. Walk-Forward Analysis
        print("2️⃣  Walk-Forward Analysis...")
        wf_result = self.backtester.walk_forward_analysis(
            returns,
            self._signal_generator_wrapper,
            dates
        )

        # 3. Monte Carlo Simulation
        print("3️⃣  Monte Carlo Simulation...")
        mc_result = self.backtester.monte_carlo_simulation(returns, signals)

        print("✅ All tests completed!")

        return {
            'symbol': symbol,
            'model': model,
            'simple': simple_result.to_dict(),
            'walk_forward': wf_result,
            'monte_carlo': mc_result,
            'timestamp': datetime.now().isoformat()
        }

    def run_simple_backtest_light(self, symbol: str, model: str) -> Optional[Dict]:
        """Lightweight simple backtest: run only the fast simple backtest and return key metrics.

        This avoids walk-forward and Monte Carlo for speed in production pipelines.
        """
        data = self.load_model_data(symbol, model)
        if data is None:
            return None

        returns = data['returns'].values
        dates = data['date']
        signals = self._generate_signals(returns)
        simple_result = self.backtester.run_simple_backtest(returns, signals, dates)
        # Return a minimal dict
        return {
            'symbol': symbol,
            'model': model,
            'simple': simple_result.to_dict(),
            'timestamp': datetime.now().isoformat()
        }

    def _generate_signals(self, returns: np.ndarray, lookback: int = 20) -> np.ndarray:
        """Generate trading signals from returns."""
        momentum = pd.Series(returns).rolling(lookback).mean()
        signals = np.zeros(len(returns))
        signals[momentum > 0] = 1
        signals[momentum < 0] = -1
        return signals

    def _signal_generator_wrapper(self, returns: np.ndarray, **kwargs) -> np.ndarray:
        """Wrapper for signal generation in walk-forward analysis."""
        return self._generate_signals(returns)

    def batch_backtest_all_models(self) -> List[Dict]:
        """Run comprehensive backtest on all models."""
        if not self.results_file.exists():
            print(f"❌ Results file not found: {self.results_file}")
            return []

        df = pd.read_csv(self.results_file)

        results = []
        total = len(df)

        print(f"\n{'='*60}")
        print(f"🚀 Batch Backtesting {total} Models")
        print(f"{'='*60}")

        for idx, row in df.iterrows():
            symbol = row['symbol']
            model = row['model']

            print(f"\n[{idx+1}/{total}] Testing {symbol} - {model}...")

            result = self.run_comprehensive_backtest(symbol, model)
            if result:
                results.append(result)

        return results

    def compare_backtest_vs_baseline(self, symbol: str, model: str) -> Dict:
        """Compare advanced backtest results with baseline results."""
        # Load baseline results
        if not self.results_file.exists():
            return {}

        df = pd.read_csv(self.results_file)
        baseline = df[(df['symbol'] == symbol) & (df['model'] == model)]

        if baseline.empty:
            return {}

        # Run advanced backtest
        advanced = self.run_comprehensive_backtest(symbol, model)

        if not advanced:
            return {}

        comparison = {
            'symbol': symbol,
            'model': model,
            'baseline': {
                'sharpe': float(baseline['sharpe'].values[0]),
                'volatility': float(baseline['volatility'].values[0]),
                'win_rate': float(baseline['win_rate'].values[0])
            },
            'advanced': {
                'simple': {
                    'sharpe': advanced['simple']['sharpe_ratio'],
                    'total_return': advanced['simple']['total_return'],
                    'max_drawdown': advanced['simple']['max_drawdown'],
                    'win_rate': advanced['simple']['win_rate']
                },
                'walk_forward': {
                    'avg_sharpe': advanced['walk_forward']['avg_sharpe'],
                    'consistency': advanced['walk_forward']['consistency'],
                    'total_return': advanced['walk_forward']['total_return']
                },
                'monte_carlo': {
                    'expected_return': advanced['monte_carlo']['returns']['mean'],
                    'ci_95': [
                        advanced['monte_carlo']['returns']['ci_lower'],
                        advanced['monte_carlo']['returns']['ci_upper']
                    ],
                    'prob_positive': advanced['monte_carlo']['probability_positive']
                }
            }
        }

        return comparison

    def generate_backtest_report(self, results: List[Dict], output_file: str = None):
        """Generate comprehensive backtest report."""
        if not results:
            print("⚠️  No results to report")
            return None

        # Create report DataFrame
        report_data = []

        for r in results:
            simple = r['simple']
            wf = r['walk_forward']
            mc = r['monte_carlo']

            report_data.append({
                'Symbol': r['symbol'],
                'Model': r['model'],
                'Sharpe': simple['sharpe_ratio'],
                'Total Return': simple['total_return'] * 100,
                'Annual Return': simple['annual_return'] * 100,
                'Max DD': simple['max_drawdown'] * 100,
                'Win Rate': simple['win_rate'] * 100,
                'Profit Factor': simple['profit_factor'],
                'WF Sharpe': wf['avg_sharpe'],
                'WF Consistency': wf['consistency'] * 100,
                'MC Expected Return': mc['returns']['mean'] * 100,
                'MC P(Positive)': mc['probability_positive'] * 100
            })

        df = pd.DataFrame(report_data)

        # Display summary
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE BACKTEST REPORT")
        print("="*80)
        print(f"\nTotal Models Tested: {len(results)}")
        print("\nTop 5 by Sharpe Ratio:")
        print(df.nlargest(5, 'Sharpe')[['Symbol', 'Model', 'Sharpe', 'Total Return', 'Max DD']])

        print("\nTop 5 by Walk-Forward Consistency:")
        print(df.nlargest(5, 'WF Consistency')[['Symbol', 'Model', 'WF Sharpe', 'WF Consistency']])

        print("\nTop 5 by Monte Carlo Expected Return:")
        print(df.nlargest(5, 'MC Expected Return')[['Symbol', 'Model', 'MC Expected Return', 'MC P(Positive)']])

        # Save to CSV if requested
        if output_file:
            output_path = Path(output_file)
            df.to_csv(output_path, index=False)
            print(f"\n✅ Report saved to: {output_path}")

        return df

    def visualize_backtest_results(self,
                                   symbol: str,
                                   model: str,
                                   output_dir: str = "poc/backtest_results"):
        """Create visualization of backtest results."""
        result = self.run_comprehensive_backtest(symbol, model)

        if not result:
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{symbol} - {model}: Advanced Backtest Results',
                    fontsize=16, fontweight='bold')

        # 1. Equity Curve
        ax1 = axes[0, 0]
        equity = result['simple']['equity_curve']
        ax1.plot(equity, linewidth=2, color='#00d9ff')
        ax1.fill_between(range(len(equity)), equity, alpha=0.3, color='#00d9ff')
        ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Days')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=self.config.initial_capital, color='red', linestyle='--', alpha=0.5)

        # 2. Drawdown
        ax2 = axes[0, 1]
        drawdown = np.array(result['simple']['drawdown_curve']) * 100
        ax2.fill_between(range(len(drawdown)), drawdown, alpha=0.5, color='#ff3366')
        ax2.plot(drawdown, linewidth=2, color='#ff3366')
        ax2.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Days')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)

        # 3. Walk-Forward Performance
        ax3 = axes[1, 0]
        wf_periods = result['walk_forward']['periods']
        wf_sharpes = [p['sharpe_ratio'] for p in wf_periods]
        x_labels = [f"P{i+1}" for i in range(len(wf_sharpes))]
        ax3.bar(x_labels, wf_sharpes, color='#00ff88', alpha=0.7)
        ax3.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Sharpe=1.0')
        ax3.set_title('Walk-Forward Sharpe by Period', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Period')
        ax3.set_ylabel('Sharpe Ratio')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Monte Carlo Distribution
        ax4 = axes[1, 1]
        mc_returns = [s['total_return'] * 100 for s in result['monte_carlo']['all_simulations']]
        ax4.hist(mc_returns, bins=50, color='#ffaa00', alpha=0.7, edgecolor='black')
        ax4.axvline(x=np.mean(mc_returns), color='red', linestyle='--',
                   linewidth=2, label=f'Mean: {np.mean(mc_returns):.1f}%')
        ax4.set_title('Monte Carlo Returns Distribution', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Total Return (%)')
        ax4.set_ylabel('Frequency')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        filename = f"{symbol}_{model}_backtest.png"
        filepath = output_path / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Visualization saved: {filepath}")

        return filepath


def main():
    """Example usage."""
    print("\n" + "="*60)
    print("🚀 CRISPR Advanced Backtest Integration")
    print("="*60)

    integration = CRISPRBacktestIntegration()

    # Example 1: Single model comprehensive backtest
    print("\n📊 Example 1: Comprehensive Backtest")
    result = integration.run_comprehensive_backtest("AAPL", "naive_momentum")

    if result:
        print("\n✅ Results Summary:")
        print(f"   Sharpe Ratio: {result['simple']['sharpe_ratio']:.2f}")
        print(f"   Total Return: {result['simple']['total_return']*100:.2f}%")
        print(f"   WF Consistency: {result['walk_forward']['consistency']*100:.1f}%")
        print(f"   MC P(Positive): {result['monte_carlo']['probability_positive']*100:.1f}%")

    # Example 2: Generate visualization
    print("\n📊 Example 2: Generate Visualization")
    integration.visualize_backtest_results("AAPL", "naive_momentum")

    print("\n" + "="*60)
    print("✅ Integration demo completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
