"""
Advanced Backtesting Engine for CRISPR-FinAI
Supports walk-forward analysis, Monte Carlo simulation, and parameter optimization.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json
from itertools import product
import warnings
warnings.filterwarnings('ignore')


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    symbol: str
    model_name: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005   # 0.05%
    position_size: float = 1.0  # Fraction of capital per trade

    # Walk-forward settings
    train_period: int = 252  # Trading days
    test_period: int = 63    # Trading days

    # Monte Carlo settings
    n_simulations: int = 1000
    confidence_level: float = 0.95


@dataclass
class BacktestResult:
    """Results from a single backtest run."""
    config: BacktestConfig

    # Performance metrics
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

    # Time series
    equity_curve: List[float]
    drawdown_curve: List[float]
    trade_log: List[Dict]

    # Execution details
    execution_time: float
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        result['config'] = asdict(self.config)
        return result


@dataclass
class WalkForwardResult:
    """Results from walk-forward analysis."""
    in_sample_results: List[BacktestResult]
    out_of_sample_results: List[BacktestResult]

    # Aggregate metrics
    avg_in_sample_sharpe: float
    avg_out_of_sample_sharpe: float
    degradation: float  # Performance degradation OOS
    consistency_score: float

    # Best parameters per window
    optimal_params: List[Dict]


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    base_result: BacktestResult
    simulated_returns: np.ndarray

    # Statistics
    mean_return: float
    median_return: float
    std_return: float
    var_95: float  # 95% Value at Risk
    cvar_95: float  # 95% Conditional VaR

    # Confidence intervals
    ci_lower: float
    ci_upper: float

    # Probability of loss
    prob_loss: float
    max_loss: float
    max_gain: float


class AdvancedBacktester:
    """
    Advanced backtesting engine with walk-forward analysis,
    Monte Carlo simulation, and parameter optimization.
    """

    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.results_cache: Dict[str, BacktestResult] = {}

    def load_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Load price data for symbol."""
        # In production, load from database or CSV
        # For now, generate synthetic data

        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # Generate realistic price data
        np.random.seed(hash(symbol) % 2**32)
        returns = np.random.normal(0.0005, 0.02, len(dates))

        prices = 100 * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
            'high': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
            'low': prices * (1 - np.random.uniform(0, 0.02, len(dates))),
            'close': prices,
            'volume': np.random.randint(1e6, 10e6, len(dates))
        })

        return df

    def calculate_signals(self, df: pd.DataFrame, model_name: str,
                         params: Optional[Dict] = None) -> pd.Series:
        """
        Generate trading signals based on model.
        
        Returns:
            Series of signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if params is None:
            params = {}

        if model_name == "momentum":
            # Simple momentum strategy
            lookback = params.get('lookback', 20)
            df['momentum'] = df['close'].pct_change(lookback)
            signals = pd.Series(0, index=df.index)
            signals[df['momentum'] > 0] = 1
            signals[df['momentum'] < 0] = -1

        elif model_name == "mean_reversion":
            # Mean reversion strategy
            window = params.get('window', 20)
            std_mult = params.get('std_mult', 2.0)

            df['sma'] = df['close'].rolling(window).mean()
            df['std'] = df['close'].rolling(window).std()
            df['upper'] = df['sma'] + std_mult * df['std']
            df['lower'] = df['sma'] - std_mult * df['std']

            signals = pd.Series(0, index=df.index)
            signals[df['close'] < df['lower']] = 1   # Buy oversold
            signals[df['close'] > df['upper']] = -1  # Sell overbought

        elif model_name == "trend_following":
            # Trend following with dual moving averages
            fast = params.get('fast', 10)
            slow = params.get('slow', 50)

            df['fast_ma'] = df['close'].rolling(fast).mean()
            df['slow_ma'] = df['close'].rolling(slow).mean()

            signals = pd.Series(0, index=df.index)
            signals[df['fast_ma'] > df['slow_ma']] = 1
            signals[df['fast_ma'] < df['slow_ma']] = -1

        else:
            raise ValueError(f"Unknown model: {model_name}")

        return signals

    def simulate_trades(self, df: pd.DataFrame, signals: pd.Series,
                       config: BacktestConfig) -> Tuple[List[float], List[Dict]]:
        """
        Simulate trading based on signals.
        
        Returns:
            Tuple of (equity_curve, trade_log)
        """
        capital = config.initial_capital
        position = 0  # Current position: 0 (cash), 1 (long), -1 (short)
        equity_curve = [capital]
        trade_log = []

        for i in range(1, len(df)):
            signal = signals.iloc[i]
            price = df['close'].iloc[i]

            # Entry logic
            if signal != 0 and position == 0:
                # Enter position
                position = signal
                shares = (capital * config.position_size) / price
                entry_price = price * (1 + config.slippage * signal)
                commission_cost = capital * config.position_size * config.commission

                trade_log.append({
                    'date': df['date'].iloc[i],
                    'action': 'BUY' if signal == 1 else 'SELL',
                    'price': entry_price,
                    'shares': shares,
                    'commission': commission_cost,
                    'position': position
                })

                capital -= commission_cost

            # Exit logic
            elif signal == -position and position != 0:
                # Exit position
                exit_price = price * (1 - config.slippage * position)
                pnl = shares * (exit_price - entry_price) * position
                commission_cost = abs(shares * exit_price) * config.commission

                capital += pnl - commission_cost

                trade_log.append({
                    'date': df['date'].iloc[i],
                    'action': 'EXIT',
                    'price': exit_price,
                    'shares': shares,
                    'pnl': pnl,
                    'commission': commission_cost,
                    'position': 0
                })

                position = 0
                shares = 0

            # Update equity
            if position != 0:
                # Mark to market
                current_value = shares * price * position + capital
                equity_curve.append(current_value)
            else:
                equity_curve.append(capital)

        return equity_curve, trade_log

    def calculate_metrics(self, equity_curve: List[float],
                         trade_log: List[Dict],
                         initial_capital: float) -> Dict:
        """Calculate performance metrics from equity curve."""
        equity = np.array(equity_curve)
        returns = np.diff(equity) / equity[:-1]

        # Total and annualized returns
        total_return = (equity[-1] - initial_capital) / initial_capital
        n_days = len(equity)
        annual_return = (1 + total_return) ** (252 / n_days) - 1

        # Risk metrics
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        # Downside deviation for Sortino
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 1e-6
        sortino_ratio = annual_return / downside_std

        # Maximum drawdown
        cummax = np.maximum.accumulate(equity)
        drawdown = (equity - cummax) / cummax
        max_drawdown = np.min(drawdown)

        # Calmar ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Trade statistics
        winning_trades = [t for t in trade_log if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trade_log if t.get('pnl', 0) < 0]

        total_trades = len([t for t in trade_log if 'pnl' in t])
        n_wins = len(winning_trades)
        n_loss = len(losing_trades)

        win_rate = n_wins / total_trades if total_trades > 0 else 0

        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 1e-6

        profit_factor = abs(avg_win * n_wins / (avg_loss * n_loss)) if n_loss > 0 and avg_loss > 0 else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'winning_trades': n_wins,
            'losing_trades': n_loss,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'drawdown_curve': drawdown.tolist()
        }

    def run_backtest(self, config: BacktestConfig,
                    params: Optional[Dict] = None) -> BacktestResult:
        """Run a single backtest."""
        start_time = datetime.now()

        # Load data
        df = self.load_data(config.symbol, config.start_date, config.end_date)

        # Generate signals
        signals = self.calculate_signals(df, config.model_name, params)

        # Simulate trades
        equity_curve, trade_log = self.simulate_trades(df, signals, config)

        # Calculate metrics
        metrics = self.calculate_metrics(equity_curve, trade_log, config.initial_capital)

        execution_time = (datetime.now() - start_time).total_seconds()

        result = BacktestResult(
            config=config,
            equity_curve=equity_curve,
            trade_log=trade_log,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
            **metrics
        )

        return result

    def walk_forward_analysis(self, config: BacktestConfig,
                             param_grid: Dict[str, List],
                             n_splits: int = 5) -> WalkForwardResult:
        """
        Perform walk-forward analysis.
        
        Args:
            config: Base backtest configuration
            param_grid: Parameter grid for optimization
            n_splits: Number of train/test splits
        """
        print("\n🔄 Running walk-forward analysis...")
        print(f"   Symbol: {config.symbol}")
        print(f"   Model: {config.model_name}")
        print(f"   Splits: {n_splits}")

        # Load full dataset
        df = self.load_data(config.symbol, config.start_date, config.end_date)

        total_days = len(df)
        window_size = total_days // n_splits

        in_sample_results = []
        out_of_sample_results = []
        optimal_params_list = []

        for i in range(n_splits):
            print(f"\n   Split {i+1}/{n_splits}:")

            # Define train/test periods
            train_start = i * window_size
            train_end = train_start + int(window_size * 0.7)
            test_start = train_end
            test_end = min(test_start + int(window_size * 0.3), total_days)

            train_df = df.iloc[train_start:train_end]
            test_df = df.iloc[test_start:test_end]

            print(f"      Train: {len(train_df)} days")
            print(f"      Test:  {len(test_df)} days")

            # Optimize parameters on training set
            best_sharpe = -np.inf
            best_params = None
            best_result = None

            # Generate parameter combinations
            param_combinations = [dict(zip(param_grid.keys(), v))
                                for v in product(*param_grid.values())]

            print(f"      Testing {len(param_combinations)} parameter combinations...")

            for params in param_combinations:
                # Test on training set
                signals = self.calculate_signals(train_df, config.model_name, params)
                equity_curve, trade_log = self.simulate_trades(train_df, signals, config)
                metrics = self.calculate_metrics(equity_curve, trade_log, config.initial_capital)

                if metrics['sharpe_ratio'] > best_sharpe:
                    best_sharpe = metrics['sharpe_ratio']
                    best_params = params
                    best_result = metrics

            print(f"      ✓ Best in-sample Sharpe: {best_sharpe:.3f}")
            print(f"      ✓ Optimal params: {best_params}")

            # Store in-sample result
            in_sample_results.append(BacktestResult(
                config=config,
                equity_curve=equity_curve,
                trade_log=trade_log,
                execution_time=0,
                timestamp=datetime.now().isoformat(),
                **best_result
            ))

            optimal_params_list.append(best_params)

            # Test on out-of-sample data
            signals = self.calculate_signals(test_df, config.model_name, best_params)
            equity_curve, trade_log = self.simulate_trades(test_df, signals, config)
            metrics = self.calculate_metrics(equity_curve, trade_log, config.initial_capital)

            print(f"      ✓ Out-of-sample Sharpe: {metrics['sharpe_ratio']:.3f}")

            out_of_sample_results.append(BacktestResult(
                config=config,
                equity_curve=equity_curve,
                trade_log=trade_log,
                execution_time=0,
                timestamp=datetime.now().isoformat(),
                **metrics
            ))

        # Calculate aggregate metrics
        avg_is_sharpe = np.mean([r.sharpe_ratio for r in in_sample_results])
        avg_oos_sharpe = np.mean([r.sharpe_ratio for r in out_of_sample_results])
        degradation = (avg_is_sharpe - avg_oos_sharpe) / avg_is_sharpe if avg_is_sharpe > 0 else 0

        # Consistency score (lower variance is better)
        oos_sharpes = [r.sharpe_ratio for r in out_of_sample_results]
        consistency_score = 1 / (1 + np.std(oos_sharpes))

        print("\n✅ Walk-forward analysis complete!")
        print(f"   Avg in-sample Sharpe:     {avg_is_sharpe:.3f}")
        print(f"   Avg out-of-sample Sharpe: {avg_oos_sharpe:.3f}")
        print(f"   Degradation:              {degradation*100:.1f}%")
        print(f"   Consistency score:        {consistency_score:.3f}")

        return WalkForwardResult(
            in_sample_results=in_sample_results,
            out_of_sample_results=out_of_sample_results,
            avg_in_sample_sharpe=avg_is_sharpe,
            avg_out_of_sample_sharpe=avg_oos_sharpe,
            degradation=degradation,
            consistency_score=consistency_score,
            optimal_params=optimal_params_list
        )

    def monte_carlo_simulation(self, base_result: BacktestResult,
                               config: BacktestConfig) -> MonteCarloResult:
        """
        Run Monte Carlo simulation on backtest results.
        
        Randomly shuffles trade returns to assess robustness.
        """
        print("\n🎲 Running Monte Carlo simulation...")
        print(f"   Simulations: {config.n_simulations}")

        # Extract trade returns
        trades_with_pnl = [t for t in base_result.trade_log if 'pnl' in t]
        trade_returns = np.array([t['pnl'] / config.initial_capital
                                 for t in trades_with_pnl])

        if len(trade_returns) == 0:
            print("   ⚠️  No trades found, using equity curve returns")
            equity = np.array(base_result.equity_curve)
            trade_returns = np.diff(equity) / equity[:-1]

        # Run simulations
        simulated_returns = []

        for i in range(config.n_simulations):
            # Randomly shuffle returns
            shuffled = np.random.choice(trade_returns, size=len(trade_returns), replace=True)
            total_return = np.prod(1 + shuffled) - 1
            simulated_returns.append(total_return)

        simulated_returns = np.array(simulated_returns)

        # Calculate statistics
        mean_return = np.mean(simulated_returns)
        median_return = np.median(simulated_returns)
        std_return = np.std(simulated_returns)

        # Value at Risk (95%)
        var_95 = np.percentile(simulated_returns, 5)

        # Conditional VaR (average of worst 5%)
        worst_5pct = simulated_returns[simulated_returns <= var_95]
        cvar_95 = np.mean(worst_5pct)

        # Confidence intervals
        ci_lower = np.percentile(simulated_returns, (1 - config.confidence_level) * 100 / 2)
        ci_upper = np.percentile(simulated_returns, (1 + config.confidence_level) * 100 / 2)

        # Probability of loss
        prob_loss = np.sum(simulated_returns < 0) / len(simulated_returns)

        max_loss = np.min(simulated_returns)
        max_gain = np.max(simulated_returns)

        print(f"   ✓ Mean return:      {mean_return*100:.2f}%")
        print(f"   ✓ Median return:    {median_return*100:.2f}%")
        print(f"   ✓ VaR (95%):        {var_95*100:.2f}%")
        print(f"   ✓ CVaR (95%):       {cvar_95*100:.2f}%")
        print(f"   ✓ Probability loss: {prob_loss*100:.1f}%")

        return MonteCarloResult(
            base_result=base_result,
            simulated_returns=simulated_returns,
            mean_return=mean_return,
            median_return=median_return,
            std_return=std_return,
            var_95=var_95,
            cvar_95=cvar_95,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            prob_loss=prob_loss,
            max_loss=max_loss,
            max_gain=max_gain
        )

    def save_results(self, results: Dict, output_path: str) -> None:
        """Save backtest results to JSON."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {output_file}")


