"""Paper trading simulator for live strategy testing.

This module provides:
1. Simulated trading execution
2. Order management
3. Portfolio tracking
4. P&L calculation
5. Performance monitoring
"""

import logging
from typing import Dict, List, Optional
from enum import Enum
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types."""
    BUY = 1
    SELL = -1
    HOLD = 0


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """Represents a single order."""

    def __init__(
        self,
        order_id: str,
        symbol: str,
        quantity: float,
        price: float,
        order_type: OrderType,
        timestamp: datetime,
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.order_type = order_type
        self.timestamp = timestamp
        self.status = OrderStatus.PENDING
        self.fill_price = None
        self.fill_timestamp = None

    def execute(self, fill_price: float, slippage: float = 0.0005):
        """Execute order with slippage."""
        self.fill_price = fill_price * (1 + slippage if self.order_type == OrderType.BUY else 1 - slippage)
        self.fill_timestamp = datetime.now()
        self.status = OrderStatus.FILLED


class Position:
    """Represents a position in a symbol."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.quantity = 0
        self.avg_price = 0
        self.value = 0
        self.entry_trades = []
        self.exit_trades = []

    def add_trade(self, quantity: float, price: float):
        """Add a trade (long or short)."""
        if quantity > 0:  # Buy
            total_cost = self.quantity * self.avg_price + quantity * price
            self.quantity += quantity
            self.avg_price = total_cost / self.quantity if self.quantity > 0 else 0
            self.entry_trades.append({"qty": quantity, "price": price, "time": datetime.now()})
        elif quantity < 0:  # Sell
            self.quantity += quantity  # quantity is negative
            self.exit_trades.append({"qty": abs(quantity), "price": price, "time": datetime.now()})

    def get_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L."""
        return self.quantity * (current_price - self.avg_price)

    def get_value(self, current_price: float) -> float:
        """Get position value at current price."""
        return self.quantity * current_price


class Portfolio:
    """Manages portfolio of positions."""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = []
        self.timestamp_start = datetime.now()

    def place_order(
        self,
        symbol: str,
        quantity: float,
        price: float,
        order_type: OrderType,
        slippage: float = 0.0005,
        commission: float = 0.001,
    ) -> Order:
        """Place and execute an order."""
        order_id = f"{symbol}_{len(self.trades)}"

        # Validate
        trade_value = quantity * price
        total_cost = trade_value * (1 + commission)

        if order_type == OrderType.BUY and total_cost > self.cash:
            logger.warning(f"Insufficient cash for {order_id}")
            return None

        # Create order
        order = Order(
            order_id,
            symbol,
            quantity,
            price,
            order_type,
            datetime.now(),
        )

        # Execute
        order.execute(price, slippage)

        # Update portfolio
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)

        if order_type == OrderType.BUY:
            self.positions[symbol].add_trade(quantity, order.fill_price)
            self.cash -= total_cost
        elif order_type == OrderType.SELL:
            self.positions[symbol].add_trade(-quantity, order.fill_price)
            self.cash += (trade_value * (1 - commission))

        self.trades.append(order)
        logger.info(
            f"{order_type.name} {quantity}x {symbol} @{order.fill_price:.2f} "
            f"(cash: ${self.cash:.2f})"
        )

        return order

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Get total portfolio value."""
        position_value = sum(
            pos.get_value(current_prices.get(symbol, pos.avg_price))
            for symbol, pos in self.positions.items()
        )
        return self.cash + position_value

    def get_total_pnl(self, current_prices: Dict[str, float]) -> float:
        """Get total unrealized P&L."""
        total_pnl = sum(
            pos.get_pnl(current_prices.get(symbol, pos.avg_price))
            for symbol, pos in self.positions.items()
        )
        # Account for commission costs
        commission_paid = sum(0.001 * (t.quantity * t.fill_price) for t in self.trades)
        return total_pnl - commission_paid

    def get_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get portfolio summary."""
        portfolio_value = self.get_portfolio_value(current_prices)
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital

        return {
            "initial_capital": self.initial_capital,
            "current_value": portfolio_value,
            "cash": self.cash,
            "total_return": total_return,
            "unrealized_pnl": self.get_total_pnl(current_prices),
            "num_trades": len(self.trades),
            "num_positions": len(self.positions),
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_price": current_prices.get(symbol, pos.avg_price),
                    "value": pos.get_value(current_prices.get(symbol, pos.avg_price)),
                    "pnl": pos.get_pnl(current_prices.get(symbol, pos.avg_price)),
                }
                for symbol, pos in self.positions.items()
            },
        }


class PaperTradingSimulator:
    """Simulate trading strategies in real-time."""

    def __init__(self, initial_capital: float = 100000):
        self.portfolio = Portfolio(initial_capital)
        self.signal_history = []
        self.trade_history = []

    def process_signal(
        self,
        symbol: str,
        signal: float,  # 1 (buy), -1 (sell), 0 (hold)
        confidence: float,  # 0-1
        price: float,
        quantity_fn=None,  # Function to calculate position size
    ):
        """Process trading signal and place order."""
        if signal == 0:
            return None

        # Determine position size
        if quantity_fn:
            quantity = quantity_fn(confidence, self.portfolio.cash, price)
        else:
            # Default: risk 2% of portfolio per trade
            risk_per_trade = self.portfolio.initial_capital * 0.02
            quantity = risk_per_trade / price

        # Scale by confidence
        quantity *= confidence

        order_type = OrderType.BUY if signal > 0 else OrderType.SELL

        # Place order
        order = self.portfolio.place_order(
            symbol,
            quantity,
            price,
            order_type,
            slippage=0.0005,
            commission=0.001,
        )

        if order:
            self.signal_history.append(
                {
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "signal": signal,
                    "confidence": confidence,
                    "price": price,
                    "order_id": order.order_id,
                }
            )

        return order

    def update_prices(self, current_prices: Dict[str, float]):
        """Update current market prices."""
        self.last_prices = current_prices

    def get_performance(self) -> Dict:
        """Get performance metrics."""
        if not self.last_prices:
            return {}

        summary = self.portfolio.get_summary(self.last_prices)

        # Win rate
        if len(self.trade_history) > 0:
            wins = sum(1 for t in self.trade_history if t.get("pnl", 0) > 0)
            win_rate = wins / len(self.trade_history)
        else:
            win_rate = 0

        return {
            **summary,
            "win_rate": win_rate,
            "trades_signal_history": len(self.signal_history),
            "trades_executed": len(self.trade_history),
        }

    def get_equity_curve(self) -> pd.DataFrame:
        """Get portfolio equity curve."""
        if not self.portfolio.portfolio_values:
            return pd.DataFrame()

        return pd.DataFrame(
            {
                "value": self.portfolio.portfolio_values,
            }
        )


def simulate_trading_session(
    strategy,
    price_data: pd.Series,
    volume_data: Optional[pd.Series] = None,
    initial_capital: float = 100000,
) -> Dict:
    """Simulate a full trading session.

    Args:
        strategy: Strategy object with generate_signals()
        price_data: Historical price series
        volume_data: Historical volume (optional)
        initial_capital: Starting capital

    Returns:
        Dict with simulation results
    """
    simulator = PaperTradingSimulator(initial_capital)

    # Generate signals
    signals, confidence = strategy.generate_signals(price_data, volume_data)

    # Process each period
    for i, (price, signal, conf) in enumerate(zip(price_data, signals, confidence)):
        current_prices = {strategy.symbol: price}
        simulator.update_prices(current_prices)

        if not pd.isna(signal) and signal != 0:
            simulator.process_signal(
                strategy.symbol,
                signal,
                conf,
                price,
            )

    return simulator.get_performance()
