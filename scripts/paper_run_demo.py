#!/usr/bin/env python3
"""
Demo runner: feed simple signals derived from latest GA weight_history into the
PaperTradingSimulator and produce a short portfolio summary.

Signal rule (one-step): compare the last two recorded weights for each symbol:
- if last > prev -> BUY signal (1)
- if last < prev -> SELL signal (-1)
- else HOLD (0)

Confidence = normalized abs(last - prev) (clipped to [0.1, 1.0])
Price source: MarketDataLoader (yfinance if available, else synthetic).

Outputs summary JSON to /tmp/paper_run_demo_summary.json
"""
import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.trading.paper_trader import PaperTradingSimulator
from src.data.market_data import MarketDataLoader

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'snapshots')
DEFAULT_OUT_JSON = '/tmp/paper_run_demo_summary.json'
DEFAULT_TRADES_CSV = '/tmp/paper_run_demo_trades.csv'
DEFAULT_EQUITY_PNG = '/tmp/paper_run_demo_equity.png'


def find_latest_snapshot(dirpath):
    js = [os.path.join(dirpath, f) for f in os.listdir(dirpath) if f.endswith('.json')]
    if not js:
        raise FileNotFoundError('No snapshot JSON files in snapshots dir')
    js.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return js[0]


def derive_signals_from_weight_history(wh):
    # wh: {'timestamps': [...], 'weights': {'SYM': [v1, v2, ...]}}
    signals = {}
    confidences = {}
    weights = wh.get('weights', {})
    for sym, series in weights.items():
        # get last two numeric values
        nums = [v for v in series if v is not None]
        if len(nums) >= 2:
            prev, last = nums[-2], nums[-1]
        elif len(nums) == 1:
            prev, last = nums[0], nums[0]
        else:
            prev, last = None, None

        if prev is None or last is None:
            sig = 0
            conf = 0.0
        else:
            if last > prev:
                sig = 1
            elif last < prev:
                sig = -1
            else:
                sig = 0
            diff = abs(last - prev)
            # normalize roughly: map diff to [0.1, 1.0] using a heuristic
            conf = min(1.0, max(0.1, diff * 10))

        signals[sym] = sig
        confidences[sym] = conf
    return signals, confidences


def parse_timestamps(ts_list: List) -> List[datetime]:
    parsed = []
    for t in ts_list:
        if isinstance(t, (int, float)):
            parsed.append(datetime.fromtimestamp(t))
        else:
            try:
                parsed.append(datetime.fromisoformat(str(t)))
            except Exception:
                # fallback try common formats
                parsed.append(datetime.strptime(str(t), "%Y-%m-%dT%H:%M:%S"))
    return parsed


def fetch_price_map_for_symbols(loader, symbols: List[str], start_ts: datetime, end_ts: datetime) -> Dict[str, pd.Series]:
    """Fetch price series for each symbol between start_ts and end_ts."""
    series_map = {}
    start_date = start_ts.strftime("%Y-%m-%d")
    end_date = end_ts.strftime("%Y-%m-%d")
    for sym in symbols:
        try:
            df = loader.fetch_historical_data(sym, start_date=start_date, end_date=end_date)
            ps = loader.get_price_series(df)
            ps = ps.sort_index()
            series_map[sym] = ps
        except Exception:
            # leave missing
            series_map[sym] = pd.Series([], dtype=float)
    return series_map


def get_price_for_symbol(loader, symbol):
    try:
        price_series, _ = loader.fetch_historical_data(symbol, days=5).pipe(lambda df: (df['Adj Close'], df['Volume']))
        # take last close
        if len(price_series) > 0:
            return float(price_series.iloc[-1])
    except Exception:
        pass
    # fallback fixed price
    return 100.0


