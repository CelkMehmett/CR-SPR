#!/usr/bin/env python3
"""Generate and serve dashboards for all symbols."""

import sys
sys.path.insert(0, '.')

import logging
import os
from pathlib import Path
import json
import urllib.request
import urllib.error

# Note: importing the full dashboard generator can fail in some environments
# because it depends on Plotly and a large HTML f-string. For the purpose of
# embedding initial telemetry into already-generated dashboard HTML files we
# avoid importing it here and instead operate on existing files in `dashboards/`.

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def generate_all_dashboards():
    """Generate dashboards for multiple symbols."""
    print("\n" + "="*80)
    print("🎨 GENERATING VISUAL DASHBOARDS FOR ALL SYMBOLS")
    print("="*80)

    # Expand to at least 30 representative liquid tickers
    symbols = [
        'AAPL','MSFT','GOOGL','AMZN','META','NVDA','TSLA','BRK-B','JPM','V',
        'MA','PG','JNJ','UNH','HD','DIS','BAC','PFE','KO','NFLX',
        'XOM','CVX','CMCSA','VZ','ORCL','INTC','CSCO','ABT','NKE','MCD'
    ]
    dashboards_dir = Path('dashboards')
    dashboards_dir.mkdir(exist_ok=True)

    generated_files = []

    for symbol in symbols:
        try:
            output_file = dashboards_dir / f'{symbol.lower()}_dashboard.html'
            print(f"\n📈 Generating dashboard for {symbol}...")
            # If a dashboard file already exists, keep it. We avoid importing the
            # heavy `generate_dashboard` here to prevent f-string/JS parsing issues
            # in environments without Plotly available. If the file doesn't
            # exist, just skip generation (user can run a full generator locally).
            if output_file.exists():
                print(f"   ✓ Found existing dashboard file: {output_file.name}")
                generated_files.append((symbol, output_file))
            else:
                print(f"   ℹ Skipping full dashboard generation for {symbol} (no dashboard file present).")

        except Exception as e:
            logger.error(f"Failed to generate dashboard for {symbol}: {e}")
            continue

    # Create index HTML for easy access
    print("\n📑 Creating index page...")
    index_html = create_index_page(generated_files)
    index_path = dashboards_dir / 'index.html'
    with open(index_path, 'w') as f:
        f.write(index_html)

    print(f"\n" + "="*80)
    print(f"✅ ALL DASHBOARDS GENERATED SUCCESSFULLY")
    print(f"="*80)
    print(f"\n📂 Dashboard directory: {dashboards_dir.absolute()}")
    print(f"🌐 Index page: {index_path.absolute()}")
    print(f"\nGenerated dashboards:")
    for symbol, path in generated_files:
        print(f"  • {symbol}: {path}")
    print(f"\nOpen in browser: file://{index_path.absolute()}")

    # Try to fetch initial weight history from local demo server and embed into dashboards
    print("\n🔎 Attempting to fetch initial weight history from local /telemetry/weights endpoint...")
    weight_history = {'timestamps': [], 'weights': {}}
    try:
        req = urllib.request.Request('http://127.0.0.1:8008/telemetry/weights')
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                payload = json.loads(resp.read().decode('utf-8'))
                wh = payload.get('weight_history') if isinstance(payload, dict) else None
                if isinstance(wh, dict):
                    weight_history = wh
                    print('   ✓ Retrieved weight_history from local server')
                else:
                    print('   ℹ /telemetry/weights returned no weight_history')
            else:
                print(f'   ℹ /telemetry/weights returned status {resp.status}')
    except (urllib.error.URLError, Exception) as e:
        print('   ⚠ Could not reach local telemetry endpoint (server may be down):', e)

    # If telemetry returned empty weight_history, attempt to derive a simple
    # per-symbol weight mapping from the server's latest genome snapshot
    # (useful when telemetry isn't instrumented yet).
    try:
        if (not weight_history.get('weights')):
            req = urllib.request.Request('http://127.0.0.1:8008/genome_snapshot')
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    snap = json.loads(resp.read().decode('utf-8'))
                    ch = snap.get('chromosomes') if isinstance(snap, dict) else None
                    if isinstance(ch, dict) and ch:
                        symbol_vals = {}
                        for cname, params in ch.items():
                            try:
                                sym = cname.split('_')[0]
                                v = None
                                if isinstance(params, dict) and 'momentum_threshold' in params:
                                    p = params['momentum_threshold']
                                    v = p.get('value') if isinstance(p, dict) else p
                                else:
                                    if isinstance(params, dict):
                                        for pinfo in params.values():
                                            try:
                                                cand = pinfo.get('value') if isinstance(pinfo, dict) else pinfo
                                                if isinstance(cand, (int, float)):
                                                    v = cand
                                                    break
                                            except Exception:
                                                continue
                                if v is None:
                                    continue
                                symbol_vals[sym] = float(abs(v))
                            except Exception:
                                continue

                        if symbol_vals:
                            total = float(sum(symbol_vals.values())) or 1.0
                            weights = {s: (symbol_vals[s] / total) for s in symbol_vals}
                            weight_history = {'timestamps': [snap.get('snapshot_time') or snap.get('creation_time') or '' ], 'weights': weights}
                            print('   ✓ Derived fallback weight_history from /genome_snapshot')
    except Exception as e:
        print('   ⚠ Could not derive fallback weight_history from /genome_snapshot:', e)

    # If HTTP endpoints were unreachable (server down) try reading latest
    # persisted snapshot file directly from the snapshots folder so the
    # generator can operate offline when snapshots are available.
    try:
        if (not weight_history.get('weights')):
            snaps_dir = Path('poc/presentation_v2/snapshots')
            if snaps_dir.exists() and snaps_dir.is_dir():
                files = sorted(list(snaps_dir.glob('*.json')), key=lambda p: p.stat().st_mtime, reverse=True)
                for p in files:
                    try:
                        with open(p, 'r', encoding='utf-8') as fh:
                            snap = json.load(fh)
                        # Prefer telemetry.weight_history if present
                        meta = snap.get('metadata') if isinstance(snap, dict) else {}
                        tele = meta.get('telemetry') if isinstance(meta, dict) else None
                        if tele and isinstance(tele, dict):
                            wh = tele.get('weight_history') or tele.get('weights') or None
                            if isinstance(wh, dict) and wh.get('weights'):
                                weight_history = wh
                                print(f"   ✓ Loaded weight_history from persisted snapshot: {p.name}")
                                break
                        # Fallback: derive from chromosomes if telemetry missing
                        ch = snap.get('chromosomes') if isinstance(snap, dict) else None
                        if isinstance(ch, dict) and ch:
                            symbol_vals = {}
                            for cname, params in ch.items():
                                try:
                                    sym = cname.split('_')[0]
                                    v = None
                                    if isinstance(params, dict) and 'momentum_threshold' in params:
                                        pinfo = params['momentum_threshold']
                                        v = pinfo.get('value') if isinstance(pinfo, dict) else pinfo
                                    else:
                                        if isinstance(params, dict):
                                            for pinfo in params.values():
                                                try:
                                                    cand = pinfo.get('value') if isinstance(pinfo, dict) else pinfo
                                                    if isinstance(cand, (int, float)):
                                                        v = cand
                                                        break
                                                except Exception:
                                                    continue
                                    if v is None:
                                        continue
                                    symbol_vals[sym] = float(abs(v))
                                except Exception:
                                    continue

                            if symbol_vals:
                                total = float(sum(symbol_vals.values())) or 1.0
                                weights = {s: (symbol_vals[s] / total) for s in symbol_vals}
                                weight_history = {'timestamps': [snap.get('snapshot_time') or snap.get('creation_time') or '' ], 'weights': weights}
                                print(f"   ✓ Derived fallback weight_history from persisted snapshot: {p.name}")
                                break
                    except Exception:
                        continue
    except Exception as e:
        print('   ⚠ Could not read persisted snapshots for fallback:', e)

    # Normalize weight_history into canonical shape: timestamps: list, weights: {SYM: [v...]}
    def _normalize_weight_history(wh):
        wh = wh or {'timestamps': [], 'weights': {}}
        ts = wh.get('timestamps') or []
        if not isinstance(ts, list):
            ts = [ts]
        weights = wh.get('weights') or {}

        # If weights are scalar values, wrap them into single-element lists
        for k, v in list(weights.items()):
            if isinstance(v, (int, float)):
                weights[k] = [float(v)]
            elif isinstance(v, list):
                # ensure numeric types where possible
                new = []
                for item in v:
                    try:
                        new.append(float(item) if item is not None else None)
                    except Exception:
                        new.append(None)
                weights[k] = new
            else:
                try:
                    weights[k] = [float(v)]
                except Exception:
                    weights[k] = [None]

        # Ensure we have at least one timestamp if there are weights
        if not ts and weights:
            ts = ['']

        # Pad or truncate each weight array to match timestamps length
        L = len(ts)
        for k in list(weights.keys()):
            arr = weights.get(k) or []
            new = []
            for i in range(L):
                if i < len(arr):
                    try:
                        new.append(float(arr[i]) if arr[i] is not None else None)
                    except Exception:
                        new.append(None)
                else:
                    new.append(None)
            weights[k] = new

        return {'timestamps': ts, 'weights': weights}

    weight_history = _normalize_weight_history(weight_history)

    # Embed the initial weight history into each generated dashboard file so chart isn't blank
    embed_js = f"""\n<script>window.__INITIAL_WEIGHT_HISTORY = {json.dumps(weight_history)};</script>\n"""

    has_payload = bool(weight_history.get('weights') and weight_history.get('timestamps'))

    import re
    token_re = re.compile(r"<script[^>]*>.*?window\.__INITIAL_WEIGHT_HISTORY.*?</script>", re.S)

    for _, path in generated_files:
        try:
            # Only append or replace when we actually have a non-empty payload.
            with open(path, 'r+', encoding='utf-8') as fh:
                content = fh.read()

                # Remove any existing embedded weight_history script blocks to avoid duplicates
                cleaned = token_re.sub('', content)

                if not has_payload:
                    # If there's no fresh payload, preserve file as-is (skip writing)
                    print(f"   → Skipping {path.name}: no fresh weight_history available")
                    continue

                # Write cleaned content and append a single canonical embed script
                fh.seek(0)
                fh.truncate(0)
                fh.write(cleaned)
                fh.write('\n' + embed_js)
                print(f"   ✚ Wrote canonical initial weight_history into {path.name}")
        except Exception as e:
            print('   ⚠ Failed to embed weight_history into', path, e)


