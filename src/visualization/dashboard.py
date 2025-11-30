#!/usr/bin/env python3
"""Visual dashboard for CRISPR trading strategies with Plotly.

Interactive web UI showing:
- Equity curves for all strategies
- Strategy performance comparison
- Market regime detection
- Real-time trading signals
- Portfolio metrics and P&L
"""

import sys
sys.path.insert(0, '.')

import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.data.market_data import MarketDataLoader
from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.advanced_trading import (
    MomentumStrategy, MeanReversionStrategy, MacdStrategy,
    EnsembleStrategy, AdaptiveRiskStrategy
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def create_equity_curves_chart(results: Dict, price_data: pd.Series) -> go.Figure:
    """Create equity curves comparison chart."""
    fig = go.Figure()

    # Add each strategy's equity curve
    for strategy_name, result in results.items():
        equity_curve = result['equity_curve']
        fig.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            name=strategy_name,
            mode='lines',
            line=dict(width=2),
        ))

    # Add price reference (right axis)
    fig.add_trace(go.Scatter(
        x=price_data.index,
        y=price_data.values,
        name='Price (Reference)',
        mode='lines',
        line=dict(width=1, dash='dot', color='gray'),
        yaxis='y2',
        opacity=0.3,
    ))

    fig.update_layout(
        title='Strategy Equity Curves Over Time',
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)',
        yaxis2=dict(
            title='Stock Price ($)',
            overlaying='y',
            side='right',
        ),
        hovermode='x unified',
        height=600,
        template='plotly_white',
    )

    return fig


def create_performance_comparison_chart(results: Dict) -> go.Figure:
    """Create performance metrics comparison bar chart."""
    strategies = []
    sharpe = []
    returns = []
    max_dd = []
    win_rate = []

    for name, result in results.items():
        metrics = result['metrics']
        strategies.append(name)
        sharpe.append(metrics['sharpe_ratio'])
        returns.append(metrics['total_return'] * 100)
        max_dd.append(metrics['max_drawdown'] * 100)
        win_rate.append(metrics['win_rate'] * 100)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Sharpe Ratio', 'Total Return (%)', 'Max Drawdown (%)', 'Win Rate (%)'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]],
    )

    # Sharpe ratio
    fig.add_trace(
        go.Bar(x=strategies, y=sharpe, name='Sharpe', marker_color='steelblue'),
        row=1, col=1,
    )

    # Returns
    colors = ['green' if r > 0 else 'red' for r in returns]
    fig.add_trace(
        go.Bar(x=strategies, y=returns, name='Return', marker_color=colors),
        row=1, col=2,
    )

    # Max Drawdown
    fig.add_trace(
        go.Bar(x=strategies, y=max_dd, name='Max DD', marker_color='coral'),
        row=2, col=1,
    )

    # Win Rate
    fig.add_trace(
        go.Bar(x=strategies, y=win_rate, name='Win Rate', marker_color='lightgreen'),
        row=2, col=2,
    )

    fig.update_layout(
        title_text='Strategy Performance Comparison',
        height=700,
        showlegend=False,
        template='plotly_white',
    )

    return fig


def create_drawdown_chart(results: Dict) -> go.Figure:
    """Create drawdown analysis chart."""
    fig = go.Figure()

    for strategy_name, result in results.items():
        if 'drawdown' in result:
            drawdown = result['drawdown']
            fig.add_trace(go.Scatter(
                x=drawdown.index,
                y=drawdown.values * 100,
                name=strategy_name,
                fill='tozeroy',
                mode='lines',
            ))

    fig.update_layout(
        title='Underwater Plot - Drawdown Over Time',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        hovermode='x unified',
        height=500,
        template='plotly_white',
    )

    return fig


def create_rolling_sharpe_chart(results: Dict, window: int = 60) -> go.Figure:
    """Create rolling Sharpe ratio chart."""
    fig = go.Figure()

    for strategy_name, result in results.items():
        if 'returns' in result:
            returns = result['returns']
            rolling_sharpe = (returns.rolling(window).mean() / 
                            returns.rolling(window).std()) * np.sqrt(252)
            fig.add_trace(go.Scatter(
                x=rolling_sharpe.index,
                y=rolling_sharpe.values,
                name=strategy_name,
                mode='lines',
                line=dict(width=2),
            ))

    fig.update_layout(
        title=f'Rolling {window}-Day Sharpe Ratio',
        xaxis_title='Date',
        yaxis_title='Sharpe Ratio',
        hovermode='x unified',
        height=500,
        template='plotly_white',
    )

    return fig


