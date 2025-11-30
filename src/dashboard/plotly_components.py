"""
📊 Advanced Plotly Visualization Components

Reusable high-performance visualization components for CRISPR-FinAI system.
Modern, interactive charts with scientific aesthetics.

From raw data to beautiful insights.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class CRISPRTheme:
    """
    🎨 CRISPR Visualization Theme
    
    Consistent color palette and styling for all CRISPR visualizations.
    Bio-inspired colors that reflect genetic modification themes.
    """

    # Primary color palette (inspired by DNA/RNA bases)
    COLORS = {
        'adenine': '#FF6B6B',    # Red - A
        'thymine': '#4ECDC4',    # Teal - T
        'guanine': '#45B7D1',    # Blue - G
        'cytosine': '#96CEB4',   # Green - C
        'backbone': '#FFEAA7',   # Yellow - DNA backbone
        'dark': '#2D3436',       # Dark gray
        'light': '#DDD',         # Light gray
        'success': '#00B894',    # Success green
        'warning': '#FDCB6E',    # Warning orange
        'danger': '#E17055',     # Danger red
        'info': '#74B9FF'        # Info blue
    }

    # Chart templates
    TEMPLATE = {
        'layout': {
            'font': {'family': 'Arial, sans-serif', 'size': 12},
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'colorway': list(COLORS.values()[:8]),
            'grid': {'color': '#E5E5E5'},
            'title': {'font': {'size': 16, 'color': COLORS['dark']}}
        },
        'data': {
            'scatter': [{'marker': {'line': {'width': 0.5}}}],
            'bar': [{'marker': {'line': {'width': 0.5}}}]
        }
    }

    @classmethod
    def get_color_scale(cls, n_colors: int = 10) -> List[str]:
        """Get color scale for heatmaps and continuous data."""
        return px.colors.sample_colorscale('viridis', [i/(n_colors-1) for i in range(n_colors)])


class TimeSeriesVisualizer:
    """
    📈 Advanced Time Series Visualization
    
    Specialized components for financial time series with technical indicators,
    performance metrics, and interactive features.
    """

    @staticmethod
    def create_candlestick_chart(
        data: pd.DataFrame,
        title: str = "Price Chart",
        height: int = 500
    ) -> go.Figure:
        """
        🕯️ Create advanced candlestick chart
        
        Args:
            data: DataFrame with OHLCV data
            title: Chart title
            height: Chart height
            
        Returns:
            Interactive candlestick figure
        """
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.02,
            subplot_titles=['Price', 'Volume']
        )

        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name='Price',
                increasing_line_color=CRISPRTheme.COLORS['success'],
                decreasing_line_color=CRISPRTheme.COLORS['danger']
            ),
            row=1, col=1
        )

        # Volume bars
        if 'volume' in data.columns:
            colors = [CRISPRTheme.COLORS['success'] if c >= o else CRISPRTheme.COLORS['danger']
                     for c, o in zip(data['close'], data['open'])]

            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )

        # Moving averages
        if 'ma_20' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['ma_20'],
                    name='MA(20)',
                    line=dict(color=CRISPRTheme.COLORS['adenine'], width=1),
                    opacity=0.8
                ),
                row=1, col=1
            )

        if 'ma_50' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['ma_50'],
                    name='MA(50)',
                    line=dict(color=CRISPRTheme.COLORS['thymine'], width=1),
                    opacity=0.8
                ),
                row=1, col=1
            )

        fig.update_layout(
            title=title,
            height=height,
            xaxis_rangeslider_visible=False,
            template=CRISPRTheme.TEMPLATE
        )

        return fig

    @staticmethod
    def create_performance_comparison(
        strategies: Dict[str, pd.Series],
        title: str = "Strategy Performance Comparison",
        height: int = 400
    ) -> go.Figure:
        """
        📊 Create strategy performance comparison chart
        
        Args:
            strategies: Dict of strategy names and return series
            title: Chart title
            height: Chart height
            
        Returns:
            Performance comparison figure
        """
        fig = go.Figure()

        colors = list(CRISPRTheme.COLORS.values())

        for i, (name, returns) in enumerate(strategies.items()):
            cumulative_returns = (1 + returns).cumprod() - 1

            fig.add_trace(
                go.Scatter(
                    x=returns.index,
                    y=cumulative_returns,
                    name=name,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f"<b>{name}</b><br>Date: %{{x}}<br>Return: %{{y:.2%}}<extra></extra>"
                )
            )

        fig.update_layout(
            title=title,
            height=height,
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
            yaxis_tickformat=".1%",
            hovermode='x unified',
            template=CRISPRTheme.TEMPLATE
        )

        return fig

    @staticmethod
    def create_drawdown_chart(
        returns: pd.Series,
        title: str = "Drawdown Analysis",
        height: int = 300
    ) -> go.Figure:
        """
        📉 Create drawdown visualization
        
        Args:
            returns: Return series
            title: Chart title
            height: Chart height
            
        Returns:
            Drawdown figure
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative / running_max) - 1

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                fill='tonexty',
                name='Drawdown',
                line=dict(color=CRISPRTheme.COLORS['danger'], width=0),
                fillcolor=f"rgba({int(CRISPRTheme.COLORS['danger'][1:3], 16)}, "
                         f"{int(CRISPRTheme.COLORS['danger'][3:5], 16)}, "
                         f"{int(CRISPRTheme.COLORS['danger'][5:7], 16)}, 0.3)"
            )
        )

        fig.update_layout(
            title=title,
            height=height,
            xaxis_title="Date",
            yaxis_title="Drawdown",
            yaxis_tickformat=".1%",
            template=CRISPRTheme.TEMPLATE
        )

        return fig


