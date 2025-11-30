"""
📱 CRISPR-FinAI Mobile Dashboard

Mobile-optimized real-time monitoring interface for CRISPR-FinAI system.
Responsive design for monitoring genetic modifications on mobile devices.

From desktop insights to mobile intelligence.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# Mobile-optimized configuration
MOBILE_CONFIG = {
    'chart_height': 300,
    'compact_metrics': True,
    'simplified_views': True,
    'touch_friendly': True
}


class MobileDashboard:
    """
    📱 Mobile-Optimized CRISPR Dashboard
    
    Streamlined interface designed for mobile monitoring of the
    CRISPR-FinAI system. Focused on essential metrics and alerts.
    """

    def __init__(self):
        self.color_palette = {
            'primary': '#1f77b4',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'dark': '#343a40'
        }

    def run_mobile_dashboard(self):
        """Run mobile-optimized dashboard."""
        # Mobile-specific page config
        st.set_page_config(
            page_title="🧬 CRISPR Mobile",
            page_icon="🧬",
            layout="centered",
            initial_sidebar_state="collapsed"
        )

        # Mobile CSS
        st.markdown("""
        <style>
        .mobile-header {
            font-size: 1.8em;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 20px;
        }
        .metric-mobile {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            margin: 10px 0;
        }
        .alert-mobile {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 10px;
            border-radius: 8px;
            margin: 5px 0;
        }
        .status-card {
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 10px;
            border-left: 4px solid #28a745;
            margin: 8px 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header
        st.markdown('<h1 class="mobile-header">🧬 CRISPR Mobile</h1>', unsafe_allow_html=True)

        # Quick status
        self._render_quick_status()

        # Main navigation
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "⚡ Live", "🚨 Alerts"])

        with tab1:
            self._render_overview_mobile()

        with tab2:
            self._render_live_mobile()

        with tab3:
            self._render_alerts_mobile()

    def _render_quick_status(self):
        """Render quick system status for mobile."""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="metric-mobile">
                <h3>System Status</h3>
                <h2>🟢 Active</h2>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-mobile">
                <h3>Performance</h3>
                <h2>+2.3%</h2>
            </div>
            """, unsafe_allow_html=True)

    def _render_overview_mobile(self):
        """Render mobile overview."""
        st.markdown("### 📈 Key Metrics")

        # Compact metrics
        metrics_data = {
            'Active Genomes': 3,
            'Total Edits': 247,
            'Success Rate': '94.2%',
            'Uptime': '72h'
        }

        for i, (metric, value) in enumerate(metrics_data.items()):
            if i % 2 == 0:
                col1, col2 = st.columns(2)

            with col1 if i % 2 == 0 else col2:
                st.markdown(f"""
                <div class="status-card">
                    <strong>{metric}</strong><br>
                    <span style="font-size: 1.2em;">{value}</span>
                </div>
                """, unsafe_allow_html=True)

        # Simplified performance chart
        st.markdown("### 📊 Performance Trend")

        # Generate sample data
        dates = [datetime.now() - timedelta(days=i) for i in range(7, 0, -1)]
        returns = np.random.uniform(-0.02, 0.03, 7)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=returns,
            mode='lines+markers',
            fill='tonexty',
            line=dict(color=self.color_palette['primary'], width=3),
            marker=dict(size=8)
        ))

        fig.update_layout(
            height=MOBILE_CONFIG['chart_height'],
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            xaxis_title="",
            yaxis_title="Return %"
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_live_mobile(self):
        """Render live monitoring for mobile."""
        st.markdown("### ⚡ Live Monitoring")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (10s)")

        if auto_refresh:
            # Placeholder for auto-refresh logic
            st.info("Auto-refresh enabled. Data updates every 10 seconds.")

        # Real-time metrics
        st.markdown("#### 📊 Real-time Data")

        # Simulated real-time data
        current_time = datetime.now()
        live_data = {
            'timestamp': current_time.strftime('%H:%M:%S'),
            'portfolio_value': 1_234_567.89,
            'daily_pnl': 2_845.32,
            'active_positions': 12,
            'anomaly_score': 0.23
        }

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Portfolio Value", f"${live_data['portfolio_value']:,.2f}")
            st.metric("Active Positions", live_data['active_positions'])

        with col2:
            st.metric("Daily P&L", f"${live_data['daily_pnl']:,.2f}", delta="2.3%")
            st.metric("Anomaly Score", f"{live_data['anomaly_score']:.2f}")

        # Live chart
        live_fig = go.Figure()

        # Generate live data points
        time_points = [current_time - timedelta(minutes=i) for i in range(30, 0, -1)]
        values = np.random.walk(30).cumsum()

        live_fig.add_trace(go.Scatter(
            x=time_points,
            y=values,
            mode='lines',
            line=dict(color=self.color_palette['success'], width=2),
            name='Live Performance'
        ))

        live_fig.update_layout(
            height=MOBILE_CONFIG['chart_height'],
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            xaxis=dict(showticklabels=False),
            yaxis_title="Value"
        )

        st.plotly_chart(live_fig, use_container_width=True)

        # Last update timestamp
        st.caption(f"Last updated: {current_time.strftime('%H:%M:%S')}")

    def _render_alerts_mobile(self):
        """Render alerts and notifications for mobile."""
        st.markdown("### 🚨 System Alerts")

        # Alert severity filter
        severity_filter = st.selectbox(
            "Filter by severity:",
            ["All", "High", "Medium", "Low"]
        )

        # Sample alerts
        alerts = [
            {
                'time': '10:23:45',
                'severity': 'High',
                'message': 'Anomaly detected in momentum strategy',
                'action': 'Auto-correction applied'
            },
            {
                'time': '09:15:22',
                'severity': 'Medium',
                'message': 'High edit frequency detected',
                'action': 'Rate limiting activated'
            },
            {
                'time': '08:44:12',
                'severity': 'Low',
                'message': 'Parameter drift in risk model',
                'action': 'Monitoring increased'
            },
            {
                'time': '07:33:01',
                'severity': 'High',
                'message': 'Emergency stop triggered',
                'action': 'System restored automatically'
            }
        ]

        # Filter alerts
        if severity_filter != "All":
            alerts = [a for a in alerts if a['severity'] == severity_filter]

        # Display alerts
        for alert in alerts:
            severity_color = {
                'High': '#dc3545',
                'Medium': '#ffc107',
                'Low': '#28a745'
            }.get(alert['severity'], '#6c757d')

            st.markdown(f"""
            <div style="border-left: 4px solid {severity_color}; padding: 10px; margin: 8px 0; background: #f8f9fa;">
                <strong>{alert['time']} - {alert['severity']}</strong><br>
                {alert['message']}<br>
                <small style="color: #6c757d;">Action: {alert['action']}</small>
            </div>
            """, unsafe_allow_html=True)

        # Alert statistics
        st.markdown("#### 📊 Alert Summary")

        total_alerts = len(alerts)
        high_alerts = len([a for a in alerts if a['severity'] == 'High'])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Alerts", total_alerts)
        with col2:
            st.metric("High Priority", high_alerts)

        # Quick actions
        st.markdown("#### 🎮 Quick Actions")

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("🔧 Auto-Fix Issues"):
                st.success("Auto-fix initiated!")

        with action_col2:
            if st.button("📞 Contact Support"):
                st.info("Support notification sent!")


def run_mobile_dashboard():
    """Run the mobile dashboard."""
    mobile_dash = MobileDashboard()
    mobile_dash.run_mobile_dashboard()


if __name__ == "__main__":
    run_mobile_dashboard()
