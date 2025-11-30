"""
Real-time Performance Monitoring System
Provides live updates on model performance, drift detection, and system health.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import websockets
from websockets.server import serve

@dataclass
class PerformanceMetric:
    """Real-time performance metric snapshot."""
    timestamp: str
    symbol: str
    model: str
    sharpe_ratio: float
    returns: float
    volatility: float
    drawdown: float
    drift_score: float
    trade_count: int
    win_rate: float
    status: str  # 'normal', 'drift', 'healing', 'healed'

    def to_dict(self) -> Dict:
        return asdict(self)


class PerformanceMonitor:
    """Monitors model performance in real-time and detects anomalies."""

    def __init__(self, data_dir: str = 'poc/scale_results_quick'):
        self.data_dir = Path(data_dir)
        self.metrics_history: List[PerformanceMetric] = []
        self.active_models: Dict[str, Dict] = {}
        self.drift_threshold = 0.3
        self.check_interval = 5  # seconds
        self.websocket_clients = set()

    def load_current_state(self) -> None:
        """Load current performance state from results."""
        results_file = self.data_dir / 'scale_compare_results.csv'
        if not results_file.exists():
            print(f"⚠️  Results file not found: {results_file}")
            return

        df = pd.read_csv(results_file)

        for _, row in df.iterrows():
            model_key = f"{row['symbol']}_{row['model']}"
            self.active_models[model_key] = {
                'symbol': row['symbol'],
                'model': row['model'],
                'sharpe': row['sharpe'],
                'volatility': row['volatility'],
                'win_rate': row['win_rate'],
                'last_update': datetime.now().isoformat()
            }

        print(f"✅ Loaded {len(self.active_models)} active models")

    def calculate_drift(self, current_sharpe: float, baseline_sharpe: float) -> float:
        """Calculate performance drift score."""
        if baseline_sharpe == 0:
            return 0.0
        return abs((current_sharpe - baseline_sharpe) / baseline_sharpe)

    def simulate_live_performance(self, symbol: str, model: str) -> PerformanceMetric:
        """Simulate live performance update (would connect to real trading in production)."""
        model_key = f"{symbol}_{model}"

        if model_key not in self.active_models:
            # Initialize with default values
            base_sharpe = np.random.uniform(0.5, 1.5)
            self.active_models[model_key] = {
                'symbol': symbol,
                'model': model,
                'sharpe': base_sharpe,
                'volatility': 0.15,
                'win_rate': 0.55,
                'last_update': datetime.now().isoformat()
            }

        model_data = self.active_models[model_key]

        # Simulate small variations
        noise = np.random.normal(0, 0.02)
        current_sharpe = model_data['sharpe'] + noise
        drift_score = self.calculate_drift(current_sharpe, model_data['sharpe'])

        # Determine status
        if drift_score > self.drift_threshold:
            status = 'drift'
        elif drift_score > self.drift_threshold * 0.5:
            status = 'healing'
        else:
            status = 'normal'

        # Simulate returns and drawdown
        returns = np.random.normal(0.001, 0.02)  # Daily return
        drawdown = np.random.uniform(-0.15, -0.05)

        metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            model=model,
            sharpe_ratio=current_sharpe,
            returns=returns * 100,  # Convert to percentage
            volatility=model_data['volatility'],
            drawdown=drawdown * 100,
            drift_score=drift_score,
            trade_count=np.random.randint(10, 50),
            win_rate=model_data['win_rate'],
            status=status
        )

        self.metrics_history.append(metric)

        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

        return metric

    def get_system_health(self) -> Dict:
        """Get overall system health metrics."""
        if not self.metrics_history:
            return {
                'status': 'unknown',
                'models_healthy': 0,
                'models_drifting': 0,
                'total_models': 0,
                'avg_sharpe': 0.0,
                'timestamp': datetime.now().isoformat()
            }

        recent_metrics = self.metrics_history[-len(self.active_models):]

        healthy = sum(1 for m in recent_metrics if m.status == 'normal')
        drifting = sum(1 for m in recent_metrics if m.status == 'drift')
        avg_sharpe = np.mean([m.sharpe_ratio for m in recent_metrics])

        overall_status = 'healthy' if drifting == 0 else 'warning' if drifting < 3 else 'critical'

        return {
            'status': overall_status,
            'models_healthy': healthy,
            'models_drifting': drifting,
            'total_models': len(self.active_models),
            'avg_sharpe': float(avg_sharpe),
            'timestamp': datetime.now().isoformat()
        }

    def get_recent_metrics(self, symbol: Optional[str] = None,
                          model: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """Get recent performance metrics."""
        metrics = self.metrics_history[-limit:]

        if symbol:
            metrics = [m for m in metrics if m.symbol == symbol]
        if model:
            metrics = [m for m in metrics if m.model == model]

        return [m.to_dict() for m in metrics]

    async def broadcast_update(self, data: Dict) -> None:
        """Broadcast update to all connected WebSocket clients."""
        if not self.websocket_clients:
            return

        message = json.dumps(data)
        disconnected = set()

        for websocket in self.websocket_clients:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)

        # Remove disconnected clients
        self.websocket_clients -= disconnected

    async def monitor_loop(self) -> None:
        """Main monitoring loop that generates updates."""
        print("🔄 Starting monitoring loop...")

        while True:
            try:
                # Update all models
                updates = []
                for model_key, model_data in self.active_models.items():
                    metric = self.simulate_live_performance(
                        model_data['symbol'],
                        model_data['model']
                    )
                    updates.append(metric.to_dict())

                # Broadcast updates
                health = self.get_system_health()
                await self.broadcast_update({
                    'type': 'performance_update',
                    'metrics': updates,
                    'health': health,
                    'timestamp': datetime.now().isoformat()
                })

                # Log status
                if len(updates) > 0:
                    drift_count = sum(1 for u in updates if u['status'] == 'drift')
                    if drift_count > 0:
                        print(f"⚠️  {drift_count} models drifting - Health: {health['status']}")

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(1)

    async def websocket_handler(self, websocket, path) -> None:
        """Handle WebSocket connections."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        print(f"🔌 Client connected: {client_id}")

        self.websocket_clients.add(websocket)

        # Send initial state
        initial_data = {
            'type': 'initial_state',
            'models': list(self.active_models.values()),
            'health': self.get_system_health(),
            'recent_metrics': self.get_recent_metrics(limit=50)
        }
        await websocket.send(json.dumps(initial_data))

        try:
            async for message in websocket:
                # Handle client requests
                try:
                    request = json.loads(message)
                    response = await self.handle_request(request)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'error': 'Invalid JSON'
                    }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.websocket_clients.remove(websocket)
            print(f"🔌 Client disconnected: {client_id}")

    async def handle_request(self, request: Dict) -> Dict:
        """Handle client requests."""
        action = request.get('action')

        if action == 'get_metrics':
            symbol = request.get('symbol')
            model = request.get('model')
            limit = request.get('limit', 100)

            return {
                'type': 'metrics_response',
                'metrics': self.get_recent_metrics(symbol, model, limit)
            }

        if action == 'get_health':
            return {
                'type': 'health_response',
                'health': self.get_system_health()
            }

        if action == 'get_models':
            return {
                'type': 'models_response',
                'models': list(self.active_models.values())
            }

        return {
            'error': f'Unknown action: {action}'
        }

    async def start_server(self, host: str = 'localhost', port: int = 8765) -> None:
        """Start the WebSocket server."""
        print(f"\n{'='*60}")
        print("🚀 Starting Real-time Performance Monitor")
        print(f"{'='*60}\n")

        self.load_current_state()

        # Start monitoring loop
        monitor_task = asyncio.create_task(self.monitor_loop())

        # Start WebSocket server
        print(f"🌐 WebSocket server starting on ws://{host}:{port}")
        print(f"📊 Monitoring {len(self.active_models)} models")
        print(f"⏱️  Update interval: {self.check_interval}s")
        print(f"\n{'='*60}")
        print("✅ Server ready! Connect with WebSocket client")
        print(f"{'='*60}\n")

        async with serve(self.websocket_handler, host, port):
            await monitor_task  # Run forever


def main():
    """Main entry point."""
    monitor = PerformanceMonitor()

    try:
        asyncio.run(monitor.start_server())
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down monitor...")
        print("✅ Monitor stopped successfully")


if __name__ == '__main__':
    main()
