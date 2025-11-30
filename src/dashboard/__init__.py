"""
🚀 CRISPR-FinAI Dashboard Package

Advanced visualization and monitoring interface for the CRISPR-FinAI system.
Real-time dashboards with scientific-grade data visualization.

From system monitoring to visual intelligence.
"""

from .streamlit_app import CRISPRDashboard, run_dashboard
from .mobile_app import MobileDashboard, run_mobile_dashboard
from .plotly_components import (
    CRISPRTheme,
    TimeSeriesVisualizer,
    RiskVisualizer,
    GenomeVisualizer,
    AnomalyVisualizer
)
from .data_layer import (
    PerformanceMetric,
    SystemEvent,
    GenomeSnapshot,
    DashboardDataManager
)

# Version info
__version__ = "1.0.0"
__author__ = "CRISPR-FinAI Team"

# Package metadata
__all__ = [
    # Main dashboard classes
    'CRISPRDashboard',
    'MobileDashboard',

    # Visualization components
    'CRISPRTheme',
    'TimeSeriesVisualizer',
    'RiskVisualizer',
    'GenomeVisualizer',
    'AnomalyVisualizer',

    # Data management
    'PerformanceMetric',
    'SystemEvent',
    'GenomeSnapshot',
    'DashboardDataManager',

    # Convenience functions
    'run_dashboard',
    'run_mobile_dashboard'
]

# Quick start functions
def launch_dashboard(config_path: str = None, port: int = 8501):
    """
    🚀 Quick launch function for CRISPR dashboard
    
    Args:
        config_path: Path to CRISPR config file
        port: Port to run dashboard on
    """
    import streamlit.web.cli as stcli
    import sys
    import os

    # Get dashboard script path
    dashboard_script = os.path.join(os.path.dirname(__file__), "streamlit_app.py")

    # Set up Streamlit arguments
    sys.argv = [
        "streamlit",
        "run",
        dashboard_script,
        f"--server.port={port}",
        "--server.headless=false"
    ]

    # Launch Streamlit
    stcli.main()


def launch_mobile_dashboard(port: int = 8502):
    """
    📱 Quick launch function for mobile dashboard
    
    Args:
        port: Port to run mobile dashboard on
    """
    import streamlit.web.cli as stcli
    import sys
    import os

    # Get mobile dashboard script path
    mobile_script = os.path.join(os.path.dirname(__file__), "mobile_app.py")

    # Set up Streamlit arguments
    sys.argv = [
        "streamlit",
        "run",
        mobile_script,
        f"--server.port={port}",
        "--server.headless=false"
    ]

    # Launch Streamlit
    stcli.main()


# Module documentation
__doc__ = """
🧬 CRISPR-FinAI Dashboard Package

This package provides comprehensive visualization and monitoring capabilities
for the CRISPR-FinAI bio-inspired financial intelligence system.

## Components

### Main Dashboards
- **CRISPRDashboard**: Full-featured web dashboard with advanced analytics
- **MobileDashboard**: Mobile-optimized monitoring interface

### Visualization Components
- **TimeSeriesVisualizer**: Financial time series charts and technical indicators
- **RiskVisualizer**: Risk analysis and portfolio metrics visualization
- **GenomeVisualizer**: Genetic algorithm and parameter evolution charts
- **AnomalyVisualizer**: Anomaly detection and system health monitoring

### Data Management
- **DashboardDataManager**: Real-time data streams and caching
- **PerformanceMetric**: Performance data structures
- **SystemEvent**: System event tracking
- **GenomeSnapshot**: Genome state snapshots

## Quick Start

### Launch Full Dashboard
```python
from crispr.dashboard import launch_dashboard

# Launch on default port 8501
launch_dashboard()

# Launch with custom config
launch_dashboard(config_path="my_config.json", port=8080)
```

### Launch Mobile Dashboard
```python
from crispr.dashboard import launch_mobile_dashboard

# Launch mobile interface
launch_mobile_dashboard(port=8502)
```

### Custom Dashboard
```python
from crispr.dashboard import CRISPRDashboard

# Create custom dashboard
dashboard = CRISPRDashboard()
dashboard.initialize_system("config.json")
dashboard.run_dashboard()
```

### Visualization Components
```python
from crispr.dashboard import TimeSeriesVisualizer, CRISPRTheme

# Create custom visualizations
viz = TimeSeriesVisualizer()
fig = viz.create_performance_comparison(strategy_data)

# Apply CRISPR theme
fig.update_layout(template=CRISPRTheme.TEMPLATE)
```

## Features

- 📊 **Real-time Monitoring**: Live system metrics and performance tracking
- 🧬 **Genome Visualization**: Genetic algorithm evolution and parameter analysis
- 📈 **Financial Analytics**: Advanced portfolio and risk analytics
- 🔍 **Anomaly Detection**: Visual anomaly detection and alerting
- 📱 **Mobile Support**: Responsive mobile-optimized interface
- 💾 **Data Management**: Efficient caching and historical data storage
- 🎨 **Scientific Aesthetics**: Bio-inspired color themes and modern design

## Architecture

The dashboard follows a modular architecture:

1. **Presentation Layer**: Streamlit-based web interfaces
2. **Visualization Layer**: Plotly-based interactive charts
3. **Data Layer**: Caching, real-time streams, and persistence
4. **Integration Layer**: CRISPR-FinAI system connectivity

Each layer is designed for high performance, scalability, and extensibility.
"""
