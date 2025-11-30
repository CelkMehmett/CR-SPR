"""
Advanced Backtesting Engine for CRISPR-FinAI
Features: Walk-forward analysis, Monte Carlo simulation, parameter optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import warnings
warnings.filterwarnings('ignore')


@dataclass
class BacktestConfig:
    """Backtesting configuration parameters."""
    initial_capital: float = 100000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005   # 0.05%
    position_size: float = 1.0  # Full position
    max_leverage: float = 1.0
    margin_requirement: float = 0.0

    # Walk-forward parameters
    train_window: int = 252  # Trading days
    test_window: int = 63    # ~3 months
    step_size: int = 21      # ~1 month

    # Monte Carlo parameters
    n_simulations: int = 1000
    confidence_level: float = 0.95

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BacktestResult:
    """Comprehensive backtest results."""
    # Basic metrics
    total_return: float
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float

    # Risk metrics
    volatility: float
    downside_deviation: float
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional VaR

    # Time-based metrics
    trades_per_year: float
    avg_trade_duration: float  # days
    max_consecutive_wins: int
    max_consecutive_losses: int

    # Equity curve
    equity_curve: List[float]
    drawdown_curve: List[float]

    # Timestamps
    start_date: str
    end_date: str
    duration_days: int

    def to_dict(self) -> Dict:
        return asdict(self)


class AdvancedBacktester:
    """
    Advanced backtesting engine with sophisticated analysis capabilities.
    """

    def __init__(self, config: BacktestConfig = BacktestConfig()):
        self.config = config
        self.results_cache = {}

    def run_simple_backtest(self,
                           returns: np.ndarray,
                           signals: np.ndarray,
                           dates: Optional[pd.DatetimeIndex] = None) -> BacktestResult:
        """
        Run simple backtest on returns and signals.
        
        Args:
            returns: Array of asset returns
            signals: Trading signals (1=long, 0=neutral, -1=short)
            dates: Date index for results
        
        Returns:
            BacktestResult object with comprehensive metrics
        """
        if len(returns) != len(signals):
            raise ValueError("Returns and signals must have same length")

        if dates is None:
            dates = pd.date_range(end=datetime.now(), periods=len(returns), freq='D')

        # Apply transaction costs
        position_changes = np.diff(signals, prepend=0)
        transaction_costs = np.abs(position_changes) * (self.config.commission + self.config.slippage)

        # Calculate strategy returns
        strategy_returns = signals * returns - transaction_costs

        # Equity curve
        equity_curve = np.cumprod(1 + strategy_returns)
        equity = self.config.initial_capital * equity_curve

        # Drawdown calculation
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        max_drawdown = np.min(drawdown)

        # Trade analysis
        trades = self._analyze_trades(signals, returns, dates)

        # Calculate metrics
        total_return = (equity[-1] / self.config.initial_capital - 1)
        n_years = len(returns) / 252
        annual_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

        # Risk metrics
        volatility = np.std(strategy_returns) * np.sqrt(252)
        sharpe_ratio = (np.mean(strategy_returns) * 252) / (volatility + 1e-10)

        # Downside deviation (for Sortino)
        negative_returns = strategy_returns[strategy_returns < 0]
        downside_deviation = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = (np.mean(strategy_returns) * 252) / (downside_deviation + 1e-10)

        # Calmar ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Value at Risk (VaR) and Conditional VaR (CVaR)
        var_95 = np.percentile(strategy_returns, 5)
        cvar_95 = np.mean(strategy_returns[strategy_returns <= var_95])

        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            total_trades=trades['total'],
            winning_trades=trades['winning'],
            losing_trades=trades['losing'],
            win_rate=trades['win_rate'],
            profit_factor=trades['profit_factor'],
            avg_win=trades['avg_win'],
            avg_loss=trades['avg_loss'],
            volatility=volatility,
            downside_deviation=downside_deviation,
            var_95=var_95,
            cvar_95=cvar_95,
            trades_per_year=trades['total'] / n_years if n_years > 0 else 0,
            avg_trade_duration=trades['avg_duration'],
            max_consecutive_wins=trades['max_consecutive_wins'],
            max_consecutive_losses=trades['max_consecutive_losses'],
            equity_curve=equity.tolist(),
            drawdown_curve=drawdown.tolist(),
            start_date=dates.iloc[0].strftime('%Y-%m-%d') if hasattr(dates, 'iloc') else dates[0].strftime('%Y-%m-%d'),
            end_date=dates.iloc[-1].strftime('%Y-%m-%d') if hasattr(dates, 'iloc') else dates[-1].strftime('%Y-%m-%d'),
            duration_days=len(returns)
        )

    def _analyze_trades(self, signals: np.ndarray,
                       returns: np.ndarray,
                       dates: pd.DatetimeIndex) -> Dict:
        """Analyze individual trades."""
        position_changes = np.diff(signals, prepend=0)
        trade_entries = np.where(position_changes != 0)[0]

        # Convert dates to numpy array for easier indexing
        if hasattr(dates, 'values'):
            dates_array = dates.values
        else:
            dates_array = np.array(dates)

        trades = []
        for i in range(len(trade_entries) - 1):
            entry_idx = trade_entries[i]
            exit_idx = trade_entries[i + 1]

            # Calculate trade return
            position = signals[entry_idx]
            trade_returns = position * returns[entry_idx:exit_idx]
            trade_pnl = np.sum(trade_returns)

            trades.append({
                'entry_date': pd.Timestamp(dates_array[entry_idx]),
                'exit_date': pd.Timestamp(dates_array[exit_idx]),
                'duration': exit_idx - entry_idx,
                'position': position,
                'pnl': trade_pnl
            })

        if not trades:
            return {
                'total': 0,
                'winning': 0,
                'losing': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_duration': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }

        # Calculate statistics
        pnls = [t['pnl'] for t in trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]

        total_profit = sum(winning_trades) if winning_trades else 0
        total_loss = abs(sum(losing_trades)) if losing_trades else 0

        # Consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_streak = 0
        current_type = None

        for pnl in pnls:
            if pnl > 0:
                if current_type == 'win':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_type = 'win'
                max_consecutive_wins = max(max_consecutive_wins, current_streak)
            else:
                if current_type == 'loss':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_type = 'loss'
                max_consecutive_losses = max(max_consecutive_losses, current_streak)

        return {
            'total': len(trades),
            'winning': len(winning_trades),
            'losing': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) if trades else 0,
            'profit_factor': total_profit / total_loss if total_loss > 0 else 0,
            'avg_win': np.mean(winning_trades) if winning_trades else 0,
            'avg_loss': np.mean(losing_trades) if losing_trades else 0,
            'avg_duration': np.mean([t['duration'] for t in trades]),
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses
        }

    def walk_forward_analysis(self,
                             returns: np.ndarray,
                             signal_generator: Callable,
                             dates: Optional[pd.DatetimeIndex] = None) -> Dict:
        """
        Perform walk-forward analysis.
        
        Args:
            returns: Asset returns
            signal_generator: Function that generates signals from returns
                             Should accept returns array and return signals array
            dates: Date index
        
        Returns:
            Dictionary with walk-forward results
        """
        if dates is None:
            dates = pd.date_range(end=datetime.now(), periods=len(returns), freq='D')

        train_window = self.config.train_window
        test_window = self.config.test_window
        step_size = self.config.step_size

        results = []
        equity_curve = []
        current_equity = self.config.initial_capital

        # Walk-forward loop
        start_idx = 0
        while start_idx + train_window + test_window <= len(returns):
            # Split data
            train_end = start_idx + train_window
            test_end = train_end + test_window

            train_returns = returns[start_idx:train_end]
            test_returns = returns[train_end:test_end]
            test_dates = dates[train_end:test_end]

            # Generate signals on training data (optimization happens here)
            # In production, you'd optimize parameters here
            signals = signal_generator(train_returns)

            # Apply same strategy to test data
            test_signals = signal_generator(test_returns)

            # Backtest on test period
            test_result = self.run_simple_backtest(test_returns, test_signals, test_dates)

            results.append({
                'train_start': dates[start_idx].strftime('%Y-%m-%d'),
                'train_end': dates[train_end - 1].strftime('%Y-%m-%d'),
                'test_start': dates[train_end].strftime('%Y-%m-%d'),
                'test_end': dates[test_end - 1].strftime('%Y-%m-%d'),
                'sharpe_ratio': test_result.sharpe_ratio,
                'total_return': test_result.total_return,
                'max_drawdown': test_result.max_drawdown,
                'win_rate': test_result.win_rate
            })

            # Update equity curve
            period_return = test_result.total_return
            current_equity *= (1 + period_return)
            equity_curve.extend([current_equity] * test_window)

            # Move forward
            start_idx += step_size

        # Calculate overall metrics
        sharpe_ratios = [r['sharpe_ratio'] for r in results]
        total_returns = [r['total_return'] for r in results]

        return {
            'periods': results,
            'n_periods': len(results),
            'avg_sharpe': np.mean(sharpe_ratios),
            'std_sharpe': np.std(sharpe_ratios),
            'avg_return': np.mean(total_returns),
            'total_return': (current_equity / self.config.initial_capital - 1),
            'consistency': len([s for s in sharpe_ratios if s > 0]) / len(sharpe_ratios),
            'equity_curve': equity_curve
        }

    def monte_carlo_simulation(self,
                              returns: np.ndarray,
                              signals: np.ndarray) -> Dict:
        """
        Run Monte Carlo simulation by bootstrapping returns.
        
        Args:
            returns: Historical returns
            signals: Trading signals
        
        Returns:
            Dictionary with Monte Carlo results
        """
        n_sims = self.config.n_simulations
        n_periods = len(returns)

        simulation_results = []

        for _ in range(n_sims):
            # Bootstrap returns (sample with replacement)
            sim_indices = np.random.choice(n_periods, size=n_periods, replace=True)
            sim_returns = returns[sim_indices]
            sim_signals = signals[sim_indices]

            # Run backtest
            result = self.run_simple_backtest(sim_returns, sim_signals)

            simulation_results.append({
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate
            })

        # Calculate statistics
        returns_dist = [r['total_return'] for r in simulation_results]
        sharpe_dist = [r['sharpe_ratio'] for r in simulation_results]
        dd_dist = [r['max_drawdown'] for r in simulation_results]

        conf_level = self.config.confidence_level
        lower_pct = (1 - conf_level) / 2 * 100
        upper_pct = (1 - (1 - conf_level) / 2) * 100

        return {
            'n_simulations': n_sims,
            'confidence_level': conf_level,
            'returns': {
                'mean': np.mean(returns_dist),
                'median': np.median(returns_dist),
                'std': np.std(returns_dist),
                'min': np.min(returns_dist),
                'max': np.max(returns_dist),
                'ci_lower': np.percentile(returns_dist, lower_pct),
                'ci_upper': np.percentile(returns_dist, upper_pct)
            },
            'sharpe': {
                'mean': np.mean(sharpe_dist),
                'median': np.median(sharpe_dist),
                'std': np.std(sharpe_dist),
                'min': np.min(sharpe_dist),
                'max': np.max(sharpe_dist),
                'ci_lower': np.percentile(sharpe_dist, lower_pct),
                'ci_upper': np.percentile(sharpe_dist, upper_pct)
            },
            'max_drawdown': {
                'mean': np.mean(dd_dist),
                'median': np.median(dd_dist),
                'std': np.std(dd_dist),
                'min': np.min(dd_dist),
                'max': np.max(dd_dist),
                'ci_lower': np.percentile(dd_dist, lower_pct),
                'ci_upper': np.percentile(dd_dist, upper_pct)
            },
            'probability_positive': len([r for r in returns_dist if r > 0]) / n_sims,
            'probability_sharpe_above_1': len([s for s in sharpe_dist if s > 1.0]) / n_sims,
            'all_simulations': simulation_results
        }

    def parameter_optimization(self,
                              returns: np.ndarray,
                              parameter_grid: Dict[str, List],
                              signal_generator: Callable,
                              optimize_metric: str = 'sharpe_ratio',
                              n_jobs: int = -1) -> Dict:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            returns: Asset returns
            parameter_grid: Dictionary of parameter names and values to test
            signal_generator: Function that generates signals given returns and parameters
            optimize_metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)
            n_jobs: Number of parallel jobs (-1 for all cores)
        
        Returns:
            Dictionary with optimization results
        """
        # Generate all parameter combinations
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        param_combinations = list(product(*param_values))

        print(f"🔍 Testing {len(param_combinations)} parameter combinations...")

        results = []

        # Parallel parameter testing
        with ProcessPoolExecutor(max_workers=n_jobs if n_jobs > 0 else None) as executor:
            futures = {}

            for params in param_combinations:
                param_dict = dict(zip(param_names, params))
                future = executor.submit(
                    self._test_parameters,
                    returns,
                    signal_generator,
                    param_dict
                )
                futures[future] = param_dict

            # Collect results
            for future in as_completed(futures):
                param_dict = futures[future]
                try:
                    result = future.result()
                    result['parameters'] = param_dict
                    results.append(result)
                except Exception as e:
                    print(f"❌ Error testing {param_dict}: {e}")

        # Sort by optimization metric
        results.sort(key=lambda x: x.get(optimize_metric, -np.inf), reverse=True)

        best_result = results[0] if results else None

        return {
            'n_combinations': len(param_combinations),
            'optimize_metric': optimize_metric,
            'best_parameters': best_result['parameters'] if best_result else None,
            'best_result': best_result,
            'all_results': results,
            'parameter_sensitivity': self._analyze_parameter_sensitivity(results, param_names)
        }

    def _test_parameters(self,
                        returns: np.ndarray,
                        signal_generator: Callable,
                        parameters: Dict) -> Dict:
        """Test a single parameter combination."""
        try:
            signals = signal_generator(returns, **parameters)
            result = self.run_simple_backtest(returns, signals)
            return result.to_dict()
        except Exception as e:
            return {'error': str(e)}

    def _analyze_parameter_sensitivity(self,
                                      results: List[Dict],
                                      param_names: List[str]) -> Dict:
        """Analyze how sensitive results are to each parameter."""
        sensitivity = {}

        for param_name in param_names:
            param_values = [r['parameters'][param_name] for r in results if 'parameters' in r]
            sharpe_values = [r.get('sharpe_ratio', 0) for r in results]

            # Calculate correlation between parameter and Sharpe
            if len(set(param_values)) > 1:
                correlation = np.corrcoef(param_values, sharpe_values)[0, 1]
            else:
                correlation = 0

            sensitivity[param_name] = {
                'correlation_with_sharpe': correlation,
                'unique_values': len(set(param_values)),
                'value_range': (min(param_values), max(param_values))
            }

        return sensitivity


