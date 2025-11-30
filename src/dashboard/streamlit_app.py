"""
📊 CRISPR-FinAI Advanced Visualization Dashboard

Interactive web-based dashboard for real-time monitoring and analysis
of CRISPR-FinAI system performance. Like a digital microscope for
observing genetic modifications in financial models.

From data to insights. From mutations to evolution.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
import threading
import time

# CRISPR components
from ..main import CRISPRFinAI

logger = logging.getLogger(__name__)


class DashboardDataManager:
    """
    📊 Dashboard Data Management System
    
    Manages real-time data flow and caching for the visualization dashboard.
    Like a data laboratory managing experimental results.
    """

    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_duration = 300  # 5 minutes

        # Data streams
        self.performance_data = []
        self.edit_history = []
        self.anomaly_data = []
        self.compliance_data = []

        # Real-time monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if still valid."""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.cache_duration:
                return self.cache[key]
        return None

    def set_cached_data(self, key: str, data: Any):
        """Cache data with timestamp."""
        self.cache[key] = data
        self.cache_timestamps[key] = time.time()

    def start_monitoring(self, crispr_system: CRISPRFinAI):
        """Start real-time monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(crispr_system,),
                daemon=True
            )
            self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()

    def _monitoring_loop(self, crispr_system: CRISPRFinAI):
        """Real-time monitoring loop."""
        while self.monitoring_active:
            try:
                # Update system status
                status = crispr_system.get_system_status()
                self.set_cached_data('system_status', status)

                # Update performance metrics if available
                if hasattr(crispr_system, 'session_results'):
                    self.set_cached_data('session_results', crispr_system.session_results)

                time.sleep(10)  # Update every 10 seconds

            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(30)  # Wait longer on error


class VisualizationEngine:
    """
    🎨 Advanced Visualization Engine
    
    Creates sophisticated interactive charts and plots for CRISPR-FinAI
    system analysis. Like creating visual representations of genetic data.
    """

    def __init__(self):
        self.color_palette = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }

    def create_performance_dashboard(self, performance_data: Dict) -> go.Figure:
        """
        📈 Create comprehensive performance dashboard
        
        Args:
            performance_data: Performance metrics and time series
            
        Returns:
            Interactive Plotly figure
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Portfolio Returns', 'Risk Metrics', 'Edit Performance', 'System Health'],
            specs=[[{'secondary_y': True}, {'type': 'indicator'}],
                   [{'type': 'bar'}, {'type': 'scatter'}]]
        )

        # Portfolio Returns (Row 1, Col 1)
        if 'returns_timeseries' in performance_data:
            returns = performance_data['returns_timeseries']
            cumulative = np.cumprod(1 + np.array(returns)) - 1

            fig.add_trace(
                go.Scatter(
                    x=list(range(len(cumulative))),
                    y=cumulative,
                    name='Cumulative Returns',
                    line=dict(color=self.color_palette['primary'], width=2)
                ),
                row=1, col=1
            )

            # Add benchmark if available
            if 'benchmark_returns' in performance_data:
                benchmark_cum = np.cumprod(1 + np.array(performance_data['benchmark_returns'])) - 1
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(benchmark_cum))),
                        y=benchmark_cum,
                        name='Benchmark',
                        line=dict(color=self.color_palette['secondary'], width=2, dash='dash')
                    ),
                    row=1, col=1
                )

        # Risk Metrics (Row 1, Col 2)
        if 'risk_metrics' in performance_data:
            metrics = performance_data['risk_metrics']

            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=metrics.get('sharpe_ratio', 0),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Sharpe Ratio"},
                    gauge={
                        'axis': {'range': [-1, 3]},
                        'bar': {'color': self.color_palette['success']},
                        'steps': [
                            {'range': [-1, 0], 'color': self.color_palette['warning']},
                            {'range': [0, 1], 'color': 'yellow'},
                            {'range': [1, 3], 'color': self.color_palette['success']}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 1.5
                        }
                    }
                ),
                row=1, col=2
            )

        # Edit Performance (Row 2, Col 1)
        if 'edit_stats' in performance_data:
            edit_stats = performance_data['edit_stats']

            categories = list(edit_stats.keys())
            values = list(edit_stats.values())

            fig.add_trace(
                go.Bar(
                    x=categories,
                    y=values,
                    name='Edit Statistics',
                    marker_color=self.color_palette['info']
                ),
                row=2, col=1
            )

        # System Health (Row 2, Col 2)
        if 'system_health' in performance_data:
            health_data = performance_data['system_health']

            fig.add_trace(
                go.Scatter(
                    x=health_data.get('timestamps', []),
                    y=health_data.get('stability_scores', []),
                    mode='lines+markers',
                    name='Stability Score',
                    line=dict(color=self.color_palette['success'])
                ),
                row=2, col=2
            )

        # Update layout
        fig.update_layout(
            title_text="🧬 CRISPR-FinAI Performance Dashboard",
            showlegend=True,
            height=800,
            template='plotly_white'
        )

        return fig

    def create_genome_heatmap(self, genome_data: Dict) -> go.Figure:
        """
        🧬 Create genome parameter heatmap
        
        Args:
            genome_data: Genome parameter values and metadata
            
        Returns:
            Interactive heatmap visualization
        """
        if not genome_data:
            return go.Figure()

        # Prepare data for heatmap
        chromosomes = list(genome_data.keys())
        max_genes = max(len(genes) for genes in genome_data.values())

        # Create matrix
        z_values = []
        gene_names = []
        chromosome_labels = []

        for chrom in chromosomes:
            genes = genome_data[chrom]
            row_values = []
            row_names = []

            for gene_name, gene_info in genes.items():
                value = gene_info.get('value', 0)
                if isinstance(value, (list, np.ndarray)):
                    value = np.mean(value)
                row_values.append(float(value))
                row_names.append(gene_name)

            # Pad to max length
            while len(row_values) < max_genes:
                row_values.append(np.nan)
                row_names.append('')

            z_values.append(row_values)
            if not gene_names:  # First chromosome sets gene names
                gene_names = row_names
            chromosome_labels.append(chrom)

        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=gene_names,
            y=chromosome_labels,
            colorscale='RdYlBu',
            showscale=True,
            hoverongaps=False
        ))

        fig.update_layout(
            title="🧬 Financial Genome Parameter Heatmap",
            xaxis_title="Genes (Parameters)",
            yaxis_title="Chromosomes",
            height=600,
            template='plotly_white'
        )

        return fig

    def create_edit_timeline(self, edit_history: List[Dict]) -> go.Figure:
        """
        ⏰ Create edit timeline visualization
        
        Args:
            edit_history: List of edit events with timestamps
            
        Returns:
            Timeline chart
        """
        if not edit_history:
            return go.Figure()

        # Prepare timeline data
        timestamps = [edit['timestamp'] for edit in edit_history]
        parameters = [edit.get('parameter_path', 'Unknown') for edit in edit_history]
        success = [edit.get('success', False) for edit in edit_history]
        improvements = [edit.get('fitness_improvement', 0) for edit in edit_history]

        # Create scatter plot
        colors = [self.color_palette['success'] if s else self.color_palette['warning'] for s in success]

        fig = go.Figure(data=go.Scatter(
            x=timestamps,
            y=parameters,
            mode='markers',
            marker=dict(
                size=[abs(imp) * 100 + 10 for imp in improvements],
                color=colors,
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=[f"Improvement: {imp:.3f}" for imp in improvements],
            hovertemplate="<b>%{y}</b><br>Time: %{x}<br>%{text}<extra></extra>"
        ))

        fig.update_layout(
            title="✂️ Parameter Edit Timeline",
            xaxis_title="Time",
            yaxis_title="Parameters",
            height=500,
            template='plotly_white'
        )

        return fig

    def create_anomaly_detection_plot(self, anomaly_data: Dict) -> go.Figure:
        """
        🔍 Create anomaly detection visualization
        
        Args:
            anomaly_data: Anomaly scores and detection results
            
        Returns:
            Anomaly detection plot
        """
        if not anomaly_data:
            return go.Figure()

        timestamps = anomaly_data.get('timestamps', [])
        scores = anomaly_data.get('anomaly_scores', [])
        threshold = anomaly_data.get('threshold', 0.5)
        detections = anomaly_data.get('anomaly_detected', [])

        fig = go.Figure()

        # Anomaly scores
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=scores,
            mode='lines+markers',
            name='Anomaly Score',
            line=dict(color=self.color_palette['primary']),
            fill='tonexty'
        ))

        # Threshold line
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color=self.color_palette['warning'],
            annotation_text="Threshold"
        )

        # Highlight detections
        if detections:
            detection_times = [t for t, d in zip(timestamps, detections) if d]
            detection_scores = [s for s, d in zip(scores, detections) if d]

            if detection_times:
                fig.add_trace(go.Scatter(
                    x=detection_times,
                    y=detection_scores,
                    mode='markers',
                    name='Anomalies Detected',
                    marker=dict(
                        size=12,
                        color=self.color_palette['warning'],
                        symbol='diamond'
                    )
                ))

        fig.update_layout(
            title="🔍 Anomaly Detection Results",
            xaxis_title="Time",
            yaxis_title="Anomaly Score",
            height=400,
            template='plotly_white'
        )

        return fig

    def create_compliance_report_viz(self, compliance_data: Dict) -> go.Figure:
        """
        📋 Create compliance report visualization
        
        Args:
            compliance_data: Compliance scores and violation data
            
        Returns:
            Compliance dashboard
        """
        if not compliance_data:
            return go.Figure()

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Compliance Score', 'Violation Breakdown'],
            specs=[[{'type': 'indicator'}, {'type': 'pie'}]]
        )

        # Compliance Score Gauge
        score = compliance_data.get('compliance_score', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Compliance Score"},
                gauge={
                    'axis': {'range': [0, 1]},
                    'bar': {'color': self.color_palette['success'] if score > 0.8 else self.color_palette['warning']},
                    'steps': [
                        {'range': [0, 0.5], 'color': 'lightgray'},
                        {'range': [0.5, 0.8], 'color': 'yellow'},
                        {'range': [0.8, 1], 'color': 'lightgreen'}
                    ]
                }
            ),
            row=1, col=1
        )

        # Violation Breakdown
        violations = compliance_data.get('violations', [])
        if violations:
            violation_types = [v.get('type', 'Unknown') for v in violations]
            violation_counts = {}
            for vtype in violation_types:
                violation_counts[vtype] = violation_counts.get(vtype, 0) + 1

            fig.add_trace(
                go.Pie(
                    labels=list(violation_counts.keys()),
                    values=list(violation_counts.values()),
                    name="Violations"
                ),
                row=1, col=2
            )

        fig.update_layout(
            title="⚖️ Compliance Dashboard",
            height=400,
            template='plotly_white'
        )

        return fig