def main():
    parser = argparse.ArgumentParser(description="Paper trading demo runner")
    parser.add_argument("--snapshot", help="Path to snapshot JSON (default: latest)")
    parser.add_argument("--out", default=DEFAULT_OUT_JSON, help="Output summary JSON path")
    parser.add_argument("--trades", default=DEFAULT_TRADES_CSV, help="Output trades CSV path")
    parser.add_argument("--equity", default=DEFAULT_EQUITY_PNG, help="Output equity PNG path")
    parser.add_argument("--mode", default="one-step", choices=("one-step", "replay"), help="one-step (default) or replay across timestamps")
    parser.add_argument("--initial-capital", type=float, default=100000, help="Initial capital for simulator")
    parser.add_argument("--plot", action="store_true", help="Save equity curve PNG")

    args = parser.parse_args()

    latest = args.snapshot or find_latest_snapshot(SNAPSHOT_DIR)
    print('Using snapshot:', latest)
    with open(latest, 'r', encoding='utf-8') as fh:
        snap = json.load(fh)

    wh = snap.get('metadata', {}).get('telemetry', {}).get('weight_history') or {}
    if not wh:
        print('No weight_history found in snapshot telemetry')
        return

    loader = MarketDataLoader()
    sim = PaperTradingSimulator(initial_capital=args.initial_capital)

    out_json = args.out
    trades_csv = args.trades
    equity_png = args.equity

    if args.mode == 'one-step':
        signals, confidences = derive_signals_from_weight_history(wh)

        executed = []

        for sym, sig in signals.items():
            conf = confidences.get(sym, 0.0)
            # get current price (last close) via loader
            try:
                data = loader.fetch_historical_data(sym, days=5)
                price = loader.get_price_series(data).iloc[-1]
                price = float(price)
            except Exception:
                price = 100.0

            if sig == 0:
                continue

            # simple quantity_fn: risk 0.5% capital per trade
            def quantity_fn(confidence, cash, price):
                risk = sim.portfolio.initial_capital * 0.005
                qty = max(1, int((risk * confidence) / price))
                return qty

            order = sim.process_signal(sym, sig, conf, price, quantity_fn=quantity_fn)
            executed.append({
                'symbol': sym,
                'signal': sig,
                'confidence': conf,
                'price': price,
                'order_id': order.order_id if order else None,
                'status': order.status.name if order else 'rejected'
            })

        # Prepare summary
        last_prices = {}
        for sym in signals.keys():
            try:
                data = loader.fetch_historical_data(sym, days=5)
                price = loader.get_price_series(data).iloc[-1]
                last_prices[sym] = float(price)
            except Exception:
                last_prices[sym] = 100.0

        # Ensure simulator has latest prices for performance calculation
        sim.update_prices(last_prices)
        summary = sim.get_performance()
        summary['timestamp'] = datetime.utcnow().isoformat()
        summary['executed_orders'] = executed

        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2, default=str)

        print('Wrote summary to', out_json)
        print('Summary:', json.dumps({k: summary[k] for k in ['initial_capital','current_value','total_return','num_trades','num_positions'] if k in summary}, indent=2, default=str))

    else:
        # Replay mode: step through weight_history timestamps
        timestamps = wh.get('timestamps') or []
        parsed_ts = parse_timestamps(timestamps) if timestamps else []
        if not parsed_ts:
            # fallback to indices if no timestamps
            n = 0
            for v in wh.get('weights', {}).values():
                n = max(n, len(v))
            parsed_ts = [datetime.utcnow() for _ in range(n)]

        start_ts = parsed_ts[0]
        end_ts = parsed_ts[-1]

        symbols = sorted(list(wh.get('weights', {}).keys()))
        price_series_map = fetch_price_map_for_symbols(loader, symbols, start_ts, end_ts)

        equity_curve = []
        equity_times = []

        # iterate over time steps (from 1..n-1)
        n_steps = len(parsed_ts)
        for i in range(1, n_steps):
            ts = parsed_ts[i]
            # build signals for this timestep
            signals_step = {}
            confidences_step = {}
            for sym in symbols:
                series = wh.get('weights', {}).get(sym, [])
                # try to get values at i-1 and i safely
                prev = series[i-1] if i-1 < len(series) else None
                last = series[i] if i < len(series) else None
                if prev is None or last is None:
                    sig = 0
                    conf = 0.0
                else:
                    if last > prev:
                        sig = 1
                    elif last < prev:
                        sig = -1
                    else:
                        sig = 0
                    diff = abs(last - prev)
                    conf = min(1.0, max(0.1, diff * 10))

                signals_step[sym] = sig
                confidences_step[sym] = conf

            # get prices at this timestamp
            current_prices = {}
            for sym in symbols:
                ps = price_series_map.get(sym)
                price_val = None
                try:
                    if ps is not None and len(ps) > 0:
                        # asof will return last valid on or before ts
                        price_val = ps.asof(pd.Timestamp(ts))
                    if price_val is None or pd.isna(price_val):
                        # fallback to last available price
                        price_val = ps.iloc[-1] if (ps is not None and len(ps) > 0) else None
                except Exception:
                    price_val = None

                if price_val is None or pd.isna(price_val):
                    price_val = 100.0

                current_prices[sym] = float(price_val)

            # update simulator prices
            sim.update_prices(current_prices)

            # process signals for this timestep
            for sym, sig in signals_step.items():
                if sig == 0:
                    continue
                conf = confidences_step.get(sym, 0.0)

                def quantity_fn(confidence, cash, price):
                    risk = sim.portfolio.initial_capital * 0.005
                    qty = max(1, int((risk * confidence) / price))
                    return qty

                sim.process_signal(sym, sig, conf, current_prices[sym], quantity_fn=quantity_fn)

            # record equity
            val = sim.portfolio.get_portfolio_value(current_prices)
            equity_curve.append(val)
            equity_times.append(ts.isoformat())

        # finalize
        sim.update_prices(current_prices)
        summary = sim.get_performance()
        summary['timestamp'] = datetime.utcnow().isoformat()
        summary['equity_curve'] = {'times': equity_times, 'values': equity_curve}

        # write trades CSV
        trades = []
        for t in sim.portfolio.trades:
            trades.append({
                'order_id': t.order_id,
                'symbol': t.symbol,
                'quantity': t.quantity,
                'fill_price': t.fill_price,
                'status': t.status.name,
                'timestamp': str(t.fill_timestamp),
            })

        if trades:
            pd.DataFrame(trades).to_csv(trades_csv, index=False)
            print('Wrote trades to', trades_csv)

        # optionally plot equity curve
        if args.plot and equity_curve:
            plt.figure(figsize=(8, 4))
            plt.plot(pd.to_datetime(equity_times), equity_curve)
            plt.title('Equity Curve')
            plt.ylabel('Portfolio Value')
            plt.xlabel('Time')
            plt.tight_layout()
            plt.savefig(equity_png)
            print('Wrote equity PNG to', equity_png)

        # write summary
        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2, default=str)

        print('Wrote summary to', out_json)
        print('Summary:', json.dumps({k: summary[k] for k in ['initial_capital','current_value','total_return','num_trades','num_positions'] if k in summary}, indent=2, default=str))


if __name__ == '__main__':
    main()