class RiskVisualizer:
    """
    ⚠️ Risk Analysis Visualization Components
    
    Specialized charts for risk metrics, correlation analysis,
    and portfolio risk decomposition.
    """

    @staticmethod
    def create_correlation_heatmap(
        correlation_matrix: pd.DataFrame,
        title: str = "Asset Correlation Matrix",
        height: int = 500
    ) -> go.Figure:
        """
        🔥 Create correlation heatmap
        
        Args:
            correlation_matrix: Correlation matrix
            title: Chart title
            height: Chart height
            
        Returns:
            Correlation heatmap figure
        """
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=correlation_matrix.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))

        fig.update_layout(
            title=title,
            height=height,
            template=CRISPRTheme.TEMPLATE
        )

        return fig

    @staticmethod
    def create_risk_decomposition(
        risk_contributions: Dict[str, float],
        title: str = "Risk Contribution",
        height: int = 400
    ) -> go.Figure:
        """
        🥧 Create risk decomposition pie chart
        
        Args:
            risk_contributions: Dict of asset/factor risk contributions
            title: Chart title
            height: Chart height
            
        Returns:
            Risk decomposition figure
        """
        fig = go.Figure(data=[go.Pie(
            labels=list(risk_contributions.keys()),
            values=list(risk_contributions.values()),
            hole=0.4,
            textinfo='label+percent',
            textposition='outside',
            marker=dict(
                colors=CRISPRTheme.get_color_scale(len(risk_contributions)),
                line=dict(color='white', width=2)
            )
        )])

        fig.update_layout(
            title=title,
            height=height,
            template=CRISPRTheme.TEMPLATE,
            showlegend=True,
            annotations=[dict(text='Risk<br>Contribution', x=0.5, y=0.5, font_size=12, showarrow=False)]
        )

        return fig

    @staticmethod
    def create_var_evolution(
        var_data: pd.Series,
        confidence_level: float = 0.95,
        title: str = "Value at Risk Evolution",
        height: int = 350
    ) -> go.Figure:
        """
        📊 Create VaR evolution chart
        
        Args:
            var_data: VaR time series
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            title: Chart title
            height: Chart height
            
        Returns:
            VaR evolution figure
        """
        fig = go.Figure()

        # VaR line
        fig.add_trace(
            go.Scatter(
                x=var_data.index,
                y=var_data,
                name=f'{confidence_level:.0%} VaR',
                line=dict(color=CRISPRTheme.COLORS['danger'], width=2),
                fill='tonexty'
            )
        )

        # Add breach indicators if available
        if hasattr(var_data, 'breaches'):
            breach_dates = [date for date, breach in var_data.breaches.items() if breach]
            breach_values = [var_data[date] for date in breach_dates]

            if breach_dates:
                fig.add_trace(
                    go.Scatter(
                        x=breach_dates,
                        y=breach_values,
                        mode='markers',
                        name='VaR Breaches',
                        marker=dict(
                            color=CRISPRTheme.COLORS['warning'],
                            size=10,
                            symbol='triangle-up'
                        )
                    )
                )

        fig.update_layout(
            title=title,
            height=height,
            xaxis_title="Date",
            yaxis_title="VaR",
            yaxis_tickformat=".2%",
            template=CRISPRTheme.TEMPLATE
        )

        return fig