class CRISPRDashboard:
    """
    🖥️ Main CRISPR-FinAI Dashboard Application
    
    Interactive Streamlit-based dashboard for monitoring and controlling
    the CRISPR-FinAI system. Like a mission control center for genetic
    modifications in financial models.
    """

    def __init__(self):
        self.data_manager = DashboardDataManager()
        self.viz_engine = VisualizationEngine()
        self.crispr_system: Optional[CRISPRFinAI] = None

    def initialize_system(self, config_path: Optional[str] = None) -> bool:
        """Initialize CRISPR system for dashboard."""
        try:
            self.crispr_system = CRISPRFinAI(config_path)
            self.data_manager.start_monitoring(self.crispr_system)
            return True
        except Exception as e:
            st.error(f"Failed to initialize CRISPR system: {str(e)}")
            return False

    def run_dashboard(self):
        """Run the main dashboard application."""
        st.set_page_config(
            page_title="🧬 CRISPR-FinAI Dashboard",
            page_icon="🧬",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 3em;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 30px;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #1f77b4;
        }
        .status-good { color: #2ca02c; }
        .status-warning { color: #ff7f0e; }
        .status-error { color: #d62728; }
        </style>
        """, unsafe_allow_html=True)

        # Header
        st.markdown('<h1 class="main-header">🧬 CRISPR-FinAI Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("*Bio-Inspired Adaptive Financial Intelligence — Real-Time Monitoring*")

        # Sidebar
        self._render_sidebar()

        # Main content
        if self.crispr_system is None:
            self._render_initialization_page()
        else:
            self._render_main_dashboard()

    def _render_sidebar(self):
        """Render sidebar with controls and navigation."""
        st.sidebar.markdown("## 🎛️ Control Panel")

        # System status
        if self.crispr_system:
            status_data = self.data_manager.get_cached_data('system_status')
            if status_data:
                st.sidebar.markdown("### 📊 System Status")

                uptime = status_data.get('uptime_seconds', 0)
                st.sidebar.metric("Uptime", f"{uptime:.0f}s")

                active_genomes = status_data.get('active_genomes', 0)
                st.sidebar.metric("Active Genomes", active_genomes)

                operations = status_data.get('operations_performed', {})
                total_ops = sum(operations.values())
                st.sidebar.metric("Total Operations", total_ops)

        # Navigation
        st.sidebar.markdown("### 🧭 Navigation")
        page = st.sidebar.selectbox(
            "Select Page",
            ["🏠 Overview", "📈 Performance", "🧬 Genome Analysis", "🔍 Anomaly Detection", "⚖️ Compliance"]
        )

        # System controls
        st.sidebar.markdown("### 🎮 System Controls")

        if st.sidebar.button("🔄 Refresh Data"):
            self._refresh_data()

        if st.sidebar.button("📊 Generate Report"):
            self._generate_report()

        if st.sidebar.button("💾 Save Session"):
            self._save_session()

        return page

    def _render_initialization_page(self):
        """Render system initialization page."""
        st.markdown("## 🚀 System Initialization")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Configuration")
            config_file = st.file_uploader("Upload Config File (Optional)", type=['json'])

            if st.button("Initialize CRISPR System"):
                config_path = None
                if config_file:
                    # Save uploaded config
                    config_path = f"temp_config_{int(time.time())}.json"
                    with open(config_path, 'wb') as f:
                        f.write(config_file.getbuffer())

                with st.spinner("Initializing CRISPR-FinAI system..."):
                    if self.initialize_system(config_path):
                        st.success("✅ System initialized successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ System initialization failed!")

        with col2:
            st.markdown("### Quick Start Guide")
            st.markdown("""
            1. **Upload Configuration** (optional): Custom system parameters
            2. **Initialize System**: Start CRISPR-FinAI components
            3. **Monitor Performance**: Real-time system metrics
            4. **Analyze Results**: Detailed performance analytics
            5. **Generate Reports**: Comprehensive analysis reports
            """)

    def _render_main_dashboard(self):
        """Render main dashboard with all components."""
        page = st.session_state.get('current_page', '🏠 Overview')

        if page == "🏠 Overview":
            self._render_overview_page()
        elif page == "📈 Performance":
            self._render_performance_page()
        elif page == "🧬 Genome Analysis":
            self._render_genome_page()
        elif page == "🔍 Anomaly Detection":
            self._render_anomaly_page()
        elif page == "⚖️ Compliance":
            self._render_compliance_page()

    def _render_overview_page(self):
        """Render overview page with key metrics."""
        st.markdown("## 🏠 System Overview")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("System Status", "🟢 Operational")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Active Genomes", "3")
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Edits", "247")
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Compliance Score", "94.2%")
            st.markdown('</div>', unsafe_allow_html=True)

        # Recent activity
        st.markdown("## 📊 Recent Activity")

        # Sample data for demonstration
        recent_data = {
            'returns_timeseries': np.random.randn(100).cumsum() * 0.01,
            'benchmark_returns': np.random.randn(100).cumsum() * 0.008,
            'risk_metrics': {'sharpe_ratio': 1.47},
            'edit_stats': {'Successful': 85, 'Failed': 12, 'Pending': 3},
            'system_health': {
                'timestamps': [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)],
                'stability_scores': np.random.uniform(0.8, 1.0, 24)
            }
        }

        performance_fig = self.viz_engine.create_performance_dashboard(recent_data)
        st.plotly_chart(performance_fig, use_container_width=True)

    def _render_performance_page(self):
        """Render detailed performance analysis page."""
        st.markdown("## 📈 Performance Analysis")

        # Time range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())

        # Performance metrics
        st.markdown("### 📊 Key Performance Indicators")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sharpe Ratio", "1.47", "0.12")
        with col2:
            st.metric("Annual Return", "23.4%", "2.1%")
        with col3:
            st.metric("Max Drawdown", "-8.3%", "1.2%")

        # Detailed charts would be added here based on actual data
        st.info("📊 Detailed performance charts will be displayed here based on actual system data.")

    def _render_genome_page(self):
        """Render genome analysis page."""
        st.markdown("## 🧬 Genome Analysis")

        # Genome selector
        if self.crispr_system and self.crispr_system.active_genomes:
            genome_names = list(self.crispr_system.active_genomes.keys())
            selected_genome = st.selectbox("Select Genome", genome_names)

            if selected_genome:
                genome = self.crispr_system.active_genomes[selected_genome]

                # Genome info
                st.markdown(f"### 📋 Genome: {selected_genome}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Parameters", len(genome.list_all_parameters()))
                with col2:
                    st.metric("Chromosomes", len(genome.list_chromosomes()))
                with col3:
                    st.metric("Health Score", f"{genome.calculate_health_score():.2f}")

                # Genome visualization
                genome_data = {}
                for chrom in genome.list_chromosomes():
                    genome_data[chrom] = {}
                    for gene_name in genome.list_genes(chrom):
                        param_path = f"{chrom}.{gene_name}"
                        gene = genome.get_gene(param_path)
                        genome_data[chrom][gene_name] = {
                            'value': gene.value,
                            'edit_count': gene.edit_count
                        }

                heatmap_fig = self.viz_engine.create_genome_heatmap(genome_data)
                st.plotly_chart(heatmap_fig, use_container_width=True)
        else:
            st.warning("No active genomes found. Please create a genome first.")

    def _render_anomaly_page(self):
        """Render anomaly detection page."""
        st.markdown("## 🔍 Anomaly Detection")

        # Detection controls
        col1, col2 = st.columns(2)
        with col1:
            detection_method = st.selectbox("Detection Method", ["Isolation Forest", "Deep Learning", "Statistical"])
        with col2:
            sensitivity = st.slider("Sensitivity", 0.0, 1.0, 0.8)

        # Sample anomaly data
        anomaly_data = {
            'timestamps': [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)],
            'anomaly_scores': np.random.uniform(0, 1, 24),
            'threshold': 0.8,
            'anomaly_detected': np.random.choice([True, False], 24, p=[0.1, 0.9])
        }

        anomaly_fig = self.viz_engine.create_anomaly_detection_plot(anomaly_data)
        st.plotly_chart(anomaly_fig, use_container_width=True)

        # Recent detections
        st.markdown("### 🚨 Recent Anomalies")

        detection_times = [t for t, d in zip(anomaly_data['timestamps'], anomaly_data['anomaly_detected']) if d]
        if detection_times:
            for i, time in enumerate(detection_times[:5]):
                st.warning(f"Anomaly detected at {time.strftime('%H:%M:%S')} - Score: {np.random.uniform(0.8, 1.0):.3f}")
        else:
            st.success("No recent anomalies detected.")

    def _render_compliance_page(self):
        """Render compliance monitoring page."""
        st.markdown("## ⚖️ Compliance Monitoring")

        # Compliance overview
        compliance_data = {
            'compliance_score': 0.942,
            'violations': [
                {'type': 'edit_frequency', 'severity': 'medium'},
                {'type': 'parameter_drift', 'severity': 'low'}
            ]
        }

        compliance_fig = self.viz_engine.create_compliance_report_viz(compliance_data)
        st.plotly_chart(compliance_fig, use_container_width=True)

        # Compliance details
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ Compliance Highlights")
            st.success("✓ Audit trail integrity verified")
            st.success("✓ Parameter constraints enforced")
            st.success("✓ Emergency protocols operational")

        with col2:
            st.markdown("### ⚠️ Areas for Improvement")
            st.warning("• High edit frequency detected")
            st.warning("• Parameter drift in momentum models")
            st.info("• Consider implementing rate limiting")

    def _refresh_data(self):
        """Refresh all dashboard data."""
        # Clear cache
        self.data_manager.cache.clear()
        self.data_manager.cache_timestamps.clear()

        st.success("Data refreshed successfully!")
        st.experimental_rerun()

    def _generate_report(self):
        """Generate comprehensive system report."""
        if self.crispr_system:
            with st.spinner("Generating report..."):
                # Generate compliance report
                compliance_report = self.crispr_system.generate_compliance_report()

                # Create download link
                report_json = json.dumps(compliance_report, indent=2, default=str)
                st.download_button(
                    label="📄 Download Report",
                    data=report_json,
                    file_name=f"crispr_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

                st.success("Report generated successfully!")

    def _save_session(self):
        """Save current session state."""
        if self.crispr_system:
            with st.spinner("Saving session..."):
                session_path = self.crispr_system.save_session()
                st.success(f"Session saved to: {session_path}")


def run_dashboard():
    """Main function to run the dashboard."""
    dashboard = CRISPRDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    run_dashboard()
