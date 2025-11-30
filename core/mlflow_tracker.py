"""
MLflow Experiment Tracking for CRISPR-FinAI
Comprehensive experiment management, model versioning, and artifact storage.
"""

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class CRISPRMLflowTracker:
    """
    MLflow integration for CRISPR-FinAI experiment tracking.
    """

    def __init__(self,
                 experiment_name: str = "CRISPR-FinAI",
                 tracking_uri: str = "mlruns",
                 artifact_location: Optional[str] = None):
        """
        Initialize MLflow tracker.
        
        Args:
            experiment_name: Name of the MLflow experiment
            tracking_uri: MLflow tracking server URI or local path
            artifact_location: Custom artifact storage location
        """
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri

        # Set tracking URI
        mlflow.set_tracking_uri(tracking_uri)

        # Get or create experiment
        try:
            self.experiment_id = mlflow.create_experiment(
                experiment_name,
                artifact_location=artifact_location
            )
            print(f"✅ Created new experiment: {experiment_name}")
        except Exception:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            self.experiment_id = experiment.experiment_id
            print(f"✅ Using existing experiment: {experiment_name}")

        mlflow.set_experiment(experiment_name)
        self.client = MlflowClient()

    def log_backtest_run(self,
                        symbol: str,
                        model_name: str,
                        backtest_results: Dict[str, Any],
                        parameters: Optional[Dict[str, Any]] = None,
                        tags: Optional[Dict[str, str]] = None,
                        artifacts: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a backtest run to MLflow.
        
        Args:
            symbol: Trading symbol
            model_name: Model name
            backtest_results: Dictionary with backtest metrics
            parameters: Model/strategy parameters
            tags: Additional tags
            artifacts: Files to log as artifacts
        
        Returns:
            run_id: MLflow run ID
        """
        with mlflow.start_run(run_name=f"{symbol}_{model_name}") as run:
            run_id = run.info.run_id

            # Log parameters
            if parameters:
                for key, value in parameters.items():
                    mlflow.log_param(key, value)

            # Log default parameters
            mlflow.log_param("symbol", symbol)
            mlflow.log_param("model", model_name)
            mlflow.log_param("timestamp", datetime.now().isoformat())

            # Log metrics
            metrics_to_log = {
                'sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
                'sortino_ratio': backtest_results.get('sortino_ratio', 0),
                'calmar_ratio': backtest_results.get('calmar_ratio', 0),
                'total_return': backtest_results.get('total_return', 0),
                'annual_return': backtest_results.get('annual_return', 0),
                'max_drawdown': backtest_results.get('max_drawdown', 0),
                'volatility': backtest_results.get('volatility', 0),
                'win_rate': backtest_results.get('win_rate', 0),
                'profit_factor': backtest_results.get('profit_factor', 0),
                'total_trades': backtest_results.get('total_trades', 0)
            }

            for metric_name, metric_value in metrics_to_log.items():
                if metric_value is not None:
                    mlflow.log_metric(metric_name, float(metric_value))

            # Log tags
            default_tags = {
                "symbol": symbol,
                "model": model_name,
                "type": "backtest",
                "status": "completed"
            }

            if tags:
                default_tags.update(tags)

            for tag_key, tag_value in default_tags.items():
                mlflow.set_tag(tag_key, tag_value)

            # Log artifacts
            if artifacts:
                for artifact_name, artifact_data in artifacts.items():
                    self._log_artifact(artifact_name, artifact_data)

            # Log backtest results as JSON
            results_path = Path("temp_results.json")
            with open(results_path, 'w') as f:
                json.dump(backtest_results, f, indent=2, default=str)
            mlflow.log_artifact(str(results_path))
            results_path.unlink()

            print(f"✅ Logged run: {run_id}")
            print(f"   Symbol: {symbol}, Model: {model_name}")
            print(f"   Sharpe: {metrics_to_log['sharpe_ratio']:.2f}")
            print(f"   Return: {metrics_to_log['total_return']*100:.2f}%")

            return run_id

    def log_walk_forward_run(self,
                            symbol: str,
                            model_name: str,
                            wf_results: Dict[str, Any],
                            parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Log walk-forward analysis results.
        
        Args:
            symbol: Trading symbol
            model_name: Model name
            wf_results: Walk-forward results dictionary
            parameters: Strategy parameters
        
        Returns:
            run_id: MLflow run ID
        """
        with mlflow.start_run(run_name=f"{symbol}_{model_name}_walkforward") as run:
            run_id = run.info.run_id

            # Log parameters
            if parameters:
                for key, value in parameters.items():
                    mlflow.log_param(key, value)

            mlflow.log_param("symbol", symbol)
            mlflow.log_param("model", model_name)
            mlflow.log_param("analysis_type", "walk_forward")

            # Log aggregate metrics
            mlflow.log_metric("wf_periods", wf_results.get('n_periods', 0))
            mlflow.log_metric("wf_avg_sharpe", wf_results.get('avg_sharpe', 0))
            mlflow.log_metric("wf_std_sharpe", wf_results.get('std_sharpe', 0))
            mlflow.log_metric("wf_consistency", wf_results.get('consistency', 0))
            mlflow.log_metric("wf_total_return", wf_results.get('total_return', 0))

            # Log period-by-period metrics
            if 'periods' in wf_results:
                for i, period in enumerate(wf_results['periods']):
                    mlflow.log_metric(f"period_{i}_sharpe", period['sharpe_ratio'], step=i)
                    mlflow.log_metric(f"period_{i}_return", period['total_return'], step=i)

            # Set tags
            mlflow.set_tag("symbol", symbol)
            mlflow.set_tag("model", model_name)
            mlflow.set_tag("type", "walk_forward")
            mlflow.set_tag("status", "completed")

            # Log results as artifact
            results_path = Path("temp_wf_results.json")
            with open(results_path, 'w') as f:
                json.dump(wf_results, f, indent=2, default=str)
            mlflow.log_artifact(str(results_path))
            results_path.unlink()

            print(f"✅ Logged walk-forward run: {run_id}")
            print(f"   Periods: {wf_results.get('n_periods', 0)}")
            print(f"   Avg Sharpe: {wf_results.get('avg_sharpe', 0):.2f}")
            print(f"   Consistency: {wf_results.get('consistency', 0)*100:.1f}%")

            return run_id

    def log_monte_carlo_run(self,
                           symbol: str,
                           model_name: str,
                           mc_results: Dict[str, Any],
                           parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Log Monte Carlo simulation results.
        
        Args:
            symbol: Trading symbol
            model_name: Model name
            mc_results: Monte Carlo results dictionary
            parameters: Strategy parameters
        
        Returns:
            run_id: MLflow run ID
        """
        with mlflow.start_run(run_name=f"{symbol}_{model_name}_montecarlo") as run:
            run_id = run.info.run_id

            # Log parameters
            if parameters:
                for key, value in parameters.items():
                    mlflow.log_param(key, value)

            mlflow.log_param("symbol", symbol)
            mlflow.log_param("model", model_name)
            mlflow.log_param("analysis_type", "monte_carlo")
            mlflow.log_param("n_simulations", mc_results.get('n_simulations', 0))

            # Log metrics
            returns = mc_results.get('returns', {})
            sharpe = mc_results.get('sharpe', {})

            mlflow.log_metric("mc_mean_return", returns.get('mean', 0))
            mlflow.log_metric("mc_median_return", returns.get('median', 0))
            mlflow.log_metric("mc_std_return", returns.get('std', 0))
            mlflow.log_metric("mc_ci_lower", returns.get('ci_lower', 0))
            mlflow.log_metric("mc_ci_upper", returns.get('ci_upper', 0))
            mlflow.log_metric("mc_mean_sharpe", sharpe.get('mean', 0))
            mlflow.log_metric("mc_prob_positive", mc_results.get('probability_positive', 0))
            mlflow.log_metric("mc_prob_sharpe_above_1", mc_results.get('probability_sharpe_above_1', 0))

            # Set tags
            mlflow.set_tag("symbol", symbol)
            mlflow.set_tag("model", model_name)
            mlflow.set_tag("type", "monte_carlo")
            mlflow.set_tag("status", "completed")

            # Log results
            results_path = Path("temp_mc_results.json")
            with open(results_path, 'w') as f:
                # Remove large simulation arrays for artifact
                mc_summary = {k: v for k, v in mc_results.items() if k != 'all_simulations'}
                json.dump(mc_summary, f, indent=2, default=str)
            mlflow.log_artifact(str(results_path))
            results_path.unlink()

            print(f"✅ Logged Monte Carlo run: {run_id}")
            print(f"   Simulations: {mc_results.get('n_simulations', 0)}")
            print(f"   Mean Return: {returns.get('mean', 0)*100:.2f}%")
            print(f"   P(Positive): {mc_results.get('probability_positive', 0)*100:.1f}%")

            return run_id

    def log_comprehensive_experiment(self,
                                    symbol: str,
                                    model_name: str,
                                    comprehensive_results: Dict[str, Any],
                                    parameters: Optional[Dict[str, Any]] = None,
                                    tags: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Log all analysis types (simple, walk-forward, Monte Carlo) in one experiment.
        
        Args:
            symbol: Trading symbol
            model_name: Model name
            comprehensive_results: Dict with 'simple', 'walk_forward', 'monte_carlo' keys
            parameters: Strategy parameters
            tags: Additional tags
        
        Returns:
            Dictionary with run IDs for each analysis type
        """
        run_ids = {}

        # Create parent run
        with mlflow.start_run(run_name=f"{symbol}_{model_name}_comprehensive") as parent_run:
            parent_run_id = parent_run.info.run_id

            # Log parent parameters
            if parameters:
                for key, value in parameters.items():
                    mlflow.log_param(key, value)

            mlflow.log_param("symbol", symbol)
            mlflow.log_param("model", model_name)

            # Set parent tags
            default_tags = {
                "symbol": symbol,
                "model": model_name,
                "type": "comprehensive",
                "status": "completed"
            }
            if tags:
                default_tags.update(tags)

            for tag_key, tag_value in default_tags.items():
                mlflow.set_tag(tag_key, tag_value)

            # Log summary metrics from all analyses
            if 'simple' in comprehensive_results:
                simple = comprehensive_results['simple']
                mlflow.log_metric("simple_sharpe", simple.get('sharpe_ratio', 0))
                mlflow.log_metric("simple_return", simple.get('total_return', 0))

            if 'walk_forward' in comprehensive_results:
                wf = comprehensive_results['walk_forward']
                mlflow.log_metric("wf_avg_sharpe", wf.get('avg_sharpe', 0))
                mlflow.log_metric("wf_consistency", wf.get('consistency', 0))

            if 'monte_carlo' in comprehensive_results:
                mc = comprehensive_results['monte_carlo']
                mlflow.log_metric("mc_mean_return", mc['returns']['mean'])
                mlflow.log_metric("mc_prob_positive", mc.get('probability_positive', 0))

            # Log comprehensive results
            results_path = Path("temp_comprehensive.json")
            with open(results_path, 'w') as f:
                json.dump(comprehensive_results, f, indent=2, default=str)
            mlflow.log_artifact(str(results_path))
            results_path.unlink()

            run_ids['comprehensive'] = parent_run_id

            print(f"✅ Logged comprehensive experiment: {parent_run_id}")
            print(f"   Symbol: {symbol}, Model: {model_name}")
            if 'simple' in comprehensive_results:
                print(f"   Simple Sharpe: {comprehensive_results['simple'].get('sharpe_ratio', 0):.2f}")
            if 'walk_forward' in comprehensive_results:
                print(f"   WF Consistency: {comprehensive_results['walk_forward'].get('consistency', 0)*100:.1f}%")

        return run_ids

    def _log_artifact(self, name: str, data: Any):
        """Log various types of artifacts."""
        if isinstance(data, pd.DataFrame):
            path = Path(f"temp_{name}.csv")
            data.to_csv(path, index=False)
            mlflow.log_artifact(str(path))
            path.unlink()
        elif isinstance(data, (dict, list)):
            path = Path(f"temp_{name}.json")
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            mlflow.log_artifact(str(path))
            path.unlink()
        elif isinstance(data, plt.Figure):
            path = Path(f"temp_{name}.png")
            data.savefig(path, dpi=300, bbox_inches='tight')
            mlflow.log_artifact(str(path))
            path.unlink()
            plt.close(data)
        elif isinstance(data, (str, Path)):
            # Assume it's a file path
            if Path(data).exists():
                mlflow.log_artifact(str(data))

    def compare_models(self,
                      symbol: str,
                      models: List[str],
                      metric: str = 'sharpe_ratio') -> pd.DataFrame:
        """
        Compare multiple models for a symbol.
        
        Args:
            symbol: Trading symbol
            models: List of model names
            metric: Metric to compare
        
        Returns:
            DataFrame with comparison results
        """
        results = []

        # Search runs
        filter_string = f"tags.symbol = '{symbol}' and tags.type = 'backtest'"
        runs = self.client.search_runs(
            experiment_ids=[self.experiment_id],
            filter_string=filter_string,
            order_by=[f"metrics.{metric} DESC"]
        )

        for run in runs:
            model = run.data.tags.get('model', 'unknown')
            if not models or model in models:
                results.append({
                    'run_id': run.info.run_id,
                    'model': model,
                    'symbol': symbol,
                    metric: run.data.metrics.get(metric, 0),
                    'total_return': run.data.metrics.get('total_return', 0),
                    'win_rate': run.data.metrics.get('win_rate', 0),
                    'max_drawdown': run.data.metrics.get('max_drawdown', 0),
                    'timestamp': run.info.start_time
                })

        df = pd.DataFrame(results)

        if not df.empty:
            print(f"\n{'='*60}")
            print(f"📊 Model Comparison for {symbol}")
            print(f"{'='*60}")
            print(df[['model', metric, 'total_return', 'win_rate']].to_string(index=False))

        return df

    def get_best_run(self,
                    symbol: Optional[str] = None,
                    model: Optional[str] = None,
                    metric: str = 'sharpe_ratio') -> Optional[Dict]:
        """
        Get the best run based on a metric.
        
        Args:
            symbol: Optional symbol filter
            model: Optional model filter
            metric: Metric to optimize
        
        Returns:
            Dictionary with best run information
        """
        filter_parts = ["tags.type = 'backtest'"]

        if symbol:
            filter_parts.append(f"tags.symbol = '{symbol}'")
        if model:
            filter_parts.append(f"tags.model = '{model}'")

        filter_string = " and ".join(filter_parts)

        runs = self.client.search_runs(
            experiment_ids=[self.experiment_id],
            filter_string=filter_string,
            order_by=[f"metrics.{metric} DESC"],
            max_results=1
        )

        if not runs:
            return None

        best_run = runs[0]

        return {
            'run_id': best_run.info.run_id,
            'symbol': best_run.data.tags.get('symbol'),
            'model': best_run.data.tags.get('model'),
            'metrics': best_run.data.metrics,
            'parameters': best_run.data.params,
            'timestamp': best_run.info.start_time
        }

    def generate_leaderboard(self,
                           metric: str = 'sharpe_ratio',
                           top_n: int = 10) -> pd.DataFrame:
        """
        Generate leaderboard of best performing models.
        
        Args:
            metric: Metric to rank by
            top_n: Number of top results
        
        Returns:
            DataFrame with leaderboard
        """
        runs = self.client.search_runs(
            experiment_ids=[self.experiment_id],
            filter_string="tags.type = 'backtest'",
            order_by=[f"metrics.{metric} DESC"],
            max_results=top_n
        )

        leaderboard = []
        for rank, run in enumerate(runs, 1):
            leaderboard.append({
                'Rank': rank,
                'Symbol': run.data.tags.get('symbol', 'N/A'),
                'Model': run.data.tags.get('model', 'N/A'),
                metric: run.data.metrics.get(metric, 0),
                'Total Return': run.data.metrics.get('total_return', 0) * 100,
                'Win Rate': run.data.metrics.get('win_rate', 0) * 100,
                'Max DD': run.data.metrics.get('max_drawdown', 0) * 100,
                'Run ID': run.info.run_id[:8] + '...'
            })

        df = pd.DataFrame(leaderboard)

        print(f"\n{'='*80}")
        print(f"🏆 LEADERBOARD - Top {top_n} by {metric}")
        print(f"{'='*80}")
        print(df.to_string(index=False))

        return df

    def export_experiment_data(self, output_dir: str = "mlflow_exports"):
        """
        Export all experiment data to CSV files.
        
        Args:
            output_dir: Directory to save exports
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get all runs
        runs = self.client.search_runs(
            experiment_ids=[self.experiment_id],
            order_by=["start_time DESC"]
        )

        # Extract data
        data = []
        for run in runs:
            row = {
                'run_id': run.info.run_id,
                'status': run.info.status,
                'start_time': run.info.start_time,
                **run.data.params,
                **run.data.metrics,
                **run.data.tags
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Save to CSV
        output_file = output_path / f"experiment_{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)

        print(f"✅ Exported {len(df)} runs to: {output_file}")

        return df


def main():
    """Example usage of MLflow tracker."""
    print("\n" + "="*60)
    print("🚀 MLflow Experiment Tracking - Demo")
    print("="*60)

    # Initialize tracker
    tracker = CRISPRMLflowTracker(
        experiment_name="CRISPR-FinAI-Demo",
        tracking_uri="./mlruns"
    )

    # Example 1: Log simple backtest
    print("\n1️⃣  Logging Simple Backtest...")
    backtest_results = {
        'sharpe_ratio': 2.45,
        'sortino_ratio': 3.12,
        'total_return': 0.856,
        'annual_return': 0.425,
        'max_drawdown': -0.145,
        'volatility': 0.173,
        'win_rate': 0.625,
        'profit_factor': 2.34,
        'total_trades': 87
    }

    run_id = tracker.log_backtest_run(
        symbol="AAPL",
        model_name="naive_momentum",
        backtest_results=backtest_results,
        parameters={'lookback': 20, 'threshold': 0.001},
        tags={'version': 'v1.0', 'environment': 'test'}
    )

    # Example 2: Log walk-forward
    print("\n2️⃣  Logging Walk-Forward Analysis...")
    wf_results = {
        'n_periods': 8,
        'avg_sharpe': 2.15,
        'std_sharpe': 0.45,
        'consistency': 0.875,
        'total_return': 0.645,
        'periods': [
            {'sharpe_ratio': 2.3, 'total_return': 0.12},
            {'sharpe_ratio': 1.9, 'total_return': 0.08}
        ]
    }

    tracker.log_walk_forward_run(
        symbol="GOOGL",
        model_name="mean_reversion",
        wf_results=wf_results,
        parameters={'window': 30, 'z_score': 2.0}
    )

    # Example 3: Generate leaderboard
    print("\n3️⃣  Generating Leaderboard...")
    leaderboard = tracker.generate_leaderboard(metric='sharpe_ratio', top_n=5)

    # Example 4: Export data
    print("\n4️⃣  Exporting Experiment Data...")
    tracker.export_experiment_data()

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("📁 View results: mlflow ui --backend-store-uri ./mlruns")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
