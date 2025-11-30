"""
🗃️ Dashboard Data Layer

Data management and caching system for CRISPR-FinAI dashboard.
Handles real-time data streams, historical data, and performance metrics.

From raw metrics to structured insights.
"""

import numpy as np
import sqlite3
import json
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging
import threading
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """📊 Performance metric data structure."""
    timestamp: datetime
    value: float
    metric_type: str
    category: str
    metadata: Dict[str, Any] = None


@dataclass
class SystemEvent:
    """🎯 System event data structure."""
    timestamp: datetime
    event_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    component: str
    data: Dict[str, Any] = None


@dataclass
class GenomeSnapshot:
    """🧬 Genome state snapshot."""
    timestamp: datetime
    genome_id: str
    parameters: Dict[str, Any]
    fitness_score: float
    health_metrics: Dict[str, float]
    edit_count: int


class DataCache:
    """
    💾 High-Performance Data Cache
    
    Multi-layered caching system with automatic expiration and
    memory-efficient storage for dashboard data.
    """

    def __init__(self, max_memory_mb: int = 100):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = {}
        self.metadata = {}
        self.access_times = {}
        self.lock = threading.RLock()

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self.lock:
            if key in self.cache:
                meta = self.metadata[key]

                # Check expiration
                if datetime.now() > meta['expires_at']:
                    self._remove(key)
                    self.misses += 1
                    return None

                # Update access time
                self.access_times[key] = datetime.now()
                self.hits += 1
                return self.cache[key]

            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set item in cache with TTL."""
        with self.lock:
            # Estimate memory usage
            try:
                estimated_size = len(pickle.dumps(value))
            except Exception:
                estimated_size = 1024  # Default estimate

            # Ensure we have space
            self._ensure_space(estimated_size)

            # Store item
            self.cache[key] = value
            self.metadata[key] = {
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=ttl_seconds),
                'size_bytes': estimated_size,
                'access_count': 0
            }
            self.access_times[key] = datetime.now()

    def _ensure_space(self, needed_bytes: int):
        """Ensure sufficient cache space."""
        current_size = sum(meta['size_bytes'] for meta in self.metadata.values())

        if current_size + needed_bytes <= self.max_memory_bytes:
            return

        # Evict least recently used items
        items_by_access = sorted(
            self.access_times.items(),
            key=lambda x: x[1]
        )

        for key, _ in items_by_access:
            if current_size + needed_bytes <= self.max_memory_bytes:
                break

            current_size -= self.metadata[key]['size_bytes']
            self._remove(key)
            self.evictions += 1

    def _remove(self, key: str):
        """Remove item from cache."""
        if key in self.cache:
            del self.cache[key]
            del self.metadata[key]
            del self.access_times[key]

    def clear(self):
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
            self.metadata.clear()
            self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        current_size = sum(meta['size_bytes'] for meta in self.metadata.values())

        return {
            'hit_rate': hit_rate,
            'total_items': len(self.cache),
            'memory_usage_mb': current_size / (1024 * 1024),
            'memory_usage_percent': (current_size / self.max_memory_bytes) * 100,
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions
        }


class TimeSeriesBuffer:
    """
    📈 Real-Time Time Series Buffer
    
    Efficient circular buffer for real-time time series data with
    automatic aggregation and downsampling capabilities.
    """

    def __init__(self, max_size: int = 10000, auto_aggregate: bool = True):
        self.max_size = max_size
        self.auto_aggregate = auto_aggregate
        self.data = deque(maxlen=max_size)
        self.lock = threading.RLock()

        # Aggregated views
        self.minute_data = deque(maxlen=1440)  # 24 hours of minute data
        self.hour_data = deque(maxlen=168)     # 7 days of hour data
        self.day_data = deque(maxlen=365)      # 1 year of day data

        self.last_minute_aggregate = None
        self.last_hour_aggregate = None
        self.last_day_aggregate = None

    def append(self, timestamp: datetime, value: float, metadata: Dict = None):
        """Append new data point."""
        with self.lock:
            data_point = {
                'timestamp': timestamp,
                'value': value,
                'metadata': metadata or {}
            }

            self.data.append(data_point)

            if self.auto_aggregate:
                self._update_aggregates(data_point)

    def _update_aggregates(self, data_point: Dict):
        """Update aggregated views."""
        timestamp = data_point['timestamp']
        value = data_point['value']

        # Minute aggregation
        minute_key = timestamp.replace(second=0, microsecond=0)
        if self.last_minute_aggregate != minute_key:
            if self.last_minute_aggregate and self.minute_data:
                # Finalize previous minute
                prev_minute_data = [
                    p for p in self.data
                    if p['timestamp'].replace(second=0, microsecond=0) == self.last_minute_aggregate
                ]
                if prev_minute_data:
                    self._finalize_minute_aggregate(self.last_minute_aggregate, prev_minute_data)

            self.last_minute_aggregate = minute_key

        # Similar logic for hour and day aggregation...

    def _finalize_minute_aggregate(self, minute_key: datetime, data_points: List[Dict]):
        """Finalize minute aggregate."""
        values = [p['value'] for p in data_points]

        aggregate = {
            'timestamp': minute_key,
            'open': values[0],
            'high': max(values),
            'low': min(values),
            'close': values[-1],
            'mean': np.mean(values),
            'count': len(values),
            'std': np.std(values) if len(values) > 1 else 0
        }

        self.minute_data.append(aggregate)

    def get_recent(self, n: int = 100) -> List[Dict]:
        """Get recent data points."""
        with self.lock:
            return list(self.data)[-n:]

    def get_range(self, start: datetime, end: datetime) -> List[Dict]:
        """Get data points in time range."""
        with self.lock:
            return [
                p for p in self.data
                if start <= p['timestamp'] <= end
            ]

    def get_aggregated(self, resolution: str = 'minute') -> List[Dict]:
        """Get aggregated data."""
        with self.lock:
            if resolution == 'minute':
                return list(self.minute_data)
            if resolution == 'hour':
                return list(self.hour_data)
            if resolution == 'day':
                return list(self.day_data)
            raise ValueError(f"Invalid resolution: {resolution}")


class DatabaseManager:
    """
    🗄️ Dashboard Database Manager
    
    SQLite-based persistent storage for dashboard data with
    optimized schemas and query performance.
    """

    def __init__(self, db_path: str = "crispr_dashboard.db"):
        self.db_path = Path(db_path)
        self.connection_pool = {}
        self.lock = threading.RLock()

        self._initialize_database()

    def _initialize_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    metadata TEXT,
                    INDEX(timestamp),
                    INDEX(metric_type),
                    INDEX(category)
                )
            """)

            # System events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    component TEXT NOT NULL,
                    data TEXT,
                    INDEX(timestamp),
                    INDEX(event_type),
                    INDEX(severity)
                )
            """)

            # Genome snapshots table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS genome_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    genome_id TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    fitness_score REAL NOT NULL,
                    health_metrics TEXT NOT NULL,
                    edit_count INTEGER NOT NULL,
                    INDEX(timestamp),
                    INDEX(genome_id)
                )
            """)

            conn.commit()

    def store_performance_metric(self, metric: PerformanceMetric):
        """Store performance metric."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_metrics 
                (timestamp, value, metric_type, category, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metric.timestamp.timestamp(),
                metric.value,
                metric.metric_type,
                metric.category,
                json.dumps(metric.metadata) if metric.metadata else None
            ))
            conn.commit()

    def store_system_event(self, event: SystemEvent):
        """Store system event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO system_events 
                (timestamp, event_type, severity, message, component, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp.timestamp(),
                event.event_type,
                event.severity,
                event.message,
                event.component,
                json.dumps(event.data) if event.data else None
            ))
            conn.commit()

    def store_genome_snapshot(self, snapshot: GenomeSnapshot):
        """Store genome snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO genome_snapshots 
                (timestamp, genome_id, parameters, fitness_score, health_metrics, edit_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp.timestamp(),
                snapshot.genome_id,
                json.dumps(snapshot.parameters),
                snapshot.fitness_score,
                json.dumps(snapshot.health_metrics),
                snapshot.edit_count
            ))
            conn.commit()

    def get_performance_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        metric_types: Optional[List[str]] = None
    ) -> List[PerformanceMetric]:
        """Get performance metrics in time range."""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT timestamp, value, metric_type, category, metadata
                FROM performance_metrics 
                WHERE timestamp BETWEEN ? AND ?
            """
            params = [start_time.timestamp(), end_time.timestamp()]

            if metric_types:
                placeholders = ','.join(['?'] * len(metric_types))
                query += f" AND metric_type IN ({placeholders})"
                params.extend(metric_types)

            query += " ORDER BY timestamp"

            cursor = conn.execute(query, params)
            results = []

            for row in cursor:
                results.append(PerformanceMetric(
                    timestamp=datetime.fromtimestamp(row[0]),
                    value=row[1],
                    metric_type=row[2],
                    category=row[3],
                    metadata=json.loads(row[4]) if row[4] else None
                ))

            return results

    def get_recent_events(self, limit: int = 100) -> List[SystemEvent]:
        """Get recent system events."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, event_type, severity, message, component, data
                FROM system_events 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor:
                results.append(SystemEvent(
                    timestamp=datetime.fromtimestamp(row[0]),
                    event_type=row[1],
                    severity=row[2],
                    message=row[3],
                    component=row[4],
                    data=json.loads(row[5]) if row[5] else None
                ))

            return results

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to maintain database size."""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)

        with sqlite3.connect(self.db_path) as conn:
            # Clean old performance metrics
            conn.execute(
                "DELETE FROM performance_metrics WHERE timestamp < ?",
                (cutoff_time.timestamp(),)
            )

            # Clean old events (keep critical events longer)
            conn.execute("""
                DELETE FROM system_events 
                WHERE timestamp < ? AND severity NOT IN ('critical', 'high')
            """, (cutoff_time.timestamp(),))

            # Clean old genome snapshots (keep every 10th snapshot for history)
            conn.execute("""
                DELETE FROM genome_snapshots 
                WHERE timestamp < ? AND id % 10 != 0
            """, (cutoff_time.timestamp(),))

            # Vacuum database to reclaim space
            conn.execute("VACUUM")
            conn.commit()


