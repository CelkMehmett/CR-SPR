"""
🧬 Financial Data Loader — DNA Sequencing Lab

Loads, preprocesses, and prepares financial data for the CRISPR-FinAI system.
Like preparing genetic samples for sequencing, this module ensures clean,
normalized data ready for analysis and model training.

Think like biology. Code like AI.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
from dataclasses import dataclass
import warnings
from pathlib import Path
import logging

# Suppress yfinance warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)

logger = logging.getLogger(__name__)


@dataclass
class DataProfile:
    """
    🔬 Financial Data Profile — Like a DNA sample profile
    
    Contains metadata about a financial dataset including quality metrics,
    completeness, and characteristics essential for model training.
    """
    symbol: str
    start_date: datetime
    end_date: datetime
    total_samples: int
    missing_values: int
    data_quality_score: float
    features: List[str]
    data_range: Dict[str, float]
    volatility_profile: Dict[str, float]
    drift_indicators: Dict[str, float]


class FinancialDataLoader:
    """
    🧬 Financial Data Sequencer
    
    Primary data loading and preprocessing system for financial time series.
    Like a DNA sequencer, it reads raw market data and converts it into
    clean, standardized format suitable for AI model consumption.
    
    Biological Analogy:
    - Raw Market Data → Biological Sample
    - Data Cleaning → Sample Preparation
    - Feature Engineering → DNA Amplification
    - Normalization → Standardization
    """

    def __init__(self, cache_dir: str = "./data/cache"):
        """
        Initialize the financial data sequencer.
        
        Args:
            cache_dir: Directory for caching downloaded data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Data quality thresholds
        self.min_quality_score = 0.8
        self.max_missing_ratio = 0.05

        # Feature engineering parameters
        self.technical_indicators = [
            'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'bollinger_upper', 'bollinger_lower', 'bollinger_width',
            'atr_14', 'volume_sma_20'
        ]

        self._cached_data = {}

    def load_market_data(self,
                        symbols: Union[str, List[str]],
                        period: str = "2y",
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """
        🔬 Sequence market DNA
        
        Download and cache raw market data for specified symbols.
        Like extracting DNA from biological samples.
        
        Args:
            symbols: Stock symbol(s) to download
            period: Time period ('1y', '2y', '5y', 'max') or custom range
            start_date: Custom start date (YYYY-MM-DD)
            end_date: Custom end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLCV data and basic metadata
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        # Check cache first
        cache_key = f"{'_'.join(symbols)}_{period}_{start_date}_{end_date}"
        if cache_key in self._cached_data:
            logger.info(f"Loading {symbols} from cache")
            return self._cached_data[cache_key].copy()

        logger.info(f"Downloading market data for {symbols}")

        try:
            # Download data using yfinance
            tickers = yf.Tickers(' '.join(symbols))

            if start_date and end_date:
                data = tickers.download(start=start_date, end=end_date, group_by='ticker')
            else:
                data = tickers.download(period=period, group_by='ticker')

            # Handle single vs multiple symbols
            if len(symbols) == 1:
                data.columns = pd.MultiIndex.from_product([symbols, data.columns])

            # Cache the data
            self._cached_data[cache_key] = data.copy()

            logger.info(f"Successfully loaded {len(data)} rows for {len(symbols)} symbols")
            return data

        except Exception as e:
            logger.error(f"Failed to download data for {symbols}: {str(e)}")
            raise

    def engineer_features(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        🧬 Amplify genetic features
        
        Create technical indicators and derived features from raw OHLCV data.
        Like DNA amplification, this expands the information content.
        
        Args:
            data: Raw OHLCV data for a single symbol
            symbol: Symbol name for column access
            
        Returns:
            DataFrame with engineered features
        """
        df = data.copy()

        # Extract basic OHLCV
        try:
            open_col = (symbol, 'Open')
            high_col = (symbol, 'High')
            low_col = (symbol, 'Low')
            close_col = (symbol, 'Close')
            volume_col = (symbol, 'Volume')

            # Basic price features
            df[(symbol, 'returns')] = df[close_col].pct_change()
            df[(symbol, 'log_returns')] = np.log(df[close_col] / df[close_col].shift(1))
            df[(symbol, 'volatility_5d')] = df[(symbol, 'returns')].rolling(5).std()
            df[(symbol, 'volatility_20d')] = df[(symbol, 'returns')].rolling(20).std()

            # Moving averages
            df[(symbol, 'sma_20')] = df[close_col].rolling(20).mean()
            df[(symbol, 'sma_50')] = df[close_col].rolling(50).mean()
            df[(symbol, 'ema_12')] = df[close_col].ewm(span=12).mean()
            df[(symbol, 'ema_26')] = df[close_col].ewm(span=26).mean()

            # RSI
            delta = df[close_col].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df[(symbol, 'rsi_14')] = 100 - (100 / (1 + rs))

            # MACD
            df[(symbol, 'macd')] = df[(symbol, 'ema_12')] - df[(symbol, 'ema_26')]
            df[(symbol, 'macd_signal')] = df[(symbol, 'macd')].ewm(span=9).mean()
            df[(symbol, 'macd_histogram')] = df[(symbol, 'macd')] - df[(symbol, 'macd_signal')]

            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            sma_bb = df[close_col].rolling(bb_period).mean()
            bb_std_dev = df[close_col].rolling(bb_period).std()
            df[(symbol, 'bollinger_upper')] = sma_bb + (bb_std_dev * bb_std)
            df[(symbol, 'bollinger_lower')] = sma_bb - (bb_std_dev * bb_std)
            df[(symbol, 'bollinger_width')] = df[(symbol, 'bollinger_upper')] - df[(symbol, 'bollinger_lower')]

            # Average True Range (ATR)
            high_low = df[high_col] - df[low_col]
            high_close = np.abs(df[high_col] - df[close_col].shift())
            low_close = np.abs(df[low_col] - df[close_col].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df[(symbol, 'atr_14')] = true_range.rolling(14).mean()

            # Volume indicators
            df[(symbol, 'volume_sma_20')] = df[volume_col].rolling(20).mean()
            df[(symbol, 'volume_ratio')] = df[volume_col] / df[(symbol, 'volume_sma_20')]

            # Price position indicators
            df[(symbol, 'price_position')] = (df[close_col] - df[(symbol, 'sma_20')]) / df[(symbol, 'sma_20')]
            df[(symbol, 'high_low_ratio')] = (df[close_col] - df[low_col]) / (df[high_col] - df[low_col])

        except KeyError as e:
            logger.warning(f"Could not create all features for {symbol}: {str(e)}")

        return df

    def normalize_data(self,
                      data: pd.DataFrame,
                      method: str = "robust",
                      lookback_window: int = 252) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        🧬 Standardize genetic sequences
        
        Normalize financial data to ensure stable model training.
        Like standardizing DNA concentrations for consistent analysis.
        
        Args:
            data: Raw financial data
            method: Normalization method ('robust', 'minmax', 'zscore')
            lookback_window: Rolling window for adaptive normalization
            
        Returns:
            Tuple of (normalized_data, normalization_parameters)
        """
        df = data.copy()
        norm_params = {}

        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                series = df[col].dropna()

                if len(series) == 0:
                    continue

                if method == "robust":
                    # Use rolling median and MAD for robust normalization
                    rolling_median = series.rolling(lookback_window, min_periods=50).median()
                    rolling_mad = series.rolling(lookback_window, min_periods=50).apply(
                        lambda x: np.median(np.abs(x - np.median(x)))
                    )

                    # Avoid division by zero
                    rolling_mad = rolling_mad.fillna(1.0)
                    rolling_mad = rolling_mad.where(rolling_mad > 1e-8, 1.0)

                    df[col] = (series - rolling_median) / (1.4826 * rolling_mad)

                    norm_params[col] = {
                        'method': 'robust',
                        'median': rolling_median.iloc[-1] if len(rolling_median) > 0 else series.median(),
                        'mad': rolling_mad.iloc[-1] if len(rolling_mad) > 0 else series.mad()
                    }

                elif method == "minmax":
                    # Rolling min-max normalization
                    rolling_min = series.rolling(lookback_window, min_periods=50).min()
                    rolling_max = series.rolling(lookback_window, min_periods=50).max()

                    range_val = rolling_max - rolling_min
                    range_val = range_val.where(range_val > 1e-8, 1.0)

                    df[col] = (series - rolling_min) / range_val

                    norm_params[col] = {
                        'method': 'minmax',
                        'min': rolling_min.iloc[-1] if len(rolling_min) > 0 else series.min(),
                        'max': rolling_max.iloc[-1] if len(rolling_max) > 0 else series.max()
                    }

                elif method == "zscore":
                    # Rolling z-score normalization
                    rolling_mean = series.rolling(lookback_window, min_periods=50).mean()
                    rolling_std = series.rolling(lookback_window, min_periods=50).std()

                    rolling_std = rolling_std.where(rolling_std > 1e-8, 1.0)

                    df[col] = (series - rolling_mean) / rolling_std

                    norm_params[col] = {
                        'method': 'zscore',
                        'mean': rolling_mean.iloc[-1] if len(rolling_mean) > 0 else series.mean(),
                        'std': rolling_std.iloc[-1] if len(rolling_std) > 0 else series.std()
                    }

        return df, norm_params

    def create_data_profile(self, data: pd.DataFrame, symbol: str) -> DataProfile:
        """
        🔬 Generate data quality profile
        
        Analyze dataset characteristics and quality metrics.
        Like creating a comprehensive DNA sample report.
        
        Args:
            data: Financial dataset to profile
            symbol: Symbol being analyzed
            
        Returns:
            DataProfile with comprehensive quality metrics
        """
        # Basic statistics
        total_samples = len(data)
        missing_values = data.isnull().sum().sum()
        completeness = 1.0 - (missing_values / (total_samples * len(data.columns)))

        # Extract relevant columns for this symbol
        symbol_cols = [col for col in data.columns if col[0] == symbol] if isinstance(data.columns, pd.MultiIndex) else data.columns
        symbol_data = data[symbol_cols] if symbol_cols else data

        # Data range analysis
        numeric_cols = symbol_data.select_dtypes(include=[np.number])
        data_range = {
            'min': float(numeric_cols.min().min()) if len(numeric_cols) > 0 else 0.0,
            'max': float(numeric_cols.max().max()) if len(numeric_cols) > 0 else 0.0,
            'mean': float(numeric_cols.mean().mean()) if len(numeric_cols) > 0 else 0.0
        }

        # Volatility analysis
        if len(symbol_cols) > 0:
            try:
                # Try to find returns or close price column
                close_col = None
                for col in symbol_cols:
                    if isinstance(col, tuple):
                        if 'Close' in col[1] or 'close' in col[1]:
                            close_col = col
                            break
                    elif 'close' in str(col).lower():
                        close_col = col
                        break

                if close_col is not None:
                    returns = data[close_col].pct_change().dropna()
                    volatility_profile = {
                        'daily_vol': float(returns.std()) if len(returns) > 0 else 0.0,
                        'annualized_vol': float(returns.std() * np.sqrt(252)) if len(returns) > 0 else 0.0,
                        'max_drawdown': float((returns.cumsum() - returns.cumsum().cummax()).min()) if len(returns) > 0 else 0.0
                    }
                else:
                    volatility_profile = {'daily_vol': 0.0, 'annualized_vol': 0.0, 'max_drawdown': 0.0}
            except:
                volatility_profile = {'daily_vol': 0.0, 'annualized_vol': 0.0, 'max_drawdown': 0.0}
        else:
            volatility_profile = {'daily_vol': 0.0, 'annualized_vol': 0.0, 'max_drawdown': 0.0}

        # Drift indicators (simple statistical measures)
        drift_indicators = {
            'trend_strength': 0.0,  # Could implement trend analysis
            'regime_changes': 0.0,  # Could implement regime detection
            'mean_reversion': 0.0   # Could implement mean reversion tests
        }

        # Overall quality score
        quality_factors = [
            completeness,  # Data completeness
            min(1.0, total_samples / 1000),  # Sample size adequacy
            1.0 if volatility_profile['daily_vol'] > 0 else 0.5,  # Volatility presence
        ]
        data_quality_score = np.mean(quality_factors)

        return DataProfile(
            symbol=symbol,
            start_date=data.index[0] if len(data) > 0 else datetime.now(),
            end_date=data.index[-1] if len(data) > 0 else datetime.now(),
            total_samples=total_samples,
            missing_values=missing_values,
            data_quality_score=data_quality_score,
            features=list(symbol_cols) if symbol_cols else [],
            data_range=data_range,
            volatility_profile=volatility_profile,
            drift_indicators=drift_indicators
        )

    def simulate_regime_change(self,
                              data: pd.DataFrame,
                              symbol: str,
                              change_date: Optional[str] = None,
                              volatility_multiplier: float = 2.0,
                              trend_shift: float = 0.0) -> pd.DataFrame:
        """
        🧬 Induce artificial mutations
        
        Simulate market regime changes or data drift for testing
        the CRISPR system's detection and adaptation capabilities.
        
        Args:
            data: Original clean data
            symbol: Symbol to modify
            change_date: Date to start regime change (default: middle of dataset)
            volatility_multiplier: Factor to multiply volatility by
            trend_shift: Daily trend shift to add
            
        Returns:
            Data with simulated regime change
        """
        df = data.copy()

        if change_date is None:
            change_idx = len(df) // 2
        else:
            change_idx = df.index.get_loc(pd.to_datetime(change_date))

        logger.info(f"Simulating regime change for {symbol} starting at index {change_idx}")

        try:
            # Find the close price column
            close_col = None
            for col in df.columns:
                if isinstance(col, tuple) and col[0] == symbol and 'Close' in col[1]:
                    close_col = col
                    break

            if close_col is None:
                logger.warning(f"Could not find close price for {symbol}")
                return df

            # Apply regime change to the latter part of the data
            post_change = df.index[change_idx:]

            for i, date in enumerate(post_change):
                if i == 0:
                    continue

                # Original return
                prev_price = df.loc[df.index[change_idx + i - 1], close_col]
                current_price = df.loc[date, close_col]
                original_return = (current_price - prev_price) / prev_price

                # Modified return with increased volatility and trend shift
                modified_return = original_return * volatility_multiplier + trend_shift

                # Apply the modified return
                new_price = prev_price * (1 + modified_return)
                df.loc[date, close_col] = new_price

                # Update other OHLC prices proportionally
                for price_type in ['Open', 'High', 'Low']:
                    price_col = (symbol, price_type)
                    if price_col in df.columns:
                        original_ratio = df.loc[date, price_col] / current_price
                        df.loc[date, price_col] = new_price * original_ratio

        except Exception as e:
            logger.error(f"Failed to simulate regime change: {str(e)}")

        return df

    def prepare_training_data(self,
                             symbols: List[str],
                             features: Optional[List[str]] = None,
                             train_ratio: float = 0.8,
                             normalize: bool = True) -> Dict[str, pd.DataFrame]:
        """
        🧬 Prepare genome for analysis
        
        Create clean, normalized training and validation datasets
        ready for model training and testing.
        
        Args:
            symbols: List of symbols to prepare
            features: Specific features to include (None = all)
            train_ratio: Fraction of data for training
            normalize: Whether to normalize the data
            
        Returns:
            Dictionary with 'train' and 'val' DataFrames
        """
        # Load and engineer features for all symbols
        all_data = []

        for symbol in symbols:
            # Load raw data
            raw_data = self.load_market_data(symbol)

            # Engineer features
            featured_data = self.engineer_features(raw_data, symbol)

            # Select specific features if requested
            if features:
                symbol_features = [(symbol, feat) for feat in features if (symbol, feat) in featured_data.columns]
                featured_data = featured_data[symbol_features]

            all_data.append(featured_data)

        # Combine all symbols
        combined_data = pd.concat(all_data, axis=1)

        # Remove rows with too many NaN values
        combined_data = combined_data.dropna(thresh=len(combined_data.columns) * 0.5)

        # Normalize if requested
        if normalize:
            combined_data, _ = self.normalize_data(combined_data)

        # Split into train/validation
        split_idx = int(len(combined_data) * train_ratio)

        train_data = combined_data.iloc[:split_idx]
        val_data = combined_data.iloc[split_idx:]

        logger.info(f"Prepared training data: {len(train_data)} train samples, {len(val_data)} validation samples")

        return {
            'train': train_data,
            'val': val_data,
            'full': combined_data
        }