def create_signals_heatmap(signals_dict: Dict[str, pd.Series]) -> go.Figure:
    """Create trading signals heatmap."""
    # Prepare data for heatmap
    heatmap_data = []
    for name, signals in signals_dict.items():
        heatmap_data.append(signals.values)

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=list(signals_dict.values())[0].index if signals_dict else [],
        y=list(signals_dict.keys()),
        colorscale='RdBu',
        zmid=0,
        zmin=-1,
        zmax=1,
    ))

    fig.update_layout(
        title='Trading Signals Heatmap (-1=Sell, 0=Hold, 1=Buy)',
        xaxis_title='Date',
        yaxis_title='Strategy',
        height=400,
        template='plotly_white',
    )

    return fig


def create_metrics_table(results: Dict) -> go.Figure:
    """Create performance metrics table."""
    rows = []
    for strategy_name, result in results.items():
        metrics = result['metrics']
        rows.append([
            strategy_name,
            f"{metrics['sharpe_ratio']:.4f}",
            f"{metrics['total_return']:.2%}",
            f"{metrics['sortino_ratio']:.4f}",
            f"{metrics['calmar_ratio']:.4f}",
            f"{metrics['max_drawdown']:.2%}",
            f"{metrics['win_rate']:.2%}",
            f"{metrics['profit_factor']:.2f}",
        ])

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Strategy', 'Sharpe', 'Return', 'Sortino', 'Calmar',
                   'Max DD', 'Win Rate', 'Profit Factor'],
            fill_color='steelblue',
            align='center',
            font=dict(color='white', size=12),
        ),
        cells=dict(
            values=list(zip(*rows)),
            fill_color='lavender',
            align='center',
            font=dict(size=11),
        ),
    )])

    fig.update_layout(
        title='Detailed Performance Metrics',
        height=400,
        template='plotly_white',
    )

    return fig


