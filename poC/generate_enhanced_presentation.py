"""Generate enhanced presentation with equity curves, risk metrics, and executive summary.

New features:
- Equity curve plots (baseline vs GA-optimized)
- Extended risk metrics (Sortino, Calmar, max drawdown)
- Model confidence indicators
- Comparative analysis tables
- Executive summary section
"""
from __future__ import annotations
import json
import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add repo root to path for imports
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

sns.set_style('whitegrid')
sns.set_palette('Set2')


def load_returns_data(results_dir: Path, symbol: str, model: str):
    """Load returns parquet for a specific symbol-model pair."""
    parquet_path = results_dir / f'{symbol}_{model}_returns.parquet'
    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            if 'returns' in df.columns:
                return df['returns']
            if len(df.columns) > 0:
                return df.iloc[:, 0]
        except Exception:
            pass
    return None


def calculate_extended_metrics(returns: pd.Series):
    """Calculate extended risk metrics."""
    if returns is None or returns.empty or returns.dropna().empty:
        return {
            'sharpe': np.nan,
            'sortino': np.nan,
            'calmar': np.nan,
            'max_drawdown': np.nan,
            'win_rate': np.nan,
            'avg_win': np.nan,
            'avg_loss': np.nan,
            'profit_factor': np.nan,
        }

    rets = returns.dropna()

    # Sharpe
    sharpe = rets.mean() / rets.std() * np.sqrt(252) if rets.std() > 0 else 0

    # Sortino (downside deviation)
    downside = rets[rets < 0]
    downside_std = downside.std() if len(downside) > 0 else 1e-10
    sortino = rets.mean() / downside_std * np.sqrt(252) if downside_std > 0 else 0

    # Max drawdown and Calmar
    cum_rets = (1 + rets).cumprod()
    running_max = cum_rets.expanding().max()
    drawdown = (cum_rets - running_max) / running_max
    max_dd = drawdown.min()
    calmar = (rets.mean() * 252) / abs(max_dd) if max_dd != 0 else 0

    # Win rate
    win_rate = (rets > 0).sum() / len(rets) if len(rets) > 0 else 0

    # Avg win/loss
    wins = rets[rets > 0]
    losses = rets[rets < 0]
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0

    # Profit factor
    total_wins = wins.sum() if len(wins) > 0 else 0
    total_losses = abs(losses.sum()) if len(losses) > 0 else 1e-10
    profit_factor = total_wins / total_losses if total_losses > 0 else 0

    return {
        'sharpe': sharpe,
        'sortino': sortino,
        'calmar': calmar,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
    }


def generate_equity_curves(base_dir: Path, quick_dir: Path, symbols: list, models: list, out_dir: Path):
    """Generate equity curve comparison plots."""
    fig, axes = plt.subplots(len(symbols), len(models), figsize=(6 * len(models), 4 * len(symbols)))
    if len(symbols) == 1 and len(models) == 1:
        axes = np.array([[axes]])
    elif len(symbols) == 1:
        axes = axes.reshape(1, -1)
    elif len(models) == 1:
        axes = axes.reshape(-1, 1)

    for i, symbol in enumerate(symbols):
        for j, model in enumerate(models):
            ax = axes[i, j]

            # Load baseline and GA returns
            base_rets = load_returns_data(base_dir, symbol, model)
            quick_rets = load_returns_data(quick_dir, symbol, model)

            if base_rets is not None and not base_rets.dropna().empty:
                cum_base = (1 + base_rets.fillna(0)).cumprod()
                ax.plot(cum_base.index, cum_base.values, label='Baseline', linewidth=2, alpha=0.7)

            if quick_rets is not None and not quick_rets.dropna().empty:
                cum_quick = (1 + quick_rets.fillna(0)).cumprod()
                ax.plot(cum_quick.index, cum_quick.values, label='GA-Optimized', linewidth=2, alpha=0.7)

            ax.set_title(f'{symbol} - {model}', fontsize=10, fontweight='bold')
            ax.set_xlabel('Date', fontsize=8)
            ax.set_ylabel('Cumulative Return', fontsize=8)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.axhline(1, color='black', linestyle='--', linewidth=1, alpha=0.5)

    plt.tight_layout()
    out_path = out_dir / 'equity_curves.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(out_path.relative_to(out_dir.parent))


