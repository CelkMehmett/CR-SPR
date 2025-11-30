# 🧬 CRISPR-FinAI Advanced Dashboard

> **Bio-Inspired Financial Intelligence Visualization Platform**  
> Real-time monitoring and analysis dashboard for the CRISPR-FinAI system

![Dashboard Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-orange)

## 🚀 Quick Start

### Launch Full Dashboard
```bash
# From project root
python -m src.dashboard.launcher

# Or directly with Streamlit
streamlit run src/dashboard/streamlit_app.py
```

### Launch Mobile Dashboard
```bash
streamlit run src/dashboard/mobile_app.py --server.port=8502
```

### Python API
```python
from src.dashboard import launch_dashboard, launch_mobile_dashboard

# Launch full dashboard
launch_dashboard(config_path="config.json", port=8501)

# Launch mobile interface
launch_mobile_dashboard(port=8502)
```

## 📊 Dashboard Features

### 🖥️ **Main Dashboard (Desktop)**
- **Real-time Performance Monitoring**: Live portfolio metrics, P&L tracking
- **Genome Analysis**: Interactive parameter heatmaps and evolution charts
- **Deep Learning Insights**: Neural network performance and anomaly detection
- **Risk Analytics**: Correlation matrices, VaR analysis, drawdown visualization
- **System Health**: Real-time system status and operational metrics

### 📱 **Mobile Dashboard**
- **Touch-Optimized Interface**: Mobile-first responsive design
- **Live Monitoring**: Essential metrics and alerts on mobile devices
- **Quick Actions**: Emergency controls and system management
- **Push Notifications**: Real-time alerts and system events

### 🎨 **Visualization Components**
- **Bio-Inspired Color Themes**: DNA/RNA-based color palette
- **Interactive Charts**: Plotly-powered dynamic visualizations
- **Scientific Aesthetics**: Publication-ready chart styling
- **Performance Optimized**: Efficient rendering for large datasets

## 🏗️ Architecture

```
📊 Dashboard Architecture
├── 🖥️ Presentation Layer (Streamlit)
│   ├── Main Dashboard (streamlit_app.py)
│   ├── Mobile Interface (mobile_app.py)
│   └── Quick Launcher (launcher.py)
├── 🎨 Visualization Layer (Plotly)
│   ├── Time Series Charts (TimeSeriesVisualizer)
│   ├── Risk Analytics (RiskVisualizer)
│   ├── Genome Charts (GenomeVisualizer)
│   └── Anomaly Detection (AnomalyVisualizer)
├── 💾 Data Layer
│   ├── Real-time Buffers (TimeSeriesBuffer)
│   ├── Caching System (DataCache)
│   ├── Database Storage (DatabaseManager)
│   └── Data Management (DashboardDataManager)
└── 🔗 Integration Layer
    └── CRISPR-FinAI System Connectivity
```

## 📈 Visualization Gallery

### Performance Dashboard
- **Multi-strategy Comparison**: Side-by-side performance analysis
- **Risk-Adjusted Returns**: Sharpe ratio, Sortino ratio, Calmar ratio
- **Drawdown Analysis**: Underwater curves and recovery periods
- **Rolling Statistics**: Moving averages, volatility, correlation

### Genome Analysis
- **Parameter Heatmaps**: Visual representation of genome parameters
- **Evolution Progress**: Fitness improvement over generations
- **Parameter Distribution**: Box plots and density charts
- **Health Metrics**: Multi-dimensional genome health radar

### Anomaly Detection
- **Real-time Scoring**: Live anomaly score monitoring
- **Detection Timeline**: Historical anomaly events
- **Feature Analysis**: Feature-level anomaly contributions
- **Alert Management**: Severity-based alert system

### Risk Management
- **Correlation Matrices**: Asset and factor correlation heatmaps
- **Risk Decomposition**: Portfolio risk contribution analysis
- **VaR Evolution**: Value-at-Risk tracking over time
- **Stress Testing**: Scenario analysis and backtesting

## 🛠️ Installation & Setup

### Dependencies
```bash
# Core dependencies
pip install streamlit plotly pandas numpy

# Optional enhancements
pip install sqlite3 asyncio threading
```

### Database Setup
```python
# Automatic database initialization
from src.dashboard.data_layer import DatabaseManager

db = DatabaseManager("crispr_dashboard.db")
# Database tables created automatically
```

### Configuration
```json
{
  "dashboard": {
    "cache_size_mb": 100,
    "refresh_interval": 10,
    "max_history_days": 30,
    "enable_mobile": true
  },
  "visualization": {
    "theme": "crispr_bio",
    "chart_height": 400,
    "animation_duration": 500
  }
}
```

## 🔧 API Reference

### Main Classes

#### `CRISPRDashboard`
```python
dashboard = CRISPRDashboard()
dashboard.initialize_system(config_path)
dashboard.run_dashboard()
```

#### `DashboardDataManager`
```python
data_manager = DashboardDataManager(cache_size_mb=100)
data_manager.add_performance_metric(metric)
data_manager.get_dashboard_data(period='24h')
```

#### `TimeSeriesVisualizer`
```python
viz = TimeSeriesVisualizer()
fig = viz.create_performance_comparison(strategies)
fig = viz.create_candlestick_chart(ohlc_data)
```

