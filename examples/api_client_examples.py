#!/usr/bin/env python3
"""
API Client Examples - CRISPR-FinAI
Demonstrates how to interact with the REST API.
"""

import requests
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"

class CRISPRClient:
    """Client for CRISPR-FinAI REST API."""

    def __init__(self, base_url: str = API_BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_health(self) -> Dict:
        """Get system health status."""
        response = requests.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()

    def get_models(self, symbol: Optional[str] = None,
                   status: Optional[str] = None,
                   min_sharpe: Optional[float] = None) -> List[Dict]:
        """Get list of models with optional filters."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        if status:
            params["status"] = status
        if min_sharpe is not None:
            params["min_sharpe"] = min_sharpe

        response = requests.get(
            f"{self.base_url}/api/models",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_model(self, symbol: str, model: str) -> Dict:
        """Get specific model information."""
        response = requests.get(
            f"{self.base_url}/api/models/{symbol}/{model}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_metrics(self, symbol: Optional[str] = None,
                   model: Optional[str] = None,
                   time_range: str = "1d",
                   limit: int = 100) -> List[Dict]:
        """Get performance metrics."""
        params = {
            "time_range": time_range,
            "limit": limit
        }
        if symbol:
            params["symbol"] = symbol
        if model:
            params["model"] = model

        response = requests.get(
            f"{self.base_url}/api/metrics",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def run_backtest(self, symbol: str, model: str,
                    start_date: str, end_date: str,
                    initial_capital: float = 100000.0,
                    commission: float = 0.001,
                    slippage: float = 0.0005) -> Dict:
        """Run backtest."""
        data = {
            "symbol": symbol,
            "model": model,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "commission": commission,
            "slippage": slippage
        }

        response = requests.post(
            f"{self.base_url}/api/backtest",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def get_symbols(self) -> List[str]:
        """Get available symbols."""
        response = requests.get(
            f"{self.base_url}/api/symbols",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["symbols"]

    def get_model_types(self) -> List[str]:
        """Get available model types."""
        response = requests.get(
            f"{self.base_url}/api/model-types",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["models"]


def example_1_health_check():
    """Example 1: Check system health."""
    print("\n" + "="*60)
    print("Example 1: System Health Check")
    print("="*60)

    client = CRISPRClient()
    health = client.get_health()

    print(f"\n✅ System Status: {health['status'].upper()}")
    print(f"📊 Total Models: {health['total_models']}")
    print(f"🟢 Healthy: {health['healthy_models']}")
    print(f"🔴 Drifting: {health['drifting_models']}")
    print(f"📈 Avg Sharpe: {health['avg_sharpe']:.2f}")
    print(f"⏱️  Uptime: {health['uptime']:.2f} hours")


def example_2_list_models():
    """Example 2: List all models."""
    print("\n" + "="*60)
    print("Example 2: List All Models")
    print("="*60)

    client = CRISPRClient()
    models = client.get_models()

    print(f"\nFound {len(models)} models:")

    for model in models[:5]:  # Show first 5
        print(f"\n📊 {model['symbol']} - {model['model']}")
        print(f"   Status: {model['status']}")
        print(f"   Sharpe: {model['sharpe_ratio']:.2f}")
        print(f"   Win Rate: {model['win_rate']:.1f}%")


def example_3_filter_models():
    """Example 3: Filter models by criteria."""
    print("\n" + "="*60)
    print("Example 3: Filter High-Performance Models")
    print("="*60)

    client = CRISPRClient()

    # Get models with Sharpe > 1.0
    models = client.get_models(min_sharpe=1.0)

    print(f"\nFound {len(models)} high-performance models (Sharpe > 1.0):")

    for model in models:
        print(f"\n⭐ {model['symbol']} - {model['model']}")
        print(f"   Sharpe: {model['sharpe_ratio']:.2f}")
        print(f"   Annual Return: {model['annual_return']:.1f}%")
        print(f"   Max Drawdown: {model['max_drawdown']:.1f}%")


def example_4_specific_model():
    """Example 4: Get specific model details."""
    print("\n" + "="*60)
    print("Example 4: Get Specific Model Details")
    print("="*60)

    client = CRISPRClient()

    try:
        model = client.get_model("AAPL", "naive_momentum")

        print(f"\n📊 Model: {model['symbol']} - {model['model']}")
        print(f"{'='*40}")
        print(f"Status:         {model['status']}")
        print(f"Sharpe Ratio:   {model['sharpe_ratio']:.2f}")
        print(f"Annual Return:  {model['annual_return']:.1f}%")
        print(f"Volatility:     {model['volatility']:.1f}%")
        print(f"Max Drawdown:   {model['max_drawdown']:.1f}%")
        print(f"Win Rate:       {model['win_rate']:.1f}%")
        print(f"Last Updated:   {model['last_updated']}")

    except requests.exceptions.HTTPError:
        print("\n❌ Error: Model not found")


def example_5_get_metrics():
    """Example 5: Get performance metrics."""
    print("\n" + "="*60)
    print("Example 5: Get Performance Metrics")
    print("="*60)

    client = CRISPRClient()

    # Get metrics for AAPL
    metrics = client.get_metrics(symbol="AAPL", limit=5)

    print("\nRecent metrics for AAPL:")

    for metric in metrics:
        print(f"\n📈 {metric['model']}")
        print(f"   Sharpe: {metric['sharpe_ratio']:.2f}")
        print(f"   Daily Return: {metric['daily_return']*100:.2f}%")
        print(f"   Win Rate: {metric['win_rate']:.1f}%")
        print(f"   Timestamp: {metric['timestamp']}")


def example_6_run_backtest():
    """Example 6: Run backtest."""
    print("\n" + "="*60)
    print("Example 6: Run Backtest")
    print("="*60)

    client = CRISPRClient()

    print("\n🔄 Running backtest...")

    result = client.run_backtest(
        symbol="AAPL",
        model="naive_momentum",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000.0
    )

    print("\n✅ Backtest Complete!")
    print(f"{'='*40}")
    print(f"Symbol:         {result['symbol']}")
    print(f"Model:          {result['model']}")
    print(f"Sharpe Ratio:   {result['sharpe_ratio']:.2f}")
    print(f"Total Return:   {result['total_return']:.1f}%")
    print(f"Annual Return:  {result['annual_return']:.1f}%")
    print(f"Max Drawdown:   {result['max_drawdown']:.1f}%")
    print(f"Win Rate:       {result['win_rate']:.1f}%")
    print(f"Total Trades:   {result['total_trades']}")
    print(f"Profit Factor:  {result['profit_factor']:.2f}")
    print(f"Execution Time: {result['execution_time']:.2f}s")


def example_7_list_symbols():
    """Example 7: List available symbols."""
    print("\n" + "="*60)
    print("Example 7: List Available Symbols")
    print("="*60)

    client = CRISPRClient()
    symbols = client.get_symbols()

    print(f"\nAvailable symbols ({len(symbols)}):")
    print(", ".join(symbols))


def example_8_batch_analysis():
    """Example 8: Batch analysis across multiple models."""
    print("\n" + "="*60)
    print("Example 8: Batch Analysis")
    print("="*60)

    client = CRISPRClient()

    # Get all models
    models = client.get_models()

    # Analyze by symbol
    symbol_performance = {}
    for model in models:
        symbol = model["symbol"]
        if symbol not in symbol_performance:
            symbol_performance[symbol] = []
        symbol_performance[symbol].append(model["sharpe_ratio"])

    print("\nAverage Sharpe by Symbol:")
    print("="*40)

    for symbol, sharpes in sorted(symbol_performance.items()):
        avg_sharpe = sum(sharpes) / len(sharpes)
        print(f"{symbol:6} | {avg_sharpe:6.2f} | {len(sharpes)} models")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("🚀 CRISPR-FinAI API Client Examples")
    print("="*60)
    print("\nMake sure the API server is running:")
    print("  python core/api_server.py")
    print("\nPress Enter to continue...")
    input()

    try:
        # Run examples
        example_1_health_check()
        input("\nPress Enter for next example...")

        example_2_list_models()
        input("\nPress Enter for next example...")

        example_3_filter_models()
        input("\nPress Enter for next example...")

        example_4_specific_model()
        input("\nPress Enter for next example...")

        example_5_get_metrics()
        input("\nPress Enter for next example...")

        example_6_run_backtest()
        input("\nPress Enter for next example...")

        example_7_list_symbols()
        input("\nPress Enter for next example...")

        example_8_batch_analysis()

        print("\n" + "="*60)
        print("✅ All examples completed!")
        print("="*60 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
