#!/usr/bin/env python3
"""
Executive PDF Report Generator for CRISPR-FinAI
Generates a professional PDF report with summary statistics, key visualizations, and insights.
"""

import sys
from pathlib import Path

# Add repo root to path for imports
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for PDF generation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from datetime import datetime
import json

# Use a clean, professional style
plt.style.use('seaborn-v0_8-darkgrid')

class ExecutivePDFGenerator:
    """Generate executive PDF report for CRISPR-FinAI results."""

    def __init__(self, base_dir='poc/scale_results', quick_dir='poc/scale_results_quick',
                 extended_metrics_path='poc/presentation_v2/extended_metrics.csv',
                 ga_reports_path='poc/scale_results_quick/ga_reports.jsonl'):
        self.base_dir = Path(base_dir)
        self.quick_dir = Path(quick_dir)
        self.extended_metrics_path = Path(extended_metrics_path)
        self.ga_reports_path = Path(ga_reports_path)

        # Load data
        self.baseline_df = pd.read_csv(self.base_dir / 'scale_compare_results.csv')
        self.quick_df = pd.read_csv(self.quick_dir / 'scale_compare_results.csv')

        # Load extended metrics and pivot for easier access
        extended_raw = pd.read_csv(self.extended_metrics_path)

        # Pivot to have baseline and GA columns
        baseline = extended_raw[extended_raw['type'] == 'Baseline'].copy()
        ga = extended_raw[extended_raw['type'] == 'GA-Optimized'].copy()

        # Merge baseline and GA
        self.extended_metrics = pd.merge(
            baseline, ga,
            on=['symbol', 'model'],
            suffixes=('_baseline', '_ga')
        )

        # Calculate improvements
        self.extended_metrics['sharpe_improvement'] = (
            self.extended_metrics['sharpe_ga'] - self.extended_metrics['sharpe_baseline']
        )
        self.extended_metrics['sortino_improvement'] = (
            self.extended_metrics['sortino_ga'] - self.extended_metrics['sortino_baseline']
        )
        self.extended_metrics['drawdown_improvement'] = (
            self.extended_metrics['max_drawdown_ga'] - self.extended_metrics['max_drawdown_baseline']
        )

        # Calculate composite score
        self.extended_metrics['composite_score'] = (
            self.extended_metrics['sharpe_improvement'] * 0.4 +
            self.extended_metrics['sortino_improvement'] * 0.3 +
            (-self.extended_metrics['drawdown_improvement']) * 0.3
        )

        # Load GA reports if available
        self.ga_reports = []
        if self.ga_reports_path.exists():
            with open(self.ga_reports_path) as f:
                for line in f:
                    self.ga_reports.append(json.loads(line.strip()))

        # Calculate simple improvements for summary
        self._calculate_improvements()

    def _calculate_improvements(self):
        """Calculate improvement metrics."""
        merged = pd.merge(
            self.baseline_df[['symbol', 'model', 'sharpe']],
            self.quick_df[['symbol', 'model', 'sharpe']],
            on=['symbol', 'model'],
            suffixes=('_baseline', '_ga')
        )
        merged['sharpe_improvement'] = merged['sharpe_ga'] - merged['sharpe_baseline']
        merged['sharpe_pct_improvement'] = (merged['sharpe_improvement'] / merged['sharpe_baseline'].abs()) * 100
        self.improvements = merged

    def _add_cover_page(self, pdf):
        """Add professional cover page."""
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Title
        fig.text(0.5, 0.75, 'CRISPR-FinAI', ha='center', fontsize=48, fontweight='bold',
                color='#667eea')
        fig.text(0.5, 0.68, 'Executive Performance Report', ha='center', fontsize=24,
                color='#555')

        # Subtitle
        fig.text(0.5, 0.60, 'Genetic Algorithm Optimization Results', ha='center',
                fontsize=16, style='italic', color='#888')

        # Separator line
        line = Rectangle((0.15, 0.55), 0.7, 0.002, transform=fig.transFigure,
                        color='#667eea', alpha=0.5)
        fig.add_artist(line)

        # Key metrics summary
        top_model = self.improvements.nlargest(1, 'sharpe_improvement').iloc[0]
        total_models = len(self.improvements)
        improved_models = len(self.improvements[self.improvements['sharpe_improvement'] > 0])
        avg_improvement = self.improvements['sharpe_improvement'].mean()

        metrics_y = 0.45
        fig.text(0.5, metrics_y, 'EXECUTIVE SUMMARY', ha='center', fontsize=14,
                fontweight='bold', color='#333')

        metrics_y -= 0.08
        fig.text(0.25, metrics_y, 'Models Tested:', ha='right', fontsize=12, color='#555')
        fig.text(0.26, metrics_y, f'{total_models}', ha='left', fontsize=12,
                fontweight='bold', color='#333')

        metrics_y -= 0.05
        fig.text(0.25, metrics_y, 'Models Improved:', ha='right', fontsize=12, color='#555')
        fig.text(0.26, metrics_y, f'{improved_models}', ha='left', fontsize=12,
                fontweight='bold', color='#27ae60')

        metrics_y -= 0.05
        fig.text(0.25, metrics_y, 'Avg Improvement:', ha='right', fontsize=12, color='#555')
        fig.text(0.26, metrics_y, f'+{avg_improvement:.3f}', ha='left', fontsize=12,
                fontweight='bold', color='#27ae60')

        metrics_y -= 0.05
        fig.text(0.25, metrics_y, 'Top Performer:', ha='right', fontsize=12, color='#555')
        fig.text(0.26, metrics_y, f'{top_model["symbol"]} {top_model["model"]}',
                ha='left', fontsize=12, fontweight='bold', color='#667eea')

        metrics_y -= 0.05
        fig.text(0.25, metrics_y, 'Best Improvement:', ha='right', fontsize=12, color='#555')
        fig.text(0.26, metrics_y, f'+{top_model["sharpe_improvement"]:.3f} Sharpe',
                ha='left', fontsize=12, fontweight='bold', color='#f39c12')

        # Footer
        fig.text(0.5, 0.15, f'Generated: {datetime.now().strftime("%B %d, %Y")}',
                ha='center', fontsize=10, color='#888')
        fig.text(0.5, 0.12, 'CONFIDENTIAL - For Internal Use Only',
                ha='center', fontsize=10, style='italic', color='#aaa')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _add_executive_overview(self, pdf):
        """Add executive overview page with key insights."""
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Title
        fig.text(0.5, 0.95, 'Executive Overview', ha='center', fontsize=20,
                fontweight='bold', color='#333')

        # Section: Key Findings
        y_pos = 0.88
        fig.text(0.1, y_pos, '🎯 Key Findings', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        findings = [
            f"• Tested {len(self.improvements)} symbol-model combinations across 3 assets (AAPL, MSFT, AMZN)",
            f"• {len(self.improvements[self.improvements['sharpe_improvement'] > 0])} models showed improvement with GA optimization",
            f"• Average Sharpe improvement: {self.improvements['sharpe_improvement'].mean():.3f}",
            f"• Best performer: {self.improvements.nlargest(1, 'sharpe_improvement').iloc[0]['symbol']} "
            f"{self.improvements.nlargest(1, 'sharpe_improvement').iloc[0]['model']} "
            f"(+{self.improvements.nlargest(1, 'sharpe_improvement').iloc[0]['sharpe_improvement']:.3f})",
        ]

        for finding in findings:
            fig.text(0.12, y_pos, finding, fontsize=10, color='#555', wrap=True)
            y_pos -= 0.04

        # Section: Methodology
        y_pos -= 0.03
        fig.text(0.1, y_pos, '🔬 Methodology', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        methodology = [
            "• Baseline: Standard ARIMA, Random Forest, and Naive Momentum strategies",
            "• Optimization: Genetic Algorithm with 20 generations, population size 50",
            "• Evaluation: Out-of-sample testing with 5-year historical data (2018-2023)",
            "• Metrics: Sharpe ratio, Sortino ratio, Calmar ratio, maximum drawdown, win rate",
            "• Self-Healing: Drift detection and automatic signal smoothing repair",
        ]

        for method in methodology:
            fig.text(0.12, y_pos, method, fontsize=10, color='#555')
            y_pos -= 0.04

        # Section: Risk Metrics Summary
        y_pos -= 0.03
        fig.text(0.1, y_pos, '⚠️ Risk Metrics Summary', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        # Get top 3 by composite score
        top_3 = self.extended_metrics.nlargest(3, 'composite_score')

        risk_summary = [
            "Top 3 Models by Composite Score:",
            f"  1. {top_3.iloc[0]['symbol']} {top_3.iloc[0]['model']}: {top_3.iloc[0]['composite_score']:.3f}",
            f"  2. {top_3.iloc[1]['symbol']} {top_3.iloc[1]['model']}: {top_3.iloc[1]['composite_score']:.3f}",
            f"  3. {top_3.iloc[2]['symbol']} {top_3.iloc[2]['model']}: {top_3.iloc[2]['composite_score']:.3f}",
            "",
            f"Best Sharpe Ratio: {self.extended_metrics.nlargest(1, 'sharpe_ga').iloc[0]['sharpe_ga']:.3f} "
            f"({self.extended_metrics.nlargest(1, 'sharpe_ga').iloc[0]['symbol']} "
            f"{self.extended_metrics.nlargest(1, 'sharpe_ga').iloc[0]['model']})",
            f"Best Win Rate: {self.extended_metrics.nlargest(1, 'win_rate_ga').iloc[0]['win_rate_ga']:.1f}% "
            f"({self.extended_metrics.nlargest(1, 'win_rate_ga').iloc[0]['symbol']} "
            f"{self.extended_metrics.nlargest(1, 'win_rate_ga').iloc[0]['model']})",
            f"Lowest Max Drawdown: {self.extended_metrics.nsmallest(1, 'max_drawdown_ga').iloc[0]['max_drawdown_ga']:.1f}% "
            f"({self.extended_metrics.nsmallest(1, 'max_drawdown_ga').iloc[0]['symbol']} "
            f"{self.extended_metrics.nsmallest(1, 'max_drawdown_ga').iloc[0]['model']})",
        ]

        for summary in risk_summary:
            fig.text(0.12, y_pos, summary, fontsize=10, color='#555')
            y_pos -= 0.04

        # Section: Recommendations
        y_pos -= 0.03
        fig.text(0.1, y_pos, '💡 Recommendations', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        recommendations = [
            "• Deploy top 3 models to production with weighted allocation",
            "• Implement continuous monitoring with drift detection",
            "• Set up automated GA re-optimization triggers when drift > 0.3",
            "• Use ensemble approach combining naive_momentum + ARIMA for stability",
            "• Monitor AMZN models closely - showed strongest improvements",
        ]

        for rec in recommendations:
            fig.text(0.12, y_pos, rec, fontsize=10, color='#555')
            y_pos -= 0.04

        # Footer
        fig.text(0.5, 0.05, 'Page 2 of 6', ha='center', fontsize=9, color='#aaa')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _add_performance_comparison(self, pdf):
        """Add performance comparison visualization."""
        fig, axes = plt.subplots(2, 2, figsize=(8.5, 11))
        fig.suptitle('Performance Comparison: Baseline vs GA-Optimized',
                    fontsize=16, fontweight='bold', y=0.98)

        # Chart 1: Sharpe Ratio Comparison
        ax1 = axes[0, 0]
        top_5 = self.improvements.nlargest(5, 'sharpe_improvement')
        x_pos = np.arange(len(top_5))
        width = 0.35

        ax1.bar(x_pos - width/2, top_5['sharpe_baseline'], width,
               label='Baseline', color='#e74c3c', alpha=0.7)
        ax1.bar(x_pos + width/2, top_5['sharpe_ga'], width,
               label='GA-Optimized', color='#27ae60', alpha=0.7)

        ax1.set_xlabel('Symbol-Model', fontweight='bold')
        ax1.set_ylabel('Sharpe Ratio', fontweight='bold')
        ax1.set_title('Top 5 Improvements: Sharpe Ratio', fontweight='bold', pad=10)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels([f"{row['symbol']}\n{row['model'][:6]}"
                             for _, row in top_5.iterrows()], fontsize=8)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # Chart 2: Improvement Distribution
        ax2 = axes[0, 1]
        improvements = self.improvements['sharpe_improvement']
        colors = ['#27ae60' if x > 0 else '#e74c3c' for x in improvements]

        ax2.bar(range(len(improvements)), improvements, color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_xlabel('Model Index', fontweight='bold')
        ax2.set_ylabel('Sharpe Improvement', fontweight='bold')
        ax2.set_title('Improvement Distribution', fontweight='bold', pad=10)
        ax2.grid(axis='y', alpha=0.3)

        # Chart 3: Risk-Return Scatter
        ax3 = axes[1, 0]

        # Plot baseline
        for symbol in self.extended_metrics['symbol'].unique():
            symbol_data = self.extended_metrics[self.extended_metrics['symbol'] == symbol]
            ax3.scatter(symbol_data['max_drawdown_baseline'],
                       symbol_data['sharpe_baseline'],
                       alpha=0.5, s=100, marker='o', label=f'{symbol} Baseline')

        # Plot GA
        for symbol in self.extended_metrics['symbol'].unique():
            symbol_data = self.extended_metrics[self.extended_metrics['symbol'] == symbol]
            ax3.scatter(symbol_data['max_drawdown_ga'],
                       symbol_data['sharpe_ga'],
                       alpha=0.8, s=100, marker='*', label=f'{symbol} GA')

        ax3.set_xlabel('Max Drawdown (%)', fontweight='bold')
        ax3.set_ylabel('Sharpe Ratio', fontweight='bold')
        ax3.set_title('Risk-Return Profile', fontweight='bold', pad=10)
        ax3.legend(fontsize=7, loc='best')
        ax3.grid(alpha=0.3)

        # Chart 4: Win Rate Comparison
        ax4 = axes[1, 1]

        # Get models with win rate data
        win_rate_data = self.extended_metrics[['symbol', 'model', 'win_rate_baseline', 'win_rate_ga']].head(6)
        x_pos = np.arange(len(win_rate_data))

        ax4.bar(x_pos - width/2, win_rate_data['win_rate_baseline'], width,
               label='Baseline', color='#e74c3c', alpha=0.7)
        ax4.bar(x_pos + width/2, win_rate_data['win_rate_ga'], width,
               label='GA-Optimized', color='#27ae60', alpha=0.7)

        ax4.set_xlabel('Symbol-Model', fontweight='bold')
        ax4.set_ylabel('Win Rate (%)', fontweight='bold')
        ax4.set_title('Win Rate Comparison', fontweight='bold', pad=10)
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels([f"{row['symbol']}\n{row['model'][:6]}"
                            for _, row in win_rate_data.iterrows()], fontsize=8)
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        fig.text(0.5, 0.02, 'Page 3 of 6', ha='center', fontsize=9, color='#aaa')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _add_risk_metrics_page(self, pdf):
        """Add detailed risk metrics visualization."""
        fig, axes = plt.subplots(2, 2, figsize=(8.5, 11))
        fig.suptitle('Detailed Risk Metrics Analysis',
                    fontsize=16, fontweight='bold', y=0.98)

        # Chart 1: Sortino vs Sharpe
        ax1 = axes[0, 0]

        ax1.scatter(self.extended_metrics['sharpe_baseline'],
                   self.extended_metrics['sortino_baseline'],
                   alpha=0.6, s=100, c='#e74c3c', marker='o', label='Baseline')
        ax1.scatter(self.extended_metrics['sharpe_ga'],
                   self.extended_metrics['sortino_ga'],
                   alpha=0.6, s=100, c='#27ae60', marker='*', label='GA-Optimized')

        ax1.plot([0, 2], [0, 3], 'k--', alpha=0.3, linewidth=1)
        ax1.set_xlabel('Sharpe Ratio', fontweight='bold')
        ax1.set_ylabel('Sortino Ratio', fontweight='bold')
        ax1.set_title('Sharpe vs Sortino Ratio', fontweight='bold', pad=10)
        ax1.legend()
        ax1.grid(alpha=0.3)

        # Chart 2: Max Drawdown Comparison
        ax2 = axes[0, 1]

        top_6 = self.extended_metrics.nsmallest(6, 'max_drawdown_ga')
        x_pos = np.arange(len(top_6))
        width = 0.35

        ax2.bar(x_pos - width/2, top_6['max_drawdown_baseline'], width,
               label='Baseline', color='#e74c3c', alpha=0.7)
        ax2.bar(x_pos + width/2, top_6['max_drawdown_ga'], width,
               label='GA-Optimized', color='#27ae60', alpha=0.7)

        ax2.set_xlabel('Symbol-Model', fontweight='bold')
        ax2.set_ylabel('Max Drawdown (%)', fontweight='bold')
        ax2.set_title('Best Max Drawdown Performance', fontweight='bold', pad=10)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels([f"{row['symbol']}\n{row['model'][:6]}"
                            for _, row in top_6.iterrows()], fontsize=8)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

        # Chart 3: Calmar Ratio
        ax3 = axes[1, 0]

        top_6_calmar = self.extended_metrics.nlargest(6, 'calmar_ga')
        x_pos = np.arange(len(top_6_calmar))

        ax3.bar(x_pos - width/2, top_6_calmar['calmar_baseline'], width,
               label='Baseline', color='#e74c3c', alpha=0.7)
        ax3.bar(x_pos + width/2, top_6_calmar['calmar_ga'], width,
               label='GA-Optimized', color='#27ae60', alpha=0.7)

        ax3.set_xlabel('Symbol-Model', fontweight='bold')
        ax3.set_ylabel('Calmar Ratio', fontweight='bold')
        ax3.set_title('Top 6 Calmar Ratios', fontweight='bold', pad=10)
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels([f"{row['symbol']}\n{row['model'][:6]}"
                            for _, row in top_6_calmar.iterrows()], fontsize=8)
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)

        # Chart 4: Profit Factor
        ax4 = axes[1, 1]

        top_6_pf = self.extended_metrics.nlargest(6, 'profit_factor_ga')
        x_pos = np.arange(len(top_6_pf))

        ax4.bar(x_pos - width/2, top_6_pf['profit_factor_baseline'], width,
               label='Baseline', color='#e74c3c', alpha=0.7)
        ax4.bar(x_pos + width/2, top_6_pf['profit_factor_ga'], width,
               label='GA-Optimized', color='#27ae60', alpha=0.7)

        ax4.axhline(y=1.0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax4.set_xlabel('Symbol-Model', fontweight='bold')
        ax4.set_ylabel('Profit Factor', fontweight='bold')
        ax4.set_title('Top 6 Profit Factors', fontweight='bold', pad=10)
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels([f"{row['symbol']}\n{row['model'][:6]}"
                            for _, row in top_6_pf.iterrows()], fontsize=8)
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        fig.text(0.5, 0.02, 'Page 4 of 6', ha='center', fontsize=9, color='#aaa')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _add_model_ranking_page(self, pdf):
        """Add model ranking and consistency analysis."""
        fig = plt.figure(figsize=(8.5, 11))

        # Title
        fig.text(0.5, 0.96, 'Model Ranking & Consistency Analysis', ha='center',
                fontsize=16, fontweight='bold')

        # Top 10 ranking table
        top_10 = self.extended_metrics.nlargest(10, 'composite_score')

        # Create axes for table
        ax1 = fig.add_axes([0.1, 0.55, 0.8, 0.35])
        ax1.axis('tight')
        ax1.axis('off')

        # Prepare table data
        table_data = [['Rank', 'Symbol', 'Model', 'Composite\nScore', 'Sharpe\nImprv',
                      'Sortino\nImprv', 'DD\nImprv']]

        for idx, (_, row) in enumerate(top_10.iterrows(), 1):
            medal = '🥇' if idx == 1 else '🥈' if idx == 2 else '🥉' if idx == 3 else f'{idx}'
            table_data.append([
                medal,
                row['symbol'],
                row['model'][:12],
                f"{row['composite_score']:.3f}",
                f"+{row['sharpe_improvement']:.3f}",
                f"+{row['sortino_improvement']:.3f}",
                f"{row['drawdown_improvement']:.1f}%"
            ])

        table = ax1.table(cellText=table_data, cellLoc='center', loc='center',
                         colWidths=[0.08, 0.12, 0.18, 0.14, 0.14, 0.14, 0.12])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        # Style header row
        for i in range(len(table_data[0])):
            cell = table[(0, i)]
            cell.set_facecolor('#667eea')
            cell.set_text_props(weight='bold', color='white')

        # Color rows by rank
        for i in range(1, 4):  # Top 3
            for j in range(len(table_data[0])):
                cell = table[(i, j)]
                if i == 1:
                    cell.set_facecolor('#fff9e6')
                elif i == 2:
                    cell.set_facecolor('#f0f0f0')
                else:
                    cell.set_facecolor('#ffe6cc')

        # Consistency analysis chart
        ax2 = fig.add_axes([0.15, 0.15, 0.7, 0.3])

        # Group by model type
        model_groups = self.extended_metrics.groupby('model')['composite_score'].agg(['mean', 'std'])
        model_groups = model_groups.sort_values('mean', ascending=True)

        y_pos = np.arange(len(model_groups))
        colors_map = {'naive_momentum': '#27ae60', 'arima': '#3498db',
                     'random_forest': '#e67e22', 'crispr_adaptive': '#9b59b6'}
        colors = [colors_map.get(model, '#95a5a6') for model in model_groups.index]

        ax2.barh(y_pos, model_groups['mean'], xerr=model_groups['std'],
                color=colors, alpha=0.7, capsize=5)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(model_groups.index)
        ax2.set_xlabel('Composite Score (Mean ± Std)', fontweight='bold')
        ax2.set_title('Model Consistency Across Symbols', fontweight='bold', pad=10)
        ax2.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax2.grid(axis='x', alpha=0.3)

        # Footer
        fig.text(0.5, 0.05, 'Page 5 of 6', ha='center', fontsize=9, color='#aaa')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _add_conclusion_page(self, pdf):
        """Add conclusion and next steps."""
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Title
        fig.text(0.5, 0.95, 'Conclusions & Next Steps', ha='center', fontsize=20,
                fontweight='bold', color='#333')

        # Section: Key Achievements
        y_pos = 0.88
        fig.text(0.1, y_pos, '✅ Key Achievements', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        achievements = [
            f"• Successfully optimized {len(self.improvements[self.improvements['sharpe_improvement'] > 0])} out of {len(self.improvements)} models",
            f"• Maximum Sharpe improvement: +{self.improvements['sharpe_improvement'].max():.3f} "
            f"({self.improvements.nlargest(1, 'sharpe_improvement').iloc[0]['symbol']} "
            f"{self.improvements.nlargest(1, 'sharpe_improvement').iloc[0]['model']})",
            "• Implemented self-healing architecture with drift detection",
            "• Developed comprehensive risk metrics framework (7 metrics)",
            "• Created automated GA optimization pipeline",
        ]

        for achievement in achievements:
            fig.text(0.12, y_pos, achievement, fontsize=10, color='#555')
            y_pos -= 0.04

        # Section: Implementation Roadmap
        y_pos -= 0.03
        fig.text(0.1, y_pos, '🛣️ Implementation Roadmap', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        roadmap = [
            "Phase 1: Production Deployment (Q1 2025)",
            "  • Deploy top 3 models to production environment",
            "  • Set up real-time monitoring dashboard",
            "  • Implement automated alert system for drift detection",
            "",
            "Phase 2: Scaling & Enhancement (Q2 2025)",
            "  • Expand to 10+ symbols (S&P 500 constituents)",
            "  • Add reinforcement learning controller",
            "  • Implement MLflow for experiment tracking",
            "",
            "Phase 3: Advanced Features (Q3 2025)",
            "  • Multi-asset portfolio optimization",
            "  • Risk parity allocation",
            "  • Transaction cost modeling",
        ]

        for item in roadmap:
            fig.text(0.12, y_pos, item, fontsize=10, color='#555')
            y_pos -= 0.035

        # Section: Risk Considerations
        y_pos -= 0.02
        fig.text(0.1, y_pos, '⚠️ Risk Considerations', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        risks = [
            "• Market regime changes: Models trained on 2018-2023 data",
            "• Overfitting: Continuously monitor out-of-sample performance",
            "• Slippage & costs: Real trading costs may differ from backtest",
            "• Model drift: Implement quarterly re-optimization schedule",
            "• Concentration risk: Diversify across multiple models & symbols",
        ]

        for risk in risks:
            fig.text(0.12, y_pos, risk, fontsize=10, color='#555')
            y_pos -= 0.04

        # Section: Contact & Support
        y_pos -= 0.03
        fig.text(0.1, y_pos, '📞 Contact & Support', fontsize=14, fontweight='bold', color='#667eea')
        y_pos -= 0.05

        contact = [
            "For questions or support regarding this report:",
            "",
            "📧 Email: crispr-finai@example.com",
            "🌐 Dashboard: http://localhost:8000/dashboard_v2.html",
            "📁 Repository: /home/mehmetcelik/crispr/",
        ]

        for info in contact:
            fig.text(0.12, y_pos, info, fontsize=10, color='#555')
            y_pos -= 0.035

        # Disclaimer box
        disclaimer_y = 0.15
        disclaimer_box = Rectangle((0.1, disclaimer_y - 0.08), 0.8, 0.10,
                                  transform=fig.transFigure,
                                  facecolor='#fff3cd', edgecolor='#f39c12',
                                  linewidth=2)
        fig.add_artist(disclaimer_box)

        fig.text(0.5, disclaimer_y - 0.01, 'DISCLAIMER', ha='center', fontsize=12,
                fontweight='bold', color='#856404')
        fig.text(0.5, disclaimer_y - 0.04,
                'Past performance is not indicative of future results. This report is for informational',
                ha='center', fontsize=9, color='#856404')
        fig.text(0.5, disclaimer_y - 0.06,
                'purposes only and does not constitute investment advice.',
                ha='center', fontsize=9, color='#856404')

        # Footer
        fig.text(0.5, 0.03, 'Page 6 of 6', ha='center', fontsize=9, color='#aaa')
        fig.text(0.5, 0.01, f'© 2025 CRISPR-FinAI • Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                ha='center', fontsize=8, color='#aaa', style='italic')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def generate_pdf(self, output_path='poc/presentation_v2/CRISPR_Executive_Report.pdf'):
        """Generate the complete PDF report."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print("📄 Generating Executive PDF Report...")
        print(f"{'='*60}\n")

        with PdfPages(output_path) as pdf:
            print("📝 Adding cover page...")
            self._add_cover_page(pdf)

            print("📊 Adding executive overview...")
            self._add_executive_overview(pdf)

            print("📈 Adding performance comparison...")
            self._add_performance_comparison(pdf)

            print("⚠️  Adding risk metrics analysis...")
            self._add_risk_metrics_page(pdf)

            print("🏆 Adding model ranking...")
            self._add_model_ranking_page(pdf)

            print("✅ Adding conclusion page...")
            self._add_conclusion_page(pdf)

            # Set PDF metadata
            d = pdf.infodict()
            d['Title'] = 'CRISPR-FinAI Executive Performance Report'
            d['Author'] = 'CRISPR-FinAI System'
            d['Subject'] = 'Genetic Algorithm Optimization Results'
            d['Keywords'] = 'GA, Trading, CRISPR, Machine Learning, Finance'
            d['CreationDate'] = datetime.now()

        # Get file size
        file_size = output_path.stat().st_size / 1024  # KB

        print(f"\n{'='*60}")
        print("✅ Executive PDF report generated successfully!")
        print(f"{'='*60}")
        print(f"📂 Output file: {output_path}")
        print(f"📊 File size: {file_size:.1f} KB")
        print("📄 Total pages: 6")
        print(f"\n🚀 Open with: xdg-open {output_path}")
        print(f"{'='*60}\n")

        return output_path


def main():
    """Main execution function."""
    generator = ExecutivePDFGenerator()
    pdf_path = generator.generate_pdf()
    return pdf_path


if __name__ == '__main__':
    main()