def create_dashboard_html(
    results: Dict,
    price_data: pd.Series,
    signals_dict: Dict[str, pd.Series],
    symbol: str,
) -> str:
    """Create complete HTML dashboard."""
    # Create all charts
    eq_chart = create_equity_curves_chart(results, price_data)
    perf_chart = create_performance_comparison_chart(results)
    dd_chart = create_drawdown_chart(results)
    rolling_sharpe = create_rolling_sharpe_chart(results)
    signals_heat = create_signals_heatmap(signals_dict)
    metrics_table = create_metrics_table(results)

    # Convert to HTML
    eq_html = eq_chart.to_html(include_plotlyjs='cdn', div_id='eq_chart')
    perf_html = perf_chart.to_html(include_plotlyjs=False, div_id='perf_chart')
    dd_html = dd_chart.to_html(include_plotlyjs=False, div_id='dd_chart')
    rolling_html = rolling_sharpe.to_html(include_plotlyjs=False, div_id='rolling_chart')
    signals_html = signals_heat.to_html(include_plotlyjs=False, div_id='signals_chart')
    metrics_html = metrics_table.to_html(include_plotlyjs=False, div_id='metrics_table')

    # Create dashboard HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CRISPR Trading Strategies Dashboard - {symbol}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0 0 5px 0;
            }}
            .header p {{
                margin: 5px 0;
                opacity: 0.9;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .grid.two-col {{
                grid-template-columns: 1fr 1fr;
            }}
            .card {{
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 15px;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧬 CRISPR AI Trading Strategies</h1>
            <p>Symbol: {symbol} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            <p>Visual Analytics Dashboard - Real-time Strategy Performance Monitoring</p>
        </div>

        <div class="grid">
            <div class="card">
                {eq_html}
            </div>
        </div>

        <div class="grid two-col">
            <div class="card">
                {perf_html}
            </div>
            <div class="card">
                {metrics_html}
            </div>
        </div>

        <div class="grid two-col">
            <div class="card">
                {dd_html}
            </div>
            <div class="card">
                {rolling_html}
            </div>
        </div>

        <div class="grid">
            <div class="card">
                {signals_html}
            </div>
        </div>

        <div class="grid two-col">
            <div class="card">
                <h3>GA Weight Evolution</h3>
                <div style="display:flex;gap:12px;align-items:center;margin-bottom:8px;">
                    <label style="font-size:13px;color:#444;">Window:</label>
                    <select id="we-window" style="padding:6px;border-radius:4px;border:1px solid #ccc;">
                        <option value="30">30</option>
                        <option value="60" selected>60</option>
                        <option value="120">120</option>
                        <option value="all">All</option>
                    </select>
                    <label style="font-size:13px;color:#444;">Refresh:</label>
                    <select id="we-refresh" style="padding:6px;border-radius:4px;border:1px solid #ccc;">
                        <option value="0">Off</option>
                        <option value="5">5s</option>
                        <option value="15">15s</option>
                        <option value="60">60s</option>
                    </select>
                </div>
                <div id="we-strategy-toggles" style="margin-bottom:8px;display:flex;flex-wrap:wrap;gap:8px;"></div>
                <div id="weight-evolution" style="height:320px;"></div>
                <p style="font-size:12px;color:#666;margin-top:8px;">Live GA telemetry (updates via SSE /events or initial snapshot via /telemetry)</p>
            </div>
            <div class="card">
                <h3>Live Telemetry Log</h3>
                <pre id="telemetry-log" style="height:320px;overflow:auto;background:#f7f7f7;padding:10px;border-radius:6px;"></pre>
            </div>
        </div>

        <div class="footer">
            <p>CRISPR AI Trading System | Powered by Genetic Algorithm Strategy Optimization</p>
            <p>This dashboard shows backtested performance. Past performance does not guarantee future results.</p>
        </div>
        <script>
        (function(){
                // Utilities
                function safeParseISO(s){ try{ return new Date(s); }catch(e){ return null; } }

                // Ensure weight history has canonical shape: timestamps array and per-symbol arrays
                function normalizeWeightHistory(wh){
                    if(!wh) return {timestamps: [], weights: {}};
                    var ts = wh.timestamps || [];
                    if(!Array.isArray(ts)) ts = [ts];
                    var weights = wh.weights || {};
                    // Wrap scalar weight values
                    Object.keys(weights).forEach(function(k){
                        var v = weights[k];
                        if(!Array.isArray(v)){
                            weights[k] = (v === null || v === undefined) ? [null] : [Number(v)];
                        } else {
                            // coerce elements where possible
                            weights[k] = v.map(function(el){
                                if(el === null || el === undefined) return null;
                                var n = Number(el);
                                return isFinite(n) ? n : null;
                            });
                        }
                    });
                    if(ts.length === 0 && Object.keys(weights).length > 0) ts = [''];
                    var L = ts.length;
                    Object.keys(weights).forEach(function(k){
                        var arr = weights[k] || [];
                        var out = [];
                        for(var i=0;i<L;i++){
                            if(i < arr.length){ out.push(arr[i]); }
                            else { out.push(null); }
                        }
                        weights[k] = out;
                    });
                    return {timestamps: ts, weights: weights};
                }

                function plotFromWeightHistory(wh){
                    if(!window.Plotly) return;
                    wh = normalizeWeightHistory(wh);
                    const timestamps = (wh && wh.timestamps) || [];
                    const weights = (wh && wh.weights) || {};
                    const traces = [];
                    for(const name of Object.keys(weights)){
                        traces.push({x: timestamps, y: weights[name], name: name, mode: 'lines'});
                    }
                if(traces.length===0){
                    // blank placeholder
                    Plotly.newPlot('weight-evolution', [{x:[], y:[], name:'no-data'}], {title:'GA Weight Evolution'});
                    return;
                }
                // store original
                window.__WEIGHT_ORIG = {timestamps: timestamps, weights: weights};
                Plotly.newPlot('weight-evolution', traces, {title:'GA Weight Evolution', autosize:true});
                // populate strategy toggles
                const container = document.getElementById('we-strategy-toggles');
                if(container){
                    container.innerHTML = '';
                    for(const name of Object.keys(weights)){
                        const id = 'chk_' + name.replace(/[^a-zA-Z0-9]/g,'_');
                        const label = document.createElement('label');
                        label.style.fontSize = '13px';
                        label.style.marginRight = '8px';
                        const cb = document.createElement('input');
                        cb.type = 'checkbox'; cb.id = id; cb.checked = true; cb.value = name;
                        cb.addEventListener('change', function(){ applyToggles(); });
                        label.appendChild(cb);
                        label.appendChild(document.createTextNode(' ' + name));
                        container.appendChild(label);
                    }
                }
            }

            function applyWindow(){
                const sel = document.getElementById('we-window');
                if(!sel || !window.__WEIGHT_ORIG) return;
                const val = sel.value;
                const ts = window.__WEIGHT_ORIG.timestamps || [];
                const weights = window.__WEIGHT_ORIG.weights || {};
                let cutIdx = 0;
                if(val !== 'all'){
                    const days = parseInt(val,10);
                    // find first index within last `days` entries
                    cutIdx = Math.max(0, ts.length - days);
                } else {
                    cutIdx = 0;
                }
                const traces = [];
                for(const name of Object.keys(weights)){
                    const full = weights[name] || [];
                    const sliced = full.slice(cutIdx);
                    const slicedTs = ts.slice(cutIdx);
                    traces.push({x: slicedTs, y: sliced, name: name, mode: 'lines'});
                }
                if(window.Plotly){
                    Plotly.react('weight-evolution', traces, {title:'GA Weight Evolution'});
                }
            }

            function applyToggles(){
                // Determine which strategies are checked and update visibility
                const container = document.getElementById('we-strategy-toggles');
                if(!container || !window.Plotly) return;
                const checks = container.querySelectorAll('input[type=checkbox]');
                const visibles = [];
                checks.forEach((cb)=>{ visibles.push({name: cb.value, visible: cb.checked}); });
                // Build traces from original but set visibility
                if(!window.__WEIGHT_ORIG) return;
                const ts = window.__WEIGHT_ORIG.timestamps || [];
                const weights = window.__WEIGHT_ORIG.weights || {};
                const traces = [];
                for(const item of visibles){
                    const full = weights[item.name] || [];
                    traces.push({x: ts, y: full, name: item.name, mode: 'lines', visible: item.visible});
                }
                Plotly.react('weight-evolution', traces, {title:'GA Weight Evolution'});
            }

            // Wire controls
            document.addEventListener('DOMContentLoaded', function(){
                const winSel = document.getElementById('we-window');
                const refSel = document.getElementById('we-refresh');
                if(winSel) winSel.addEventListener('change', applyWindow);
                if(refSel) refSel.addEventListener('change', function(){
                    // manage polling later (simple approach: reload from /telemetry/weights)
                    const secs = parseInt(refSel.value,10);
                    if(window.__WEIGHT_POLL_INTERVAL){ clearInterval(window.__WEIGHT_POLL_INTERVAL); window.__WEIGHT_POLL_INTERVAL = null; }
                    if(secs>0){
                        window.__WEIGHT_POLL_INTERVAL = setInterval(async function(){
                            try{
                                const resp = await fetch('/telemetry/weights');
                                if(resp.ok){
                                    const payload = await resp.json();
                                    const wh = payload.weight_history || {timestamps:[], weights:{}};
                                    window.__INITIAL_WEIGHT_HISTORY = wh;
                                    window.__WEIGHT_ORIG = {timestamps: wh.timestamps||[], weights: wh.weights||{}};
                                    applyWindow();
                                }
                            }catch(e){ console.warn('poll failed', e); }
                        }, secs*1000);
                    }
                });

                // If an initial weight history was embedded, plot it
                if(window.__INITIAL_WEIGHT_HISTORY && Object.keys(window.__INITIAL_WEIGHT_HISTORY.weights||{}).length>0){
                    plotFromWeightHistory(window.__INITIAL_WEIGHT_HISTORY);
                    applyWindow();
                } else {
                    // wait briefly for embedded var or telemetry script
                    setTimeout(function(){
                        if(window.__INITIAL_WEIGHT_HISTORY && Object.keys(window.__INITIAL_WEIGHT_HISTORY.weights||{}).length>0){
                            plotFromWeightHistory(window.__INITIAL_WEIGHT_HISTORY); applyWindow();
                        }
                    }, 1000);
                }
            });
        })();
        </script>
    </body>
    </html>
    """

    return html



def generate_dashboard(symbol: str = 'AAPL', output_file: str = None):
    """Generate complete dashboard for a symbol."""
    print(f"\n{'='*80}")
    print(f"📊 GENERATING VISUAL DASHBOARD FOR {symbol}")
    print(f"{'='*80}\n")

    # Load data
    print(f"Loading data for {symbol}...")
    loader = MarketDataLoader()
    data = loader.fetch_historical_data(symbol, days=252)
    price = loader.get_price_series(data)
    volume = loader.get_volume_series(data)

    # Create strategies
    print("Creating strategies...")
    strategies = {
        'Momentum': MomentumStrategy(symbol=symbol),
        'MeanReversion': MeanReversionStrategy(symbol=symbol),
        'MACD': MacdStrategy(symbol=symbol),
        'Ensemble': EnsembleStrategy(symbol=symbol),
        'AdaptiveRisk': AdaptiveRiskStrategy(symbol=symbol),
    }

    # Backtest
    print("Running backtests...")
    engine = BacktestEngine(initial_capital=100000)
    results = engine.backtest_multiple(strategies, price, volume)

    # Get signals for heatmap
    print("Generating signals...")
    signals_dict = {}
    for name, strategy in strategies.items():
        sigs, _ = strategy.generate_signals(price, volume)
        signals_dict[name] = sigs

    # Generate dashboard
    print("Creating visualizations...")
    html = create_dashboard_html(results, price, signals_dict, symbol)

    # Save to file
    if output_file is None:
        output_file = f'dashboard_{symbol}.html'

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"\n✅ Dashboard created successfully!")
    print(f"📁 Saved to: {output_file}")
    print(f"🌐 Open in browser: file://{output_file}\n")

    return output_file


if __name__ == '__main__':
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'
    output = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        generate_dashboard(symbol, output)
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}", exc_info=True)
        sys.exit(1)