def main():
    """Example usage of advanced backtesting engine."""
    print("\n" + "="*70)
    print("🚀 Advanced Backtesting Engine - Demo")
    print("="*70)

    # Initialize backtester
    backtester = AdvancedBacktester()

    # Configure backtest
    config = BacktestConfig(
        symbol="AAPL",
        model_name="momentum",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000.0,
        commission=0.001,
        slippage=0.0005
    )

    # 1. Simple backtest
    print("\n" + "="*70)
    print("1️⃣  SIMPLE BACKTEST")
    print("="*70)

    result = backtester.run_backtest(config)

    print("\n📊 Results:")
    print(f"   Total Return:    {result.total_return*100:.2f}%")
    print(f"   Annual Return:   {result.annual_return*100:.2f}%")
    print(f"   Sharpe Ratio:    {result.sharpe_ratio:.3f}")
    print(f"   Max Drawdown:    {result.max_drawdown*100:.2f}%")
    print(f"   Total Trades:    {result.total_trades}")
    print(f"   Win Rate:        {result.win_rate*100:.1f}%")
    print(f"   Profit Factor:   {result.profit_factor:.2f}")

    # 2. Walk-forward analysis
    print("\n" + "="*70)
    print("2️⃣  WALK-FORWARD ANALYSIS")
    print("="*70)

    param_grid = {
        'lookback': [10, 20, 30]
    }

    wf_result = backtester.walk_forward_analysis(config, param_grid, n_splits=3)

    # 3. Monte Carlo simulation
    print("\n" + "="*70)
    print("3️⃣  MONTE CARLO SIMULATION")
    print("="*70)

    mc_result = backtester.monte_carlo_simulation(result, config)

    print("\n" + "="*70)
    print("✅ Advanced backtesting complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