### Data Structures

#### `PerformanceMetric`
```python
@dataclass
class PerformanceMetric:
    timestamp: datetime
    value: float
    metric_type: str
    category: str
    metadata: Dict[str, Any] = None
```

#### `SystemEvent`
```python
@dataclass
class SystemEvent:
    timestamp: datetime
    event_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    component: str
    data: Dict[str, Any] = None
```

## 🎯 Usage Examples

### Real-time Data Streaming
```python
from src.dashboard import DashboardDataManager, PerformanceMetric
from datetime import datetime

# Initialize data manager
data_manager = DashboardDataManager()

# Add real-time performance data
metric = PerformanceMetric(
    timestamp=datetime.now(),
    value=0.0234,
    metric_type='daily_return',
    category='performance'
)
data_manager.add_performance_metric(metric)

# Get dashboard data
dashboard_data = data_manager.get_dashboard_data(period='24h')
```

### Custom Visualizations
```python
from src.dashboard import TimeSeriesVisualizer, CRISPRTheme
import pandas as pd

# Create sample data
returns = pd.Series([0.01, -0.005, 0.02, 0.015], 
                   index=pd.date_range('2024-01-01', periods=4))

# Create visualization
viz = TimeSeriesVisualizer()
fig = viz.create_performance_comparison({'Strategy A': returns})

# Apply CRISPR theme
fig.update_layout(template=CRISPRTheme.TEMPLATE)
fig.show()
```

### Mobile Dashboard Integration
```python
from src.dashboard import MobileDashboard

# Launch mobile-optimized interface
mobile_dash = MobileDashboard()
mobile_dash.run_mobile_dashboard()
```

## 📊 Dashboard Pages

### 🏠 **Overview Page**
- System status indicators
- Key performance metrics
- Recent activity summary
- Quick action buttons

### 📈 **Performance Page**
- Detailed performance analytics
- Strategy comparison charts
- Risk-adjusted metrics
- Historical analysis

### 🧬 **Genome Page**
- Parameter visualization
- Evolution tracking
- Health monitoring
- Edit history

### 🔍 **Anomaly Page**
- Real-time detection
- Historical anomalies
- Feature analysis
- Alert management

### ⚖️ **Compliance Page**
- Compliance scoring
- Violation tracking
- Audit trails
- Regulatory reports

## 🎨 Customization

### Theme Customization
```python
from src.dashboard.plotly_components import CRISPRTheme

# Modify color palette
CRISPRTheme.COLORS['primary'] = '#custom_color'

# Custom template
custom_template = CRISPRTheme.TEMPLATE.copy()
custom_template['layout']['font']['size'] = 14
```

### Component Extension
```python
from src.dashboard.plotly_components import TimeSeriesVisualizer
import plotly.graph_objects as go

class CustomVisualizer(TimeSeriesVisualizer):
    def create_custom_chart(self, data):
        fig = go.Figure()
        # Custom chart implementation
        return fig
```

## 🚀 Performance Optimization

### Caching Strategy
- **Memory Cache**: 100MB default with LRU eviction
- **Database Storage**: SQLite with automatic cleanup
- **Real-time Buffers**: Circular buffers for live data

### Data Management
- **Automatic Aggregation**: Minute/hour/day aggregates
- **Background Processing**: Non-blocking data updates
- **Efficient Queries**: Indexed database operations

## 🔒 Security Features

### Data Protection
- **Local Storage**: No external data transmission
- **Secure Caching**: Memory-only sensitive data
- **Access Control**: Dashboard-level permissions

### System Integration
- **Safe API Calls**: Error handling and timeouts
- **Resource Limits**: Memory and CPU constraints
- **Graceful Degradation**: Fallback modes

## 🐛 Troubleshooting

### Common Issues

#### Dashboard Won't Start
```bash
# Check dependencies
pip install streamlit plotly pandas numpy

# Check ports
netstat -an | grep 8501

# Launch with debug
streamlit run src/dashboard/streamlit_app.py --logger.level=debug
```

#### Performance Issues
```python
# Reduce cache size
data_manager = DashboardDataManager(cache_size_mb=50)

# Limit data history
dashboard_data = data_manager.get_dashboard_data(period='1h')
```

#### Memory Usage
```python
# Monitor cache stats
stats = data_manager.cache.get_stats()
print(f"Memory usage: {stats['memory_usage_mb']:.1f} MB")

# Clear cache if needed
data_manager.cache.clear()
```

## 📚 Additional Resources

- **CRISPR-FinAI Documentation**: Main system documentation
- **Streamlit Docs**: https://docs.streamlit.io/
- **Plotly Docs**: https://plotly.com/python/
- **Bio-Inspired Computing**: Genetic algorithm references

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository>

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/dashboard/

# Code formatting
black src/dashboard/
```

### Adding Visualizations
1. Create new visualizer class in `plotly_components.py`
2. Follow `CRISPRTheme` color scheme
3. Add comprehensive docstrings
4. Include usage examples
5. Update `__init__.py` exports

## 📄 License

This dashboard is part of the CRISPR-FinAI system. See main project license.

---

**🧬 From Data to Insights. From Mutations to Evolution.**

*Built with scientific precision for financial intelligence.*