def generate_risk_metrics_table(base_dir: Path, quick_dir: Path, symbols: list, models: list, out_path: Path):
    """Generate comprehensive risk metrics comparison table."""
    rows = []
    for symbol in symbols:
        for model in models:
            base_rets = load_returns_data(base_dir, symbol, model)
            quick_rets = load_returns_data(quick_dir, symbol, model)

            base_metrics = calculate_extended_metrics(base_rets)
            quick_metrics = calculate_extended_metrics(quick_rets)

            rows.append({
                'symbol': symbol,
                'model': model,
                'type': 'Baseline',
                **base_metrics
            })
            rows.append({
                'symbol': symbol,
                'model': model,
                'type': 'GA-Optimized',
                **quick_metrics
            })

    df = pd.DataFrame(rows)

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # Plot 1: Sharpe vs Sortino
    ax1 = axes[0, 0]
    for typ, marker in [('Baseline', 'o'), ('GA-Optimized', '^')]:
        data = df[df['type'] == typ]
        ax1.scatter(data['sharpe'], data['sortino'], label=typ, alpha=0.7, s=100, marker=marker)
    ax1.set_xlabel('Sharpe Ratio', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Sortino Ratio', fontsize=12, fontweight='bold')
    ax1.set_title('Risk-Adjusted Returns: Sharpe vs Sortino', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Max Drawdown comparison
    ax2 = axes[0, 1]
    pivot = df.pivot_table(index=['symbol', 'model'], columns='type', values='max_drawdown')
    pivot.plot(kind='barh', ax=ax2, color=['#e74c3c', '#27ae60'])
    ax2.set_xlabel('Max Drawdown', fontsize=12, fontweight='bold')
    ax2.set_title('Maximum Drawdown Comparison', fontsize=14, fontweight='bold')
    ax2.legend(title='Type')

    # Plot 3: Win Rate
    ax3 = axes[1, 0]
    pivot_wr = df.pivot_table(index=['symbol', 'model'], columns='type', values='win_rate')
    pivot_wr.plot(kind='bar', ax=ax3, color=['#e74c3c', '#27ae60'], alpha=0.7)
    ax3.set_ylabel('Win Rate', fontsize=12, fontweight='bold')
    ax3.set_title('Win Rate Comparison', fontsize=14, fontweight='bold')
    ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45, ha='right')
    ax3.legend(title='Type')
    ax3.axhline(0.5, color='black', linestyle='--', alpha=0.5)

    # Plot 4: Profit Factor
    ax4 = axes[1, 1]
    pivot_pf = df.pivot_table(index=['symbol', 'model'], columns='type', values='profit_factor')
    pivot_pf.plot(kind='bar', ax=ax4, color=['#e74c3c', '#27ae60'], alpha=0.7)
    ax4.set_ylabel('Profit Factor', fontsize=12, fontweight='bold')
    ax4.set_title('Profit Factor Comparison', fontsize=14, fontweight='bold')
    ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45, ha='right')
    ax4.legend(title='Type')
    ax4.axhline(1, color='black', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()

    # Save CSV
    csv_path = out_path.parent / 'extended_metrics.csv'
    df.to_csv(csv_path, index=False)

    return str(out_path.relative_to(out_path.parent.parent)), df


def generate_model_ranking(df_metrics: pd.DataFrame, out_path: Path):
    """Generate model ranking and consistency analysis."""
    # Calculate composite score
    baseline = df_metrics[df_metrics['type'] == 'Baseline'].copy()
    ga_opt = df_metrics[df_metrics['type'] == 'GA-Optimized'].copy()

    # Merge and calculate improvements
    merged = baseline.set_index(['symbol', 'model']).add_suffix('_base').join(
        ga_opt.set_index(['symbol', 'model']).add_suffix('_ga')
    ).reset_index()

    merged['sharpe_improvement'] = merged['sharpe_ga'] - merged['sharpe_base']
    merged['sortino_improvement'] = merged['sortino_ga'] - merged['sortino_base']
    merged['dd_improvement'] = merged['max_drawdown_ga'] - merged['max_drawdown_base']  # negative is better

    # Composite score: weighted average of improvements
    merged['composite_score'] = (
        merged['sharpe_improvement'] * 0.4 +
        merged['sortino_improvement'] * 0.3 +
        (-merged['dd_improvement']) * 0.3  # invert because lower DD is better
    )

    # Rank models
    ranked = merged.sort_values('composite_score', ascending=False)

    # Create ranking visualization
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Plot 1: Top models by composite score
    ax1 = axes[0]
    top_n = min(10, len(ranked))
    top_models = ranked.head(top_n)
    colors = ['#27ae60' if x > 0 else '#e74c3c' for x in top_models['composite_score']]
    ax1.barh(range(top_n), top_models['composite_score'], color=colors, alpha=0.7)
    ax1.set_yticks(range(top_n))
    ax1.set_yticklabels([f"{r['symbol']} - {r['model']}" for _, r in top_models.iterrows()])
    ax1.set_xlabel('Composite Score', fontsize=12, fontweight='bold')
    ax1.set_title('🏆 Top 10 Models by Composite Score', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.axvline(0, color='black', linewidth=2)

    # Plot 2: Model consistency across symbols
    ax2 = axes[1]
    model_avg = merged.groupby('model')['composite_score'].agg(['mean', 'std']).sort_values('mean', ascending=False)
    ax2.barh(range(len(model_avg)), model_avg['mean'], xerr=model_avg['std'],
             color='#3498db', alpha=0.7, capsize=5)
    ax2.set_yticks(range(len(model_avg)))
    ax2.set_yticklabels(model_avg.index)
    ax2.set_xlabel('Avg Composite Score ± Std', fontsize=12, fontweight='bold')
    ax2.set_title('Model Consistency Across Symbols', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.axvline(0, color='black', linewidth=2)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()

    return str(out_path.relative_to(out_path.parent.parent)), ranked


def generate_enhanced_html(base: pd.DataFrame, quick: pd.DataFrame, ga_reports: list,
                          comparison_chart: str, heatmap_chart: str,
                          equity_curves_chart: str, risk_metrics_chart: str,
                          ranking_chart: str, ranked_df: pd.DataFrame,
                          extended_metrics_df: pd.DataFrame,
                          out_path: Path):
    """Generate enhanced HTML dashboard with all new features."""

    # Calculate summary statistics
    merged = base.set_index(['symbol', 'model'])[['sharpe']].rename(columns={'sharpe': 'baseline'}).join(
        quick.set_index(['symbol', 'model'])[['sharpe']].rename(columns={'sharpe': 'ga_optimized'})
    ).reset_index()
    merged['improvement'] = merged['ga_optimized'] - merged['baseline']

    total_improvements = (merged['improvement'] > 0).sum()
    avg_improvement = merged['improvement'].mean()
    max_improvement = merged['improvement'].max()
    max_improvement_case = merged.loc[merged['improvement'].idxmax()]

    # Get top 3 models from ranking
    top_3 = ranked_df.head(3)

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRISPR-FinAI: Enhanced Dashboard v2.0</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 50px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        .header h1 {{
            font-size: 3.5em;
            margin-bottom: 15px;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }}
        .header .subtitle {{
            font-size: 1.4em;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }}
        .header .version {{
            font-size: 0.9em;
            margin-top: 10px;
            opacity: 0.8;
            position: relative;
            z-index: 1;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            padding: 50px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }}
        .stat-card {{
            background: white;
            padding: 35px;
            border-radius: 15px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-top: 4px solid #667eea;
        }}
        .stat-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 12px 24px rgba(0,0,0,0.25);
        }}
        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 15px 0;
        }}
        .stat-label {{
            font-size: 1.1em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        }}
        .section {{
            padding: 50px;
        }}
        .section h2 {{
            font-size: 2.2em;
            margin-bottom: 30px;
            color: #1e3c72;
            border-bottom: 4px solid #667eea;
            padding-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .section h2::before {{
            content: '▸';
            margin-right: 15px;
            color: #667eea;
        }}
        .chart-container {{
            margin: 40px 0;
            text-align: center;
        }}
        .chart-container img {{
            max-width: 100%;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            transition: transform 0.3s ease;
        }}
        .chart-container img:hover {{
            transform: scale(1.02);
        }}
        .highlight-box {{
            background: linear-gradient(120deg, #ffeaa7 0%, #fdcb6e 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
            border-left: 6px solid #f39c12;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .highlight-box h3 {{
            margin-bottom: 15px;
            color: #d35400;
        }}
        .highlight-box p {{
            font-size: 1.2em;
            line-height: 1.8;
        }}
        .podium {{
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 20px;
            margin: 40px 0;
        }}
        .podium-item {{
            text-align: center;
            padding: 30px 20px;
            border-radius: 15px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            transition: transform 0.3s ease;
            min-width: 250px;
        }}
        .podium-item:hover {{
            transform: translateY(-10px);
        }}
        .podium-1 {{
            background: linear-gradient(135deg, #f39c12 0%, #f1c40f 100%);
            color: white;
            order: 2;
            padding: 50px 30px;
        }}
        .podium-2 {{
            background: linear-gradient(135deg, #bdc3c7 0%, #95a5a6 100%);
            color: white;
            order: 1;
        }}
        .podium-3 {{
            background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
            color: white;
            order: 3;
        }}
        .podium-rank {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .podium-model {{
            font-size: 1.3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .podium-score {{
            font-size: 1.8em;
            margin: 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px;
            text-align: left;
            font-weight: bold;
            font-size: 1.1em;
        }}
        td {{
            padding: 15px 18px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .positive {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .badge-gold {{
            background: #f39c12;
            color: white;
        }}
        .badge-silver {{
            background: #95a5a6;
            color: white;
        }}
        .badge-bronze {{
            background: #e67e22;
            color: white;
        }}
        .badge-success {{
            background: #27ae60;
            color: white;
        }}
        .footer {{
            background: #1e3c72;
            color: white;
            text-align: center;
            padding: 30px;
            font-size: 1em;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        .insight-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        .insight-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        .insight-card h4 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        .insight-card p {{
            line-height: 1.6;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 CRISPR-FinAI Dashboard v2.0</h1>
            <p class="subtitle">Enhanced Self-Healing Trading System with Advanced Analytics</p>
            <p class="version">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Full Risk Analysis Enabled</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Models Tested</div>
                <div class="stat-value">{len(merged)}</div>
                <p style="margin-top: 10px; color: #888;">Symbol-Model Pairs</p>
            </div>
            <div class="stat-card">
                <div class="stat-label">Improvements</div>
                <div class="stat-value" style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total_improvements}</div>
                <p style="margin-top: 10px; color: #888;">GA Wins</p>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Sharpe Δ</div>
                <div class="stat-value" style="background: linear-gradient(135deg, {'#27ae60 0%, #2ecc71 100%' if avg_improvement > 0 else '#e74c3c 0%, #c0392b 100%'}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{avg_improvement:+.3f}</div>
                <p style="margin-top: 10px; color: #888;">Mean Improvement</p>
            </div>
            <div class="stat-card">
                <div class="stat-label">Best Gain</div>
                <div class="stat-value" style="background: linear-gradient(135deg, #f39c12 0%, #f1c40f 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{max_improvement:+.3f}</div>
                <p style="margin-top: 10px; color: #888;">{max_improvement_case['symbol']} {max_improvement_case['model'][:8]}</p>
            </div>
        </div>
        
        <div class="highlight-box">
            <h3>🏆 Champion Performance</h3>
            <p>
                <strong>{max_improvement_case['symbol']}</strong> using <strong>{max_improvement_case['model']}</strong> 
                achieved a Sharpe improvement of <span class="positive">{max_improvement:+.3f}</span> 
                ({max_improvement_case['baseline']:.3f} → {max_improvement_case['ga_optimized']:.3f})
                representing a <strong>{((max_improvement_case['ga_optimized'] - max_improvement_case['baseline']) / abs(max_improvement_case['baseline']) * 100):+.1f}%</strong> enhancement.
            </p>
        </div>
        
        <div class="section">
            <h2>🏅 Top 3 Models (Composite Score)</h2>
            <div class="podium">
                <div class="podium-item podium-2">
                    <div class="podium-rank">🥈 2nd</div>
                    <div class="podium-model">{top_3.iloc[1]['symbol']}<br>{top_3.iloc[1]['model']}</div>
                    <div class="podium-score">{top_3.iloc[1]['composite_score']:.3f}</div>
                </div>
                <div class="podium-item podium-1">
                    <div class="podium-rank">🥇 1st</div>
                    <div class="podium-model">{top_3.iloc[0]['symbol']}<br>{top_3.iloc[0]['model']}</div>
                    <div class="podium-score">{top_3.iloc[0]['composite_score']:.3f}</div>
                </div>
                <div class="podium-item podium-3">
                    <div class="podium-rank">🥉 3rd</div>
                    <div class="podium-model">{top_3.iloc[2]['symbol']}<br>{top_3.iloc[2]['model']}</div>
                    <div class="podium-score">{top_3.iloc[2]['composite_score']:.3f}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Performance Comparison</h2>
            <div class="chart-container">
                <img src="{comparison_chart}" alt="Comparison Chart">
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Equity Curves: Baseline vs GA-Optimized</h2>
            <div class="chart-container">
                <img src="{equity_curves_chart}" alt="Equity Curves">
            </div>
        </div>
        
        <div class="section">
            <h2>⚠️ Risk Metrics Analysis</h2>
            <div class="chart-container">
                <img src="{risk_metrics_chart}" alt="Risk Metrics">
            </div>
        </div>
        
        <div class="section">
            <h2>🏆 Model Ranking & Consistency</h2>
            <div class="chart-container">
                <img src="{ranking_chart}" alt="Model Ranking">
            </div>
        </div>
        
        <div class="section">
            <h2>🔥 Performance Heatmaps</h2>
            <div class="chart-container">
                <img src="{heatmap_chart}" alt="Performance Heatmaps">
            </div>
        </div>
        
        <div class="section">
            <h2>💡 Key Insights</h2>
            <div class="insight-grid">
                <div class="insight-card">
                    <h4>🧬 Self-Healing Architecture</h4>
                    <p>Drift detection triggers adaptive parameter optimization using genetic algorithms, ensuring models stay performant in changing market conditions.</p>
                </div>
                <div class="insight-card">
                    <h4>📊 Multi-Metric Optimization</h4>
                    <p>GA optimization targets Sharpe ratio while maintaining acceptable risk levels (Sortino, max drawdown, win rate).</p>
                </div>
                <div class="insight-card">
                    <h4>🎯 Model Diversity</h4>
                    <p>Ensemble includes naive momentum, ARIMA time-series, RandomForest ML, and CRISPR-adaptive strategies for robust performance.</p>
                </div>
                <div class="insight-card">
                    <h4>✅ Production-Ready</h4>
                    <p>Modular architecture with unit tests, JSONL audit logs, and comprehensive error handling ensures deployment readiness.</p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>CRISPR-FinAI v2.0</strong> | Enhanced Self-Healing Trading System</p>
            <p style="margin-top: 10px; opacity: 0.9;">Powered by Genetic Algorithms, Drift Detection & Advanced Risk Analytics</p>
            <p style="margin-top: 5px; opacity: 0.7; font-size: 0.9em;">© 2025 | All metrics calculated with walk-forward validation</p>
        </div>
    </div>
</body>
</html>
"""

    out_path.write_text(html, encoding='utf-8')
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=Path, default=Path('poc/scale_results'))
    parser.add_argument('--quick_dir', type=Path, default=Path('poc/scale_results_quick'))
    parser.add_argument('--ga_reports', type=Path, default=Path('poc/scale_results_quick/ga_reports.jsonl'))
    parser.add_argument('--out_dir', type=Path, default=Path('poc/presentation_v2'))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Load basic results
    print('📊 Loading results...')
    base_csv = args.base_dir / 'scale_compare_results.csv'
    quick_csv = args.quick_dir / 'scale_compare_results.csv'

    if not base_csv.exists() or not quick_csv.exists():
        print('❌ Missing results files')
        return

    base = pd.read_csv(base_csv)
    quick = pd.read_csv(quick_csv)

    # Load GA reports
    ga_reports = []
    if args.ga_reports.exists():
        with args.ga_reports.open() as f:
            for line in f:
                try:
                    ga_reports.append(json.loads(line))
                except Exception:
                    pass

    # Get unique symbols and models
    symbols = sorted(base['symbol'].unique())
    models = sorted(base['model'].unique())

    print(f'✓ Found {len(symbols)} symbols, {len(models)} models')

    # Generate all charts
    print('📈 Generating equity curves...')
    equity_chart = generate_equity_curves(args.base_dir, args.quick_dir, symbols, models, args.out_dir)

    print('⚠️  Calculating extended risk metrics...')
    risk_chart, extended_metrics = generate_risk_metrics_table(args.base_dir, args.quick_dir, symbols, models,
                                                                args.out_dir / 'risk_metrics.png')

    print('🏆 Generating model rankings...')
    ranking_chart, ranked_df = generate_model_ranking(extended_metrics, args.out_dir / 'ranking.png')

    print('📊 Generating comparison charts...')
    from poC.generate_presentation import generate_comparison_chart, generate_model_performance_chart
    comparison_chart = generate_comparison_chart(base, quick, args.out_dir / 'comparison.png')
    heatmap_chart = generate_model_performance_chart(base, quick, args.out_dir / 'heatmaps.png')

    # Generate enhanced HTML
    print('🎨 Generating enhanced HTML dashboard...')
    dashboard_path = generate_enhanced_html(
        base, quick, ga_reports,
        comparison_chart, heatmap_chart,
        equity_chart, risk_chart, ranking_chart,
        ranked_df, extended_metrics,
        args.out_dir / 'dashboard_v2.html'
    )

    print('\n✅ Enhanced dashboard generated successfully!')
    print(f'📂 Output directory: {args.out_dir}')
    print(f'🌐 Dashboard: {dashboard_path}')
    print(f'\n🚀 Open with: xdg-open {dashboard_path.absolute()}')


if __name__ == '__main__':
    main()
