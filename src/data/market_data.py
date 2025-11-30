"""Real market data integration with yfinance fallback.

This module provides:
1. Real market data fetching (yfinance)
2. Data validation and cleaning
3. Graceful fallback to synthetic data
4. Historical price data caching
5. Error handling for API limits
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import yfinance, fallback to synthetic if unavailable
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    logger.warning("yfinance not installed. Falling back to synthetic data.")


class MarketDataLoader:
    """Load real market data from yfinance with fallback to synthetic."""

    def __init__(self, use_cache: bool = True, cache_dir: str = ".data_cache"):
        self.use_cache = use_cache
        self.cache_dir = cache_dir
        self.cache = {}

        if use_cache:
            import os
            os.makedirs(cache_dir, exist_ok=True)

    def fetch_historical_data(
        self,
        symbol: str,
        days: int = 252,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data.

        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
            days: Number of days of historical data (if no dates specified)
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Adj Close
        """
        cache_key = f"{symbol}_{days}_{start_date}_{end_date}"

        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Loading {symbol} from cache")
            return self.cache[cache_key]

        # Try yfinance first
        if HAS_YFINANCE:
            try:
                data = self._fetch_yfinance(symbol, days, start_date, end_date)
                if data is not None and len(data) > 0:
                    logger.info(f"✓ Fetched real data for {symbol}: {len(data)} periods")
                    if self.use_cache:
                        self.cache[cache_key] = data
                    return data
            except Exception as e:
                logger.warning(f"yfinance failed for {symbol}: {e}. Using synthetic fallback.")

        # Fallback to synthetic
        logger.info(f"Using synthetic data for {symbol}")
        data = self._generate_synthetic_data(symbol, days)

        if self.use_cache:
            self.cache[cache_key] = data

        return data

    def _fetch_yfinance(
        self,
        symbol: str,
        days: int,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Optional[pd.DataFrame]:
        """Fetch data from yfinance."""
        if not HAS_YFINANCE:
            return None

        try:
            # Calculate dates if not provided
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if start_date is None:
                start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days)
                start_date = start_dt.strftime("%Y-%m-%d")

            # Fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)

            # Validate
            if data is None or len(data) == 0:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Ensure required columns
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            if not all(col in data.columns for col in required_cols):
                logger.warning(f"Missing required columns for {symbol}")
                return None

            # Handle missing data
            data = data.dropna()
            if len(data) == 0:
                logger.warning(f"All NaN values for {symbol}")
                return None

            logger.info(
                f"Fetched {len(data)} periods for {symbol} "
                f"from {start_date} to {end_date}"
            )

            return data

        except Exception as e:
            logger.error(f"Error fetching {symbol} from yfinance: {e}")
            return None

    def _generate_synthetic_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Generate realistic synthetic price data."""
        np.random.seed(hash(symbol) % 2**32)  # Deterministic per symbol

        # Base parameters
        drift = 0.0001
        volatility = 0.02
        initial_price = 100

        # Generate returns
        returns = np.random.normal(drift, volatility, days)
        prices = initial_price * np.exp(np.cumsum(returns))

        # Generate OHLCV
        open_prices = prices.copy()
        close_prices = prices.copy()
        high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, 0.01, days)))
        low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, 0.01, days)))
        volumes = np.random.randint(1000000, 5000000, days)

        # Create DataFrame
        dates = pd.date_range(end=datetime.now(), periods=days, freq="D")
        data = pd.DataFrame(
            {
                "Open": open_prices,
                "High": high_prices,
                "Low": low_prices,
                "Close": close_prices,
                "Volume": volumes,
                "Adj Close": close_prices,
            },
            index=dates,
        )

        return data

    def get_price_series(self, data: pd.DataFrame) -> pd.Series:
        """Extract price series from OHLCV data."""
        if "Adj Close" in data.columns:
            return data["Adj Close"]
        elif "Close" in data.columns:
            return data["Close"]
        else:
            raise ValueError("No price column found in data")

    def get_volume_series(self, data: pd.DataFrame) -> pd.Series:
        """Extract volume series from OHLCV data."""
        if "Volume" not in data.columns:
            logger.warning("Volume column not found, using zeros")
            return pd.Series(0, index=data.index)
        return data["Volume"]

    def validate_data(self, data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate data quality.

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        if data is None or len(data) == 0:
            issues.append("Empty dataset")
            return False, issues

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            issues.append(f"Missing columns: {missing}")

        # Check for NaN
        nan_count = data[required_cols].isna().sum().sum()
        if nan_count > 0:
            issues.append(f"{nan_count} NaN values found")

        # Check for duplicates
        if data.index.duplicated().any():
            issues.append("Duplicate dates found")

        # Check for price validity
        if (data["Close"] <= 0).any():
            issues.append("Invalid prices (<=0) found")

        return len(issues) == 0, issues


class BacktestDataManager:
    """Manage data for backtesting with multiple strategies."""

    def __init__(self, loader: MarketDataLoader):
        self.loader = loader
        self.data_cache = {}

    def get_backtest_data(
        self,
        symbols: List[str],
        days: int = 252,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols.

        Returns:
            Dict mapping symbol -> DataFrame
        """
        data = {}

        for symbol in symbols:
            try:
                df = self.loader.fetch_historical_data(
                    symbol, days=days, start_date=start_date, end_date=end_date
                )

                # Validate
                is_valid, issues = self.loader.validate_data(df)
                if not is_valid:
                    logger.warning(f"{symbol}: {issues}")

                data[symbol] = df

            except Exception as e:
                logger.error(f"Failed to load {symbol}: {e}")
                continue

        return data

    def align_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Align data across multiple symbols (same dates).

        Returns:
            Dict with aligned data
        """
        if not data_dict:
            return data_dict

        # Get common dates
        all_dates = [df.index for df in data_dict.values()]
        common_dates = all_dates[0]

        for dates in all_dates[1:]:
            common_dates = common_dates.intersection(dates)

        # Align all data
        aligned = {}
        for symbol, df in data_dict.items():
            aligned[symbol] = df.loc[common_dates]

        logger.info(
            f"Aligned {len(data_dict)} symbols to {len(common_dates)} common dates"
        )

        return aligned


def get_market_data(symbol: str, days: int = 252) -> Tuple[pd.Series, pd.Series]:
    """Convenience function to get price and volume.

    Returns:
        (price_series, volume_series)
    """
    loader = MarketDataLoader()
    data = loader.fetch_historical_data(symbol, days=days)
    price = loader.get_price_series(data)
    volume = loader.get_volume_series(data)
    return price, volume
