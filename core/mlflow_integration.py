"""
MLflow Integration with CRISPR Advanced Backtester
Complete experiment tracking for all backtest types.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mlflow_tracker import CRISPRMLflowTracker
from core.backtest_integration import CRISPRBacktestIntegration
import pandas as pd
from typing import List, Dict, Optional


class CRISPRMLflowIntegration:
    """
    Integration between CRISPR backtesting and MLflow tracking.
    """

    def __init__(self,
                 experiment_name: str = "CRISPR-FinAI-Production",
                 data_dir: str = "poc/scale_results_quick"):
        """
        Initialize integrated system.
        
        Args:
            experiment_name: MLflow experiment name
            data_dir: CRISPR data directory
        """
        self.tracker = CRISPRMLflowTracker(
            experiment_name=experiment_name,
            tracking_uri="./mlruns"
        )
        self.backtest = CRISPRBacktestIntegration(data_dir=data_dir)
        self.experiment_name = experiment_name

    def run_and_track_comprehensive(self,
                                    symbol: str,
                                    model: str,
                                    parameters: Optional[Dict] = None,
                                    tags: Optional[Dict] = None) -> Dict:
        """
        Run comprehensive backtest and track in MLflow.
        
        Args:
            symbol: Trading symbol
            model: Model name
            parameters: Strategy parameters
            tags: Additional MLflow tags
        
        Returns:
            Dictionary with run IDs and results
        """
        print(f"\n{'='*60}")
        print(f"🔬 Running & Tracking: {symbol} - {model}")
        print(f"{'='*60}")

        # Run comprehensive backtest
        results = self.backtest.run_comprehensive_backtest(symbol, model)

        if not results:
            print(f"❌ No results for {symbol}/{model}")
            return {}

        # Track in MLflow
        run_ids = self.tracker.log_comprehensive_experiment(
            symbol=symbol,
            model_name=model,
            comprehensive_results=results,
            parameters=parameters or {},
            tags=tags or {}
        )

        print(f"✅ Tracked in MLflow: {run_ids['comprehensive']}")

        return {
            'run_ids': run_ids,
            'results': results
        }

    def batch_run_and_track(self,
                           symbols: Optional[List[str]] = None,
                           models: Optional[List[str]] = None,
                           max_runs: Optional[int] = None) -> pd.DataFrame:
        """
        Run and track multiple symbol/model combinations.
        
        Args:
            symbols: List of symbols (None = all)
            models: List of models (None = all)
            max_runs: Maximum number of runs
        
        Returns:
            DataFrame with summary of runs
        """
        # Load available combinations
        if not self.backtest.results_file.exists():
            print("❌ Results file not found")
            return pd.DataFrame()

        df = pd.read_csv(self.backtest.results_file)

        # Filter
        if symbols:
            df = df[df['symbol'].isin(symbols)]
        if models:
            df = df[df['model'].isin(models)]
        if max_runs:
            df = df.head(max_runs)

        print(f"\n{'='*60}")
        print(f"🚀 Batch Processing {len(df)} Models")
        print(f"{'='*60}")

        results_summary = []

        for idx, row in df.iterrows():
            symbol = row['symbol']
            model = row['model']

            print(f"\n[{idx+1}/{len(df)}] Processing {symbol} - {model}...")

            try:
                result = self.run_and_track_comprehensive(
                    symbol=symbol,
                    model=model,
                    tags={'batch_run': 'true', 'version': 'v1.0'}
                )

                if result and 'results' in result:
                    simple = result['results'].get('simple', {})
                    wf = result['results'].get('walk_forward', {})
                    mc = result['results'].get('monte_carlo', {})

                    results_summary.append({
                        'symbol': symbol,
                        'model': model,
                        'run_id': result['run_ids'].get('comprehensive', 'N/A'),
                        'sharpe': simple.get('sharpe_ratio', 0),
                        'return': simple.get('total_return', 0) * 100,
                        'wf_consistency': wf.get('consistency', 0) * 100,
                        'mc_prob_positive': mc.get('probability_positive', 0) * 100,
                        'status': 'success'
                    })
                else:
                    results_summary.append({
                        'symbol': symbol,
                        'model': model,
                        'run_id': 'N/A',
                        'sharpe': 0,
                        'return': 0,
                        'wf_consistency': 0,
                        'mc_prob_positive': 0,
                        'status': 'failed'
                    })

            except Exception as e:
                print(f"❌ Error: {e}")
                results_summary.append({
                    'symbol': symbol,
                    'model': model,
                    'run_id': 'N/A',
                    'sharpe': 0,
                    'return': 0,
                    'wf_consistency': 0,
                    'mc_prob_positive': 0,
                    'status': f'error: {str(e)[:50]}'
                })

        summary_df = pd.DataFrame(results_summary)

        # Display summary
        print(f"\n{'='*60}")
        print("📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"\nTotal Runs: {len(summary_df)}")
        print(f"Successful: {len(summary_df[summary_df['status'] == 'success'])}")
        print(f"Failed: {len(summary_df[summary_df['status'] != 'success'])}")

        if not summary_df.empty:
            print("\nTop 5 by Sharpe Ratio:")
            print(summary_df.nlargest(5, 'sharpe')[['symbol', 'model', 'sharpe', 'return']])

        # Save summary
        output_path = Path("mlflow_exports")
        output_path.mkdir(exist_ok=True)
        summary_file = output_path / f"batch_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"\n✅ Summary saved to: {summary_file}")

        return summary_df

    def compare_models_with_mlflow(self,
                                   symbol: str,
                                   models: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compare models using MLflow data.
        
        Args:
            symbol: Trading symbol
            models: List of model names (None = all)
        
        Returns:
            Comparison DataFrame
        """
        return self.tracker.compare_models(symbol=symbol, models=models)

    def generate_experiment_report(self, output_dir: str = "reports"):
        """
        Generate comprehensive experiment report.
        
        Args:
            output_dir: Directory to save report
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print("📊 Generating Experiment Report")
        print(f"{'='*60}")

        # Export all data
        df = self.tracker.export_experiment_data(output_dir=str(output_path))

        # Generate leaderboard
        print("\n🏆 Overall Leaderboard:")
        leaderboard = self.tracker.generate_leaderboard(metric='sharpe_ratio', top_n=10)

        # Save leaderboard
        leaderboard_file = output_path / f"leaderboard_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        leaderboard.to_csv(leaderboard_file, index=False)

        # Generate statistics
        if not df.empty and 'sharpe_ratio' in df.columns:
            stats = {
                'Total Experiments': len(df),
                'Avg Sharpe': df['sharpe_ratio'].mean(),
                'Max Sharpe': df['sharpe_ratio'].max(),
                'Min Sharpe': df['sharpe_ratio'].min(),
                'Std Sharpe': df['sharpe_ratio'].std(),
            }

            print("\n📈 Statistics:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")

            # Save stats
            stats_file = output_path / f"statistics_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)

            print(f"\n✅ Report generated in: {output_path}")
            print(f"   - Leaderboard: {leaderboard_file.name}")
            print(f"   - Statistics: {stats_file.name}")

        return df

    def get_best_models_per_symbol(self) -> pd.DataFrame:
        """
        Get the best performing model for each symbol.
        
        Returns:
            DataFrame with best model per symbol
        """
        # Export all data
        df = self.tracker.export_experiment_data()

        if df.empty or 'sharpe_ratio' not in df.columns:
            return pd.DataFrame()

        # Filter backtest runs
        df = df[df.get('type', '') == 'backtest'].copy()

        # Get best per symbol
        best_models = df.loc[df.groupby('symbol')['sharpe_ratio'].idxmax()]

        result = best_models[['symbol', 'model', 'sharpe_ratio', 'total_return',
                             'win_rate', 'max_drawdown']].copy()

        print(f"\n{'='*60}")
        print("⭐ Best Model Per Symbol")
        print(f"{'='*60}")
        print(result.to_string(index=False))

        return result

    def start_mlflow_ui(self, port: int = 5000):
        """
        Start MLflow UI server.
        
        Args:
            port: Port to run UI on
        """
        import subprocess

        print(f"\n{'='*60}")
        print("🚀 Starting MLflow UI")
        print(f"{'='*60}")
        print(f"\nURL: http://localhost:{port}")
        print(f"Experiment: {self.experiment_name}")
        print("\nPress Ctrl+C to stop the server\n")

        try:
            subprocess.run([
                'mlflow', 'ui',
                '--backend-store-uri', './mlruns',
                '--port', str(port)
            ])
        except KeyboardInterrupt:
            print("\n\n✅ MLflow UI stopped")


def main():
    """Example usage."""
    print("\n" + "="*60)
    print("🚀 CRISPR MLflow Integration - Demo")
    print("="*60)

    # Initialize integration
    integration = CRISPRMLflowIntegration(
        experiment_name="CRISPR-FinAI-Integration-Demo"
    )

    # Example 1: Single comprehensive run
    print("\n1️⃣  Single Comprehensive Run & Track")
    result = integration.run_and_track_comprehensive(
        symbol="AAPL",
        model="naive_momentum",
        parameters={'lookback': 20},
        tags={'version': 'v1.0', 'test': 'demo'}
    )

    # Example 2: Batch processing (limited for demo)
    print("\n2️⃣  Batch Processing (first 3 models)")
    summary = integration.batch_run_and_track(max_runs=3)

    # Example 3: Generate leaderboard
    print("\n3️⃣  Generate Leaderboard")
    integration.tracker.generate_leaderboard(top_n=5)

    # Example 4: Generate report
    print("\n4️⃣  Generate Experiment Report")
    integration.generate_experiment_report()

    # Example 5: Best models per symbol
    print("\n5️⃣  Best Models Per Symbol")
    integration.get_best_models_per_symbol()

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("\n💡 To view results in MLflow UI:")
    print("   python -c 'from core.mlflow_integration import CRISPRMLflowIntegration; "
          "CRISPRMLflowIntegration().start_mlflow_ui()'")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
