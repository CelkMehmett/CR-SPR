"""
POC runner for quick backtests. Uses `src.eval.backtest` utilities.
Falls back to `yfinance` if `src.data.loader.FinancialDataLoader` is not available.
"""

from __future__ import annotations
import argparse
from datetime import datetime
from typing import List

try:
    from src.eval.backtest import simple_backtest
except Exception as e:
    print('Missing backtest utilities:', e)
    raise

# try to import project loader
HAS_LOADER = False
try:
    from src.data.loader import FinancialDataLoader

    HAS_LOADER = True
except Exception:
    HAS_LOADER = False


def download_yfinance(symbol: str, start: str, end: str):
    import yfinance as yf

    df = yf.download(symbol, start=start, end=end, progress=False)
    return df


def naive_signal_from_price(price):
    """Simple momentum signal: close > sma(20) -> 1 else 0."""
    sma = price.rolling(20).mean()
    sig = (price > sma).astype(int)
    return sig


def run(symbols: List[str], start: str, end: str):
    results = {}
    for s in symbols:
        if HAS_LOADER:
            loader = FinancialDataLoader()
            df = loader.load_market_data([s], period=None, start=start, end=end)
            if isinstance(df, dict):
                df = df[s]
        else:
            df = download_yfinance(s, start, end)
        # try common column names
        if 'Close' not in df.columns and 'close' in df.columns:
            df = df.rename(columns={'close': 'Close'})
        if 'Close' not in df.columns:
            print(f'No Close for {s}, skipping.')
            continue
        price = df['Close'].sort_index()
        sig = naive_signal_from_price(price)
        strat_rets, metrics = simple_backtest(price, sig, transaction_cost=0.0005, slippage=0.0001)
        results[s] = {'metrics': metrics, 'returns': strat_rets}
        print(f"{s} metrics: {metrics}")
    return results


def main(argv=None):
    p = argparse.ArgumentParser(prog='run_backtest', description='Run a quick POC backtest')
    p.add_argument('--symbols', nargs='+', required=True)
    p.add_argument('--start', default=(datetime.now().date().replace(year=datetime.now().year-2)).isoformat())
    p.add_argument('--end', default=datetime.now().date().isoformat())
    args = p.parse_args(argv)
    run(args.symbols, args.start, args.end)


if __name__ == '__main__':
    main()
