"""
Transaction cost analysis utilities.

Includes simple models for:
- fixed commission per trade (bps)
- slippage as fraction of spread or volatility
- linear market impact (price change proportional to volume)

Provides a demo that applies costs to a synthetic PnL series.
"""
import numpy as np


def apply_commission(trade_size: float, commission_bps: float) -> float:
    """Return commission cost in currency units for a trade.

    trade_size: absolute trade value in currency
    commission_bps: e.g., 1.0 = 1 basis point = 0.0001
    """
    return abs(trade_size) * (commission_bps / 10000.0)


def apply_slippage(price: float, volatility: float, slippage_factor: float = 0.1) -> float:
    """Estimate slippage as a fraction of volatility * slippage_factor.

    Returns expected slippage in price units (positive number representing cost fraction).
    """
    # simple model: slippage proportional to volatility
    return abs(price) * volatility * slippage_factor


def market_impact(volume: float, daily_volume: float, impact_coefficient: float = 0.1) -> float:
    """Linear market impact model: price move = impact_coefficient * (volume / daily_volume)

    Returns fractional price move.
    """
    if daily_volume <= 0:
        return 0.0
    return impact_coefficient * (abs(volume) / daily_volume)


def apply_total_trade_cost(price: float, trade_value: float, volatility: float, daily_volume: float,
                           commission_bps: float = 1.0, slippage_factor: float = 0.1, impact_coeff: float = 0.1) -> float:
    """Compute total cost in currency units for a single trade (commission + slippage + impact).

    trade_value: absolute notional (price * qty)
    price: current price
    Returns total cost (positive value) in currency.
    """
    commission = apply_commission(trade_value, commission_bps)
    slippage = apply_slippage(price, volatility, slippage_factor) * (trade_value / price)
    impact_frac = market_impact(trade_value, daily_volume, impact_coeff)
    impact_cost = impact_frac * trade_value
    total = commission + slippage + impact_cost
    return total


def demo():
    # synthetic PnL: assume strategy generates daily PnL before costs
    rng = np.random.default_rng(0)
    days = 252
    daily_returns = rng.normal(0.001, 0.02, size=days)  # 0.1% mean
    price = 100.0
    daily_vol = 1_000_000.0  # daily volume in currency units

    commission_bps = 2.0
    slippage_factor = 0.1
    impact_coeff = 0.05

    notional = 100_000.0

    gross_pnl = np.cumprod(1 + daily_returns) * notional
    net_pnl = gross_pnl.copy()

    total_costs = 0.0
    for i in range(days):
        # assume one trade per day equal to 1% of notional
        trade_value = notional * 0.01
        price = price * (1 + daily_returns[i])
        vol = abs(daily_returns[i]) * 1000000 + 1e5
        cost = apply_total_trade_cost(price, trade_value, np.std(daily_returns), vol,
                                      commission_bps, slippage_factor, impact_coeff)
        total_costs += cost
        net_pnl[i] -= total_costs / days  # crude per-day cost allocation

    print(f"Gross final value: {gross_pnl[-1]:.2f}")
    print(f"Net final value (approx): {net_pnl[-1]:.2f}")
    print(f"Total costs simulated: {total_costs:.2f}")


if __name__ == '__main__':
    demo()