class DashboardDataManager:
    """
    📊 Main Dashboard Data Manager
    
    Coordinates all data operations including caching, real-time streams,
    persistence, and data aggregation for the dashboard.
    """

    def __init__(self, cache_size_mb: int = 100, db_path: str = "crispr_dashboard.db"):
        self.cache = DataCache(cache_size_mb)
        self.db = DatabaseManager(db_path)

        # Real-time buffers
        self.buffers = {
            'portfolio_value': TimeSeriesBuffer(),
            'pnl': TimeSeriesBuffer(),
            'risk_metrics': TimeSeriesBuffer(),
            'anomaly_scores': TimeSeriesBuffer(),
            'system_health': TimeSeriesBuffer()
        }

        # Data aggregation
        self.aggregated_data = defaultdict(dict)
        self.last_aggregation = {}

        # Background tasks
        self.background_tasks = []
        self.shutdown_event = threading.Event()

        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background data processing tasks."""
        # Data aggregation task
        aggregation_task = threading.Thread(
            target=self._aggregation_worker,
            daemon=True
        )
        aggregation_task.start()
        self.background_tasks.append(aggregation_task)

        # Database cleanup task
        cleanup_task = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        cleanup_task.start()
        self.background_tasks.append(cleanup_task)

    def _aggregation_worker(self):
        """Background worker for data aggregation."""
        while not self.shutdown_event.wait(60):  # Run every minute
            try:
                self._aggregate_performance_data()
                self._update_dashboard_metrics()
            except Exception as e:
                logger.error(f"Aggregation worker error: {str(e)}")

    def _cleanup_worker(self):
        """Background worker for data cleanup."""
        while not self.shutdown_event.wait(3600):  # Run every hour
            try:
                self.db.cleanup_old_data()
                self.cache.clear()  # Periodic cache clearing
            except Exception as e:
                logger.error(f"Cleanup worker error: {str(e)}")

    def _aggregate_performance_data(self):
        """Aggregate performance data for dashboard."""
        now = datetime.now()

        # Aggregate data for different time periods
        for period in ['1h', '6h', '24h', '7d', '30d']:
            if period in self.last_aggregation:
                if (now - self.last_aggregation[period]).total_seconds() < 300:  # 5 min cache
                    continue

            start_time = self._get_period_start(now, period)

            # Get metrics from database
            metrics = self.db.get_performance_metrics(start_time, now)

            if metrics:
                aggregated = self._compute_aggregations(metrics)
                self.aggregated_data[period] = aggregated
                self.last_aggregation[period] = now

    def _get_period_start(self, end_time: datetime, period: str) -> datetime:
        """Get start time for aggregation period."""
        if period == '1h':
            return end_time - timedelta(hours=1)
        if period == '6h':
            return end_time - timedelta(hours=6)
        if period == '24h':
            return end_time - timedelta(days=1)
        if period == '7d':
            return end_time - timedelta(days=7)
        if period == '30d':
            return end_time - timedelta(days=30)
        return end_time - timedelta(hours=1)

    def _compute_aggregations(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Compute aggregations from metrics."""
        # Group by metric type
        by_type = defaultdict(list)
        for metric in metrics:
            by_type[metric.metric_type].append(metric.value)

        aggregated = {}
        for metric_type, values in by_type.items():
            if values:
                aggregated[metric_type] = {
                    'count': len(values),
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': min(values),
                    'max': max(values),
                    'latest': values[-1]
                }

        return aggregated

    def _update_dashboard_metrics(self):
        """Update cached dashboard metrics."""
        # Calculate key dashboard metrics
        key_metrics = {
            'system_uptime': self._calculate_uptime(),
            'total_operations': self._count_total_operations(),
            'error_rate': self._calculate_error_rate(),
            'performance_summary': self._get_performance_summary()
        }

        self.cache.set('dashboard_metrics', key_metrics, ttl_seconds=300)

    def _calculate_uptime(self) -> float:
        """Calculate system uptime in seconds."""
        # This would be implemented based on actual system start time
        return 86400.0  # Placeholder: 24 hours

    def _count_total_operations(self) -> int:
        """Count total system operations."""
        # This would query actual operation counts
        return 1247  # Placeholder

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        # This would be based on recent error events
        return 0.023  # Placeholder: 2.3%

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary metrics."""
        return {
            'daily_return': 0.0234,
            'sharpe_ratio': 1.47,
            'max_drawdown': -0.083,
            'win_rate': 0.642
        }

    # Public interface methods

    def add_performance_metric(self, metric: PerformanceMetric):
        """Add performance metric to system."""
        # Store in database
        self.db.store_performance_metric(metric)

        # Add to real-time buffer if applicable
        if metric.metric_type in self.buffers:
            self.buffers[metric.metric_type].append(
                metric.timestamp,
                metric.value,
                asdict(metric)
            )

    def add_system_event(self, event: SystemEvent):
        """Add system event."""
        self.db.store_system_event(event)

    def add_genome_snapshot(self, snapshot: GenomeSnapshot):
        """Add genome snapshot."""
        self.db.store_genome_snapshot(snapshot)

    def get_dashboard_data(self, period: str = '24h') -> Dict[str, Any]:
        """Get dashboard data for specified period."""
        # Check cache first
        cache_key = f"dashboard_data_{period}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data

        # Build dashboard data
        dashboard_data = {
            'aggregated_metrics': self.aggregated_data.get(period, {}),
            'recent_events': self.db.get_recent_events(50),
            'real_time_data': self._get_real_time_data(),
            'cache_stats': self.cache.get_stats(),
            'system_status': self.cache.get('dashboard_metrics') or {}
        }

        # Cache the result
        self.cache.set(cache_key, dashboard_data, ttl_seconds=60)

        return dashboard_data

    def _get_real_time_data(self) -> Dict[str, Any]:
        """Get current real-time data."""
        real_time = {}
        for name, buffer in self.buffers.items():
            recent_data = buffer.get_recent(100)
            if recent_data:
                real_time[name] = {
                    'latest_value': recent_data[-1]['value'],
                    'latest_timestamp': recent_data[-1]['timestamp'],
                    'data_points': len(recent_data)
                }

        return real_time

    def shutdown(self):
        """Shutdown data manager."""
        self.shutdown_event.set()

        for task in self.background_tasks:
            task.join(timeout=5)


# Export classes
__all__ = [
    'PerformanceMetric',
    'SystemEvent',
    'GenomeSnapshot',
    'DataCache',
    'TimeSeriesBuffer',
    'DatabaseManager',
    'DashboardDataManager'
]