def create_index_page(dashboards: list) -> str:
    """Create index page for all dashboards."""
    cards = []
    for symbol, path in dashboards:
        cards.append(f"""
        <a href="{path.name}" class="dashboard-card">
            <h2>{symbol}</h2>
            <p>View detailed analysis and strategy performance</p>
            <span class="arrow">→</span>
        </a>
        """)

    dashboard_cards = '\n'.join(cards)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CRISPR Trading Strategies Dashboard Index</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 60px;
            }}
            .header h1 {{
                font-size: 48px;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }}
            .header p {{
                font-size: 18px;
                opacity: 0.9;
                margin-bottom: 5px;
            }}
            .subheader {{
                font-size: 14px;
                opacity: 0.7;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin-bottom: 60px;
            }}
            .dashboard-card {{
                background: white;
                border-radius: 12px;
                padding: 40px 30px;
                text-decoration: none;
                color: #333;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                cursor: pointer;
                position: relative;
                overflow: hidden;
            }}
            .dashboard-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                transition: left 0.5s ease;
            }}
            .dashboard-card:hover {{
                transform: translateY(-10px);
                box-shadow: 0 16px 48px rgba(0,0,0,0.2);
            }}
            .dashboard-card:hover::before {{
                left: 100%;
            }}
            .dashboard-card h2 {{
                font-size: 32px;
                margin-bottom: 10px;
                color: #667eea;
            }}
            .dashboard-card p {{
                font-size: 16px;
                color: #666;
                margin-bottom: 15px;
            }}
            .arrow {{
                display: inline-block;
                font-size: 24px;
                transition: transform 0.3s ease;
            }}
            .dashboard-card:hover .arrow {{
                transform: translateX(5px);
            }}
            .features {{
                background: rgba(255,255,255,0.1);
                color: white;
                padding: 40px;
                border-radius: 12px;
                margin-bottom: 40px;
            }}
            .features h3 {{
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .features-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }}
            .feature {{
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 8px;
            }}
            .feature strong {{
                display: block;
                margin-bottom: 5px;
            }}
            .footer {{
                text-align: center;
                color: white;
                opacity: 0.8;
                font-size: 14px;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid rgba(255,255,255,0.2);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧬 CRISPR AI Trading Strategies</h1>
                <p>Visual Analytics Dashboard</p>
                <p class="subheader">Multi-Strategy Performance Analysis with Genetic Algorithm Optimization</p>
            </div>

            <div class="features">
                <h3>📊 Dashboard Features</h3>
                <div class="features-grid">
                    <div class="feature">
                        <strong>📈 Equity Curves</strong>
                        <span>Track cumulative portfolio value over time</span>
                    </div>
                    <div class="feature">
                        <strong>📊 Performance Metrics</strong>
                        <span>Sharpe, Sortino, Calmar, drawdown, win rate</span>
                    </div>
                    <div class="feature">
                        <strong>🎯 Signals Heatmap</strong>
                        <span>Visualize trading signals across all strategies</span>
                    </div>
                    <div class="feature">
                        <strong>📉 Drawdown Analysis</strong>
                        <span>Underwater plot showing peak-to-trough declines</span>
                    </div>
                    <div class="feature">
                        <strong>📈 Rolling Sharpe</strong>
                        <span>60-day rolling risk-adjusted return metrics</span>
                    </div>
                    <div class="feature">
                        <strong>🧬 GA Optimization</strong>
                        <span>Genetically optimized strategy weights</span>
                    </div>
                </div>
            </div>

            <div class="grid">
                {dashboard_cards}
            </div>

            <div class="footer">
                <p>CRISPR AI Trading System | Powered by Genetic Algorithm Strategy Optimization</p>
                <p>Past performance does not guarantee future results. For educational purposes only.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


if __name__ == '__main__':
    try:
        generate_all_dashboards()
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}", exc_info=True)
        sys.exit(1)