def example_signal_generator(returns: np.ndarray, **kwargs) -> np.ndarray:
    """
    Example signal generator - Simple momentum strategy.
    
    Args:
        returns: Asset returns
        **kwargs: Strategy parameters (e.g., lookback_period)
    
    Returns:
        Signals array (1=long, 0=neutral, -1=short)
    """
    lookback = kwargs.get('lookback_period', 20)

    # Calculate rolling momentum
    momentum = pd.Series(returns).rolling(lookback).mean()

    # Generate signals
    signals = np.zeros(len(returns))
    signals[momentum > 0] = 1
    signals[momentum < 0] = -1

    return signals


def main():
    """Example usage of Advanced Backtester."""
    print("\n" + "="*60)
    print("🚀 Advanced Backtesting Engine - Demo")
    print("="*60)

    # Generate synthetic data
    np.random.seed(42)
    n_days = 500
    returns = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

    # Generate signals
    signals = example_signal_generator(returns, lookback_period=20)

    # Initialize backtester
    config = BacktestConfig(
        initial_capital=100000.0,
        commission=0.001,
        slippage=0.0005
    )
    backtester = AdvancedBacktester(config)

    # 1. Simple Backtest
    print("\n1️⃣  Simple Backtest")
    print("-" * 40)
    result = backtester.run_simple_backtest(returns, signals, dates)
    print(f"Total Return:    {result.total_return*100:.2f}%")
    print(f"Annual Return:   {result.annual_return*100:.2f}%")
    print(f"Sharpe Ratio:    {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown:    {result.max_drawdown*100:.2f}%")
    print(f"Win Rate:        {result.win_rate*100:.1f}%")
    print(f"Profit Factor:   {result.profit_factor:.2f}")

    # 2. Walk-Forward Analysis
    print("\n2️⃣  Walk-Forward Analysis")
    print("-" * 40)
    wf_result = backtester.walk_forward_analysis(returns, example_signal_generator, dates)
    print(f"Periods Tested:  {wf_result['n_periods']}")
    print(f"Avg Sharpe:      {wf_result['avg_sharpe']:.2f}")
    print(f"Consistency:     {wf_result['consistency']*100:.1f}%")
    print(f"Total Return:    {wf_result['total_return']*100:.2f}%")

    # 3. Monte Carlo Simulation
    print("\n3️⃣  Monte Carlo Simulation")
    print("-" * 40)
    mc_result = backtester.monte_carlo_simulation(returns, signals)
    print(f"Simulations:     {mc_result['n_simulations']}")
    print(f"Expected Return: {mc_result['returns']['mean']*100:.2f}%")
    print(f"95% CI:          [{mc_result['returns']['ci_lower']*100:.2f}%, "
          f"{mc_result['returns']['ci_upper']*100:.2f}%]")
    print(f"P(Positive):     {mc_result['probability_positive']*100:.1f}%")
    print(f"P(Sharpe>1):     {mc_result['probability_sharpe_above_1']*100:.1f}%")

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