class GenomeVisualizer:
    """
    🧬 Genome and Parameter Visualization
    
    Specialized components for visualizing genetic algorithms,
    parameter evolution, and genome health metrics.
    """

    @staticmethod
    def create_evolution_chart(
        generation_data: List[Dict],
        title: str = "Evolution Progress",
        height: int = 400
    ) -> go.Figure:
        """
        🧬 Create evolution progress chart
        
        Args:
            generation_data: List of generation statistics
            title: Chart title
            height: Chart height
            
        Returns:
            Evolution progress figure
        """
        generations = [g['generation'] for g in generation_data]
        best_fitness = [g['best_fitness'] for g in generation_data]
        avg_fitness = [g['avg_fitness'] for g in generation_data]

        fig = go.Figure()

        # Best fitness line
        fig.add_trace(
            go.Scatter(
                x=generations,
                y=best_fitness,
                name='Best Fitness',
                line=dict(color=CRISPRTheme.COLORS['success'], width=3),
                mode='lines+markers'
            )
        )

        # Average fitness line
        fig.add_trace(
            go.Scatter(
                x=generations,
                y=avg_fitness,
                name='Average Fitness',
                line=dict(color=CRISPRTheme.COLORS['info'], width=2),
                mode='lines'
            )
        )

        # Fill between
        fig.add_trace(
            go.Scatter(
                x=generations + generations[::-1],
                y=best_fitness + avg_fitness[::-1],
                fill='tonexty',
                fillcolor='rgba(116, 185, 255, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                name='Fitness Range'
            )
        )

        fig.update_layout(
            title=title,
            height=height,
            xaxis_title="Generation",
            yaxis_title="Fitness Score",
            template=CRISPRTheme.TEMPLATE
        )

        return fig

    @staticmethod
    def create_parameter_distribution(
        parameter_data: Dict[str, List[float]],
        title: str = "Parameter Distribution",
        height: int = 400
    ) -> go.Figure:
        """
        📊 Create parameter distribution visualization
        
        Args:
            parameter_data: Dict of parameter names and value lists
            title: Chart title
            height: Chart height
            
        Returns:
            Parameter distribution figure
        """
        fig = go.Figure()

        colors = CRISPRTheme.get_color_scale(len(parameter_data))

        for i, (param_name, values) in enumerate(parameter_data.items()):
            fig.add_trace(
                go.Box(
                    y=values,
                    name=param_name,
                    boxpoints='outliers',
                    marker_color=colors[i],
                    line_color=CRISPRTheme.COLORS['dark']
                )
            )

        fig.update_layout(
            title=title,
            height=height,
            yaxis_title="Parameter Value",
            template=CRISPRTheme.TEMPLATE
        )

        return fig

    @staticmethod
    def create_genome_health_radar(
        health_metrics: Dict[str, float],
        title: str = "Genome Health",
        height: int = 400
    ) -> go.Figure:
        """
        🎯 Create genome health radar chart
        
        Args:
            health_metrics: Dict of health metric names and scores
            title: Chart title
            height: Chart height
            
        Returns:
            Genome health radar figure
        """
        categories = list(health_metrics.keys())
        values = list(health_metrics.values())

        # Close the radar chart
        categories += [categories[0]]
        values += [values[0]]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                fillcolor='rgba(70, 130, 180, 0.4)',
                line=dict(color=CRISPRTheme.COLORS['adenine'], width=2),
                name='Health Score'
            )
        )

        fig.update_layout(
            title=title,
            height=height,
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            template=CRISPRTheme.TEMPLATE
        )

        return fig


