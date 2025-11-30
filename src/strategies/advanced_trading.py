"""Advanced trading strategies with CRISPR-assisted GA optimization.

This module provides:
1. Advanced trading strategies beyond simple momentum
2. Multi-timeframe analysis
3. Risk management with adaptive position sizing
4. Strategy comparison framework
5. Real-time signal generation with confidence scoring
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdvancedTradingStrategy:
    """Base class for advanced trading strategies."""

    def __init__(self, symbol: str, lookback: int = 252):
        self.symbol = symbol
        self.lookback = lookback
        self.metrics = {}

    def generate_signals(self, price: pd.Series, volume: Optional[pd.Series] = None) -> Tuple[pd.Series, pd.Series]:
        """Generate trading signals and confidence scores.

        Returns:
            signals: 1 (buy), 0 (hold), -1 (sell)
            confidence: 0-1 confidence score for each signal
        """
        raise NotImplementedError

    def calculate_metrics(self, price: pd.Series, signals: pd.Series) -> Dict[str, float]:
        """Calculate strategy performance metrics."""
        returns = price.pct_change()
        strategy_returns = returns * signals.shift(1)
        total_return = (1 + strategy_returns).prod() - 1
        sharpe = strategy_returns.mean() / strategy_returns.std() if strategy_returns.std() > 0 else 0
        max_dd = (strategy_returns.cumsum().max() - strategy_returns.cumsum().min())
        win_rate = (strategy_returns > 0).sum() / len(strategy_returns) if len(strategy_returns) > 0 else 0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'num_trades': (signals != signals.shift()).sum()
        }


class MomentumStrategy(AdvancedTradingStrategy):
    """Classic momentum strategy: price above SMA = buy."""

    def __init__(self, symbol: str, sma_period: int = 20, rsi_period: int = 14):
        super().__init__(symbol)
        self.sma_period = sma_period
        self.rsi_period = rsi_period

    def _calculate_rsi(self, price: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = price.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss if (loss != 0).any() else pd.Series(0, index=price.index)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, price: pd.Series, volume: Optional[pd.Series] = None) -> Tuple[pd.Series, pd.Series]:
        """Generate momentum signals with RSI confirmation."""
        sma = price.rolling(self.sma_period).mean()
        rsi = self._calculate_rsi(price, self.rsi_period)

        # Buy: price > SMA and RSI < 70 (not overbought)
        buy_signal = (price > sma) & (rsi < 70)
        # Sell: price < SMA or RSI > 80 (overbought)
        sell_signal = (price < sma) | (rsi > 80)

        signals = pd.Series(0, index=price.index)
        signals[buy_signal] = 1
        signals[sell_signal] = -1

        # Confidence: RSI distance from extremes
        confidence = pd.Series(1.0, index=price.index)
        confidence[rsi < 30] = 0.9  # Oversold, high confidence
        confidence[(rsi >= 30) & (rsi <= 70)] = 0.6  # Neutral zone
        confidence[rsi > 80] = 0.8  # Overbought

        return signals, confidence


class MeanReversionStrategy(AdvancedTradingStrategy):
    """Mean reversion: buy when price deviates down from band, sell when up."""

    def __init__(self, symbol: str, band_period: int = 20, std_dev: float = 2.0):
        super().__init__(symbol)
        self.band_period = band_period
        self.std_dev = std_dev

    def generate_signals(self, price: pd.Series, volume: Optional[pd.Series] = None) -> Tuple[pd.Series, pd.Series]:
        """Generate mean reversion signals using Bollinger Bands."""
        sma = price.rolling(self.band_period).mean()
        std = price.rolling(self.band_period).std()
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)

        # Buy: price touches or breaks lower band
        buy_signal = price <= lower_band
        # Sell: price touches or breaks upper band
        sell_signal = price >= upper_band

        signals = pd.Series(0, index=price.index)
        signals[buy_signal] = 1
        signals[sell_signal] = -1

        # Confidence: how far from mean
        distance = (price - sma) / std
        confidence = 1.0 - np.abs(distance) / self.std_dev
        confidence = pd.Series(np.clip(confidence, 0.3, 1.0), index=price.index)

        return signals, confidence


class MacdStrategy(AdvancedTradingStrategy):
    """MACD (Moving Average Convergence Divergence) strategy."""

    def __init__(self, symbol: str, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(symbol)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def generate_signals(self, price: pd.Series, volume: Optional[pd.Series] = None) -> Tuple[pd.Series, pd.Series]:
        """Generate MACD signals."""
        ema_fast = price.ewm(span=self.fast_period).mean()
        ema_slow = price.ewm(span=self.slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period).mean()
        histogram = macd_line - signal_line

        # Buy: MACD crosses above signal line
        buy_signal = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        # Sell: MACD crosses below signal line
        sell_signal = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        signals = pd.Series(0, index=price.index)
        signals[buy_signal] = 1
        signals[sell_signal] = -1

        # Confidence: histogram magnitude
        max_hist = np.abs(histogram).rolling(50).max()
        confidence = (np.abs(histogram) / (max_hist + 1e-6)).fillna(0.5)
        confidence = pd.Series(np.clip(confidence, 0.3, 1.0), index=price.index)

        return signals, confidence


class EnsembleStrategy(AdvancedTradingStrategy):
    """Ensemble: combines multiple strategies with weighted voting."""

    def __init__(self, symbol: str, strategies: List[AdvancedTradingStrategy] = None):
        super().__init__(symbol)
        self.strategies = strategies or [
            MomentumStrategy(symbol),
            MeanReversionStrategy(symbol),
            MacdStrategy(symbol)
        ]

    def generate_signals(self, price: pd.Series, volume: Optional[pd.Series] = None) -> Tuple[pd.Series, pd.Series]:
        """Combine signals from multiple strategies."""
        all_signals = []
        all_confidences = []

        for strategy in self.strategies:
            signals, confidence = strategy.generate_signals(price, volume)
            all_signals.append(signals * confidence)  # Weight by confidence
            all_confidences.append(confidence)

        # Ensemble signal: average weighted signals
        ensemble_signal = pd.concat(all_signals, axis=1).mean(axis=1)
        ensemble_confidence = pd.concat(all_confidences, axis=1).mean(axis=1)

        # Discretize to -1, 0, 1
        final_signals = pd.Series(0, index=price.index)
        final_signals[ensemble_signal > 0.3] = 1
        final_signals[ensemble_signal < -0.3] = -1

        return final_signals, ensemble_confidence


class AdaptiveRiskStrategy(AdvancedTradingStrategy):
    """Adaptive position sizing based on volatility and drawdown."""

    def __init__(self, symbol: str, base_strategy: AdvancedTradingStrategy = None, max_loss_pct: float = 0.02):
        super().__init__(symbol)
        self.base_strategy = base_strategy or MomentumStrategy(symbol)
        self.max_loss_pct = max_loss_pct  # Max loss per position: 2%

    def calculate_position_size(self, returns: pd.Series, equity: float = 10000.0) -> pd.Series:
        """Calculate adaptive position size based on volatility."""
        volatility = returns.rolling(20).std()
        # Lower volatility = larger position
        # Higher volatility = smaller position
        # Normalized position size: 0.5 to 2.0x
        vol_normalized = volatility / volatility.rolling(50).mean()
        position_size = 2.0 / (vol_normalized + 1e-6)
        position_size = pd.Series(np.clip(position_size, 0.5, 2.0), index=returns.index)
        return position_size

    def generate_signals(self, price: pd.Series, volume: Optional[pd.Series] = None) -> Tuple[pd.Series, pd.Series]:
        """Generate signals with adaptive position sizing."""
        base_signals, base_confidence = self.base_strategy.generate_signals(price, volume)
        returns = price.pct_change()
        position_size = self.calculate_position_size(returns)

        # Adjust signals by position size
        adjusted_signals = base_signals * position_size
        # Discretize
        final_signals = pd.Series(0, index=price.index)
        final_signals[adjusted_signals > 0.5] = 1
        final_signals[adjusted_signals < -0.5] = -1

        return final_signals, base_confidence


def compare_strategies(price: pd.Series, volume: Optional[pd.Series] = None,
                      symbol: str = 'TEST') -> Dict[str, Dict[str, float]]:
    """Compare multiple trading strategies on the same price series.

    Returns:
        Dict mapping strategy name to performance metrics
    """
    strategies = {
        'Momentum': MomentumStrategy(symbol),
        'MeanReversion': MeanReversionStrategy(symbol),
        'MACD': MacdStrategy(symbol),
        'Ensemble': EnsembleStrategy(symbol),
        'AdaptiveRisk': AdaptiveRiskStrategy(symbol, MomentumStrategy(symbol))
    }

    results = {}
    for name, strategy in strategies.items():
        try:
            signals, confidence = strategy.generate_signals(price, volume)
            metrics = strategy.calculate_metrics(price, signals)
            metrics['strategy_name'] = name
            metrics['avg_confidence'] = float(confidence.mean())
            results[name] = metrics
        except Exception as e:
            logger.exception(f'Error in {name} strategy: {e}')
            results[name] = {'error': str(e)}

    return results


def rank_strategies(comparison_results: Dict[str, Dict[str, float]]) -> List[Tuple[str, float]]:
    """Rank strategies by Sharpe ratio and return ranking.

    Returns:
        List of (strategy_name, score) tuples sorted by score descending
    """
    ranking = []
    for name, metrics in comparison_results.items():
        if 'sharpe_ratio' in metrics:
            score = metrics['sharpe_ratio']
            ranking.append((name, score))

    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking


__all__ = [
    'AdvancedTradingStrategy',
    'MomentumStrategy',
    'MeanReversionStrategy',
    'MacdStrategy',
    'EnsembleStrategy',
    'AdaptiveRiskStrategy',
    'compare_strategies',
    'rank_strategies'
]
