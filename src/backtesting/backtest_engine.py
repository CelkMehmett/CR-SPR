"""Historical backtesting engine for trading strategies.

This module provides:
1. Strategy backtesting on historical data
2. Performance metrics calculation
3. Equity curve tracking
4. Per-period analysis
5. Multi-period statistics
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Backtest strategies on historical data."""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.results = {}

    def backtest_strategy(
        self,
        strategy,
        price: pd.Series,
        volume: Optional[pd.Series] = None,
        slippage: float = 0.0005,
        commission: float = 0.001,
    ) -> Dict[str, any]:
        """Run backtest for a single strategy.

        Args:
            strategy: Strategy object with generate_signals() method
            price: Price series
            volume: Volume series (optional)
            slippage: Slippage as % of trade value
            commission: Commission as % of trade value

        Returns:
            Dict with backtest results
        """
        # Generate signals
        signals, confidence = strategy.generate_signals(price, volume)

        # Calculate returns
        returns = price.pct_change()

        # Position: +1 (long), -1 (short), 0 (flat)
        positions = signals.shift(1).fillna(0)

        # Strategy returns (apply slippage and commission)
        trades = (signals != signals.shift()).astype(float)
        costs = trades * (slippage + commission)

        strategy_returns = (returns * positions) - costs

        # Equity curve
        equity = self.initial_capital * (1 + strategy_returns).cumprod()

        # Metrics
        metrics = self._calculate_metrics(
            price, signals, strategy_returns, equity, returns
        )

        return {
            "equity_curve": equity,
            "signals": signals,
            "confidence": confidence,
            "returns": strategy_returns,
            "positions": positions,
            "metrics": metrics,
            "trades": trades.sum(),
        }

    def _calculate_metrics(
        self,
        price: pd.Series,
        signals: pd.Series,
        strategy_returns: pd.Series,
        equity: pd.Series,
        benchmark_returns: pd.Series,
    ) -> Dict[str, float]:
        """Calculate comprehensive backtest metrics."""
        # Total return
        total_return = (equity.iloc[-1] - self.initial_capital) / self.initial_capital

        # Annualized return (assuming 252 trading days)
        n_years = len(equity) / 252
        annual_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

        # Sharpe ratio (risk-adjusted return)
        sharpe = (
            strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
            if strategy_returns.std() > 0
            else 0
        )

        # Sortino ratio (only downside volatility)
        downside = strategy_returns[strategy_returns < 0]
        sortino = (
            strategy_returns.mean() / downside.std() * np.sqrt(252)
            if len(downside) > 0
            else 0
        )

        # Maximum drawdown
        cumsum = (1 + strategy_returns).cumprod()
        running_max = cumsum.expanding().max()
        drawdown = (cumsum - running_max) / running_max
        max_dd = drawdown.min()

        # Win rate
        win_rate = (strategy_returns > 0).sum() / len(strategy_returns)

        # Profit factor
        wins = strategy_returns[strategy_returns > 0].sum()
        losses = abs(strategy_returns[strategy_returns < 0].sum())
        profit_factor = wins / losses if losses > 0 else 0

        # Calmar ratio (return / max drawdown)
        calmar = annual_return / abs(max_dd) if max_dd < 0 else 0

        # Number of trades
        trades = (signals != signals.shift()).sum()

        # Avg trade
        avg_trade = strategy_returns.mean()

        # Win/loss ratio
        win_loss_ratio = (
            strategy_returns[strategy_returns > 0].mean()
            / abs(strategy_returns[strategy_returns < 0].mean())
            if len(strategy_returns[strategy_returns < 0]) > 0
            else 0
        )

        # vs Benchmark (buy-and-hold)
        buy_hold_return = (price.iloc[-1] - price.iloc[0]) / price.iloc[0]
        outperformance = total_return - buy_hold_return

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "calmar_ratio": calmar,
            "num_trades": trades,
            "avg_trade": avg_trade,
            "win_loss_ratio": win_loss_ratio,
            "outperformance": outperformance,
            "buy_hold_return": buy_hold_return,
        }

    def backtest_multiple(
        self,
        strategies: Dict[str, any],
        price: pd.Series,
        volume: Optional[pd.Series] = None,
    ) -> Dict[str, Dict]:
        """Backtest multiple strategies.

        Returns:
            Dict mapping strategy_name -> backtest results
        """
        results = {}

        for name, strategy in strategies.items():
            try:
                result = self.backtest_strategy(strategy, price, volume)
                results[name] = result
                logger.info(
                    f"✓ {name}: Sharpe={result['metrics']['sharpe_ratio']:.4f}, "
                    f"Return={result['metrics']['total_return']:.2%}"
                )
            except Exception as e:
                logger.error(f"✗ {name}: {e}")
                continue

        return results

    def compare_strategies(
        self, results: Dict[str, Dict]
    ) -> List[Tuple[str, float]]:
        """Rank strategies by Sharpe ratio.

        Returns:
            List of (strategy_name, sharpe_ratio) sorted descending
        """
        ranked = [
            (name, result["metrics"]["sharpe_ratio"])
            for name, result in results.items()
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def get_equity_curves(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """Extract equity curves for plotting.

        Returns:
            DataFrame with columns per strategy
        """
        curves = {}
        for name, result in results.items():
            curves[name] = result["equity_curve"]

        return pd.DataFrame(curves)

    def get_drawdown_chart(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """Calculate drawdown for each strategy.

        Returns:
            DataFrame with columns per strategy
        """
        drawdowns = {}

        for name, result in results.items():
            equity = result["equity_curve"]
            cumsum = equity / self.initial_capital
            running_max = cumsum.expanding().max()
            dd = (cumsum - running_max) / running_max * 100
            drawdowns[name] = dd

        return pd.DataFrame(drawdowns)

    def get_rolling_sharpe(
        self, results: Dict[str, Dict], window: int = 60
    ) -> pd.DataFrame:
        """Calculate rolling Sharpe ratio.

        Args:
            results: Backtest results
            window: Rolling window size (default 60 days)

        Returns:
            DataFrame with rolling Sharpe per strategy
        """
        rolling_sharpe = {}

        for name, result in results.items():
            returns = result["returns"]
            rolling_std = returns.rolling(window).std()
            rolling_mean = returns.rolling(window).mean()
            rs = (rolling_mean / rolling_std) * np.sqrt(252)
            rolling_sharpe[name] = rs

        return pd.DataFrame(rolling_sharpe)


class PeriodicAnalyzer:
    """Analyze strategy performance by period (daily, monthly, yearly)."""

    @staticmethod
    def analyze_monthly(
        equity: pd.Series,
        returns: pd.Series,
    ) -> pd.DataFrame:
        """Analyze returns by month.

        Returns:
            DataFrame with monthly returns and statistics
        """
        monthly_returns = returns.resample("M").sum()
        monthly_equity = equity.resample("M").last()

        stats = pd.DataFrame(
            {
                "total_return": monthly_returns,
                "equity_eom": monthly_equity,
            }
        )

        return stats

    @staticmethod
    def analyze_yearly(
        equity: pd.Series,
        returns: pd.Series,
    ) -> pd.DataFrame:
        """Analyze returns by year.

        Returns:
            DataFrame with yearly returns and statistics
        """
        yearly_returns = returns.resample("Y").sum()
        yearly_equity = equity.resample("Y").last()

        stats = pd.DataFrame(
            {
                "total_return": yearly_returns,
                "equity_eoy": yearly_equity,
            }
        )

        return stats

    @staticmethod
    def analyze_by_regime(
        returns: pd.Series, price: pd.Series, window: int = 20
    ) -> pd.DataFrame:
        """Analyze returns by market regime (trending vs range-bound).

        Returns:
            DataFrame with regime classification and returns
        """
        # Simple regime detection: trending if price > MA, range-bound otherwise
        ma = price.rolling(window).mean()
        in_trend = price > ma

        regime_returns = pd.DataFrame(
            {
                "in_trend": in_trend,
                "returns": returns,
            }
        )

        return regime_returns