class AnomalyVisualizer:
    """
    🔍 Anomaly Detection Visualization
    
    Components for visualizing anomaly detection results,
    outlier analysis, and system health monitoring.
    """

    @staticmethod
    def create_anomaly_timeline(
        timestamps: List[datetime],
        scores: List[float],
        threshold: float = 0.8,
        anomalies: Optional[List[bool]] = None,
        title: str = "Anomaly Detection Timeline",
        height: int = 400
    ) -> go.Figure:
        """
        ⏰ Create anomaly detection timeline
        
        Args:
            timestamps: List of timestamps
            scores: Anomaly scores
            threshold: Anomaly threshold
            anomalies: Boolean list of anomaly detections
            title: Chart title
            height: Chart height
            
        Returns:
            Anomaly timeline figure
        """
        fig = go.Figure()

        # Anomaly scores
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=scores,
                mode='lines+markers',
                name='Anomaly Score',
                line=dict(color=CRISPRTheme.COLORS['info'], width=2),
                marker=dict(size=4)
            )
        )

        # Threshold line
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color=CRISPRTheme.COLORS['warning'],
            annotation_text=f"Threshold ({threshold})"
        )

        # Highlight anomalies
        if anomalies:
            anomaly_times = [t for t, a in zip(timestamps, anomalies) if a]
            anomaly_scores = [s for s, a in zip(scores, anomalies) if a]

            if anomaly_times:
                fig.add_trace(
                    go.Scatter(
                        x=anomaly_times,
                        y=anomaly_scores,
                        mode='markers',
                        name='Detected Anomalies',
                        marker=dict(
                            color=CRISPRTheme.COLORS['danger'],
                            size=12,
                            symbol='diamond'
                        )
                    )
                )

        # Background coloring for anomaly regions
        anomaly_regions = []
        if anomalies:
            in_anomaly = False
            start_time = None

            for i, (time, is_anomaly) in enumerate(zip(timestamps, anomalies)):
                if is_anomaly and not in_anomaly:
                    start_time = time
                    in_anomaly = True
                elif not is_anomaly and in_anomaly:
                    anomaly_regions.append((start_time, timestamps[i-1]))
                    in_anomaly = False

            # Handle case where anomaly extends to end
            if in_anomaly:
                anomaly_regions.append((start_time, timestamps[-1]))

        # Add anomaly background regions
        for start, end in anomaly_regions:
            fig.add_vrect(
                x0=start,
                x1=end,
                fillcolor="rgba(220, 48, 85, 0.1)",
                layer="below",
                line_width=0
            )

        fig.update_layout(
            title=title,
            height=height,
            xaxis_title="Time",
            yaxis_title="Anomaly Score",
            template=CRISPRTheme.TEMPLATE
        )

        return fig

    @staticmethod
    def create_anomaly_heatmap(
        feature_scores: pd.DataFrame,
        title: str = "Feature Anomaly Heatmap",
        height: int = 500
    ) -> go.Figure:
        """
        🔥 Create feature-based anomaly heatmap
        
        Args:
            feature_scores: DataFrame with features as columns, time as rows
            title: Chart title
            height: Chart height
            
        Returns:
            Anomaly heatmap figure
        """
        fig = go.Figure(data=go.Heatmap(
            z=feature_scores.values,
            x=feature_scores.columns,
            y=feature_scores.index,
            colorscale='Reds',
            zmin=0,
            zmax=1,
            colorbar=dict(title="Anomaly Score"),
            hoverongaps=False
        ))

        fig.update_layout(
            title=title,
            height=height,
            xaxis_title="Features",
            yaxis_title="Time",
            template=CRISPRTheme.TEMPLATE
        )

        return fig


# Export all visualizer classes
__all__ = [
    'CRISPRTheme',
    'TimeSeriesVisualizer',
    'RiskVisualizer',
    'GenomeVisualizer',
    'AnomalyVisualizer'
]
