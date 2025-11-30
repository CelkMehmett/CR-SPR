#!/usr/bin/env python3
"""Generate a detailed HTML report that embeds all per-symbol dashboards and
includes telemetry summaries and model comparison data.

Output: reports/all_stocks_report.html (relative paths to dashboards/ so open locally).
"""
import os
import json
import glob
import re
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DASH_DIR = os.path.join(ROOT, 'dashboards')
OUT_DIR = os.path.join(ROOT, 'reports')
os.makedirs(OUT_DIR, exist_ok=True)
OUT_HTML = os.path.join(OUT_DIR, 'all_stocks_report.html')

# regex to extract embedded JSON
token_re = re.compile(r"window\.__INITIAL_WEIGHT_HISTORY\s*=\s*(\{.*?\});", re.S)

# helper: load latest persisted snapshot
def load_latest_snapshot():
    snaps_dir = os.path.join(ROOT, 'poc', 'presentation_v2', 'snapshots')
    try:
        if os.path.isdir(snaps_dir):
            files = sorted([os.path.join(snaps_dir, f) for f in os.listdir(snaps_dir) if f.endswith('.json')], key=lambda p: os.path.getmtime(p), reverse=True)
            if files:
                with open(files[0], 'r', encoding='utf-8') as fh:
                    return json.load(fh)
    except Exception:
        return None
    return None

latest_snapshot = load_latest_snapshot()
latest_telemetry = None
if isinstance(latest_snapshot, dict):
    latest_telemetry = (latest_snapshot.get('metadata') or {}).get('telemetry')

# list dashboards
dash_files = sorted(glob.glob(os.path.join(DASH_DIR, '*_dashboard.html')))

sections = []
for f in dash_files:
    base = os.path.basename(f)
    symbol = base.replace('_dashboard.html','')
    caption = 'No embedded telemetry found.'
    try:
        txt = open(f, 'r', encoding='utf-8', errors='replace').read()
        m = token_re.search(txt)
        if m:
            js = m.group(1)
            try:
                wh = json.loads(js)
            except Exception:
                # best-effort fix: replace single quotes with double
                try:
                    fixed = js.replace("'", '"')
                    wh = json.loads(fixed)
                except Exception:
                    wh = None
            if isinstance(wh, dict):
                timestamps = wh.get('timestamps', [])
                weights = wh.get('weights', {})
                if timestamps:
                    n = len(timestamps)
                    my_weight = None
                    if symbol in weights:
                        arr = weights.get(symbol)
                        if isinstance(arr, list) and arr:
                            my_weight = arr[-1]
                        else:
                            my_weight = arr
                    # top sample
                    top = []
                    for k,v in weights.items():
                        val = None
                        if isinstance(v, list) and v:
                            val = next((x for x in reversed(v) if x is not None), None)
                        elif v is not None:
                            val = v
                        top.append((k,val))
                    top_sorted = sorted(top, key=lambda x: (x[1] is None, -(x[1] or 0)))[:5]
                    top_str = ', '.join([f"{k}: {v if v is not None else 'N/A'}" for k,v in top_sorted])
                    # trend
                    def fl(arr):
                        if not isinstance(arr, list): return (None,None)
                        first = next((x for x in arr if x is not None), None)
                        last = next((x for x in reversed(arr) if x is not None), None)
                        return (first,last)
                    trend = 'N/A'
                    if symbol in weights and isinstance(weights[symbol], list):
                        fval,lval = fl(weights[symbol])
                        if fval is None or lval is None:
                            trend = 'insufficient data'
                        else:
                            if abs(lval-fval)<1e-6:
                                trend='stable'
                            elif lval>fval:
                                trend='increasing'
                            else:
                                trend='decreasing'
                    # fitness and diversity analysis from latest telemetry if available
                    best_summary = ''
                    diversity_note = ''
                    convergence_note = ''
                    if isinstance(latest_telemetry, dict):
                        try:
                            bpg = latest_telemetry.get('best_per_generation')
                            apg = latest_telemetry.get('avg_per_generation')
                            div = latest_telemetry.get('diversity_per_generation')
                            if isinstance(bpg, list) and bpg:
                                # simple trend: compare first and last
                                if bpg[-1] > bpg[0] + 1e-6:
                                    fitness_trend = 'improving'
                                elif bpg[-1] < bpg[0] - 1e-6:
                                    fitness_trend = 'declining'
                                else:
                                    fitness_trend = 'stable'
                                best_summary = f"Best fitness (per generation): first={bpg[0]:.4f}, last={bpg[-1]:.4f} ({fitness_trend}). "
                            if isinstance(div, list) and div:
                                last_div = div[-1]
                                if last_div is not None and last_div < 0.01:
                                    diversity_note = 'Population diversity is very low (converged). '
                                elif last_div is not None and last_div < 0.05:
                                    diversity_note = 'Population diversity is low. '
                                else:
                                    diversity_note = ''
                            # convergence heuristic
                            if isinstance(bpg, list) and isinstance(apg, list) and len(bpg) >= 2:
                                # if best fitness hasn't changed much over last 3 gens, consider converged
                                recent = bpg[-3:] if len(bpg) >= 3 else bpg
                                if max(recent) - min(recent) < 1e-6:
                                    convergence_note = 'Optimization has converged (no improvement in recent generations). '
                        except Exception:
                            pass

                    caption = (
                        f'Embedded weight history with {n} timestamp(s). Trend for {symbol}: {trend}. '
                        f'Latest weight: {my_weight if my_weight is not None else "N/A"}. '
                        f'Sample top weights: {top_str}. {best_summary}{diversity_note}{convergence_note}'
                    ).strip()
                else:
                    caption = 'Embedded telemetry present but no timestamps.'
    except Exception as e:
        caption = f'Failed to parse embedded telemetry: {e}'

    sections.append({'symbol': symbol, 'file': os.path.relpath(f, ROOT), 'caption': caption})

# model comparison JSON
comp_path = os.path.join(ROOT, 'strategy_comparison_results.json')
model_comp = None
if os.path.exists(comp_path):
    try:
        model_comp = json.load(open(comp_path, 'r', encoding='utf-8'))
    except Exception:
        model_comp = None

# Build HTML (inline dashboard bodies to create a single-file report)
html = []
html.append('<!doctype html>')
html.append('<html><head><meta charset="utf-8"><title>CRISPR - All Stocks Report</title>')
html.append('<style>body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#f6f8fb} .card{border:1px solid #ddd;padding:12px;margin-bottom:18px;border-radius:6px;background:#fff} h1{color:#2a3f5f} .dashboard-embed{border:1px solid #ccc;padding:8px;margin-top:8px;background:#fff}</style>')
html.append('</head><body>')
html.append(f'<h1>CRISPR Consolidated Report (inlined dashboards)</h1>')
html.append(f'<p>Generated: {datetime.utcnow().isoformat()}Z</p>')

# Navigation
html.append('<nav><strong>Contents:</strong> <ul>')
for s in sections:
    html.append(f"<li><a href='#{s['symbol']}'>{s['symbol']}</a></li>")
html.append('</ul></nav>')

# Inline each dashboard's body content
body_re = re.compile(r"<body[^>]*>([\s\S]*?)</body>", re.I)
for s in sections:
    html.append(f"<div class='card' id='{s['symbol']}'>")
    html.append(f"<h2>{s['symbol']}</h2>")
    html.append(f"<p style='color:#444'>{s['caption']}</p>")
    # read the dashboard HTML and extract body
    dash_path = os.path.join(ROOT, s['file'])
    try:
        raw = open(dash_path, 'r', encoding='utf-8', errors='replace').read()
        m = body_re.search(raw)
        content = m.group(1) if m else raw
        # Wrap the extracted body in a container to avoid interfering with outer styles
        html.append(f"<div class='dashboard-embed'>\n{content}\n</div>")
        html.append(f"<p><a href='{s['file']}' target='_blank'>Open original dashboard</a></p>")
    except Exception as e:
        html.append(f"<p>Failed to inline dashboard content: {e}</p>")
    html.append('</div>')

# Model comparison
html.append('<div class="card" id="model-comparison">')
html.append('<h2>Model Comparison</h2>')
if model_comp:
    html.append('<pre style="white-space:pre-wrap;">')
    html.append(json.dumps(model_comp, indent=2, ensure_ascii=False))
    html.append('</pre>')
else:
    html.append('<p>No strategy_comparison_results.json found.</p>')
html.append('</div>')

html.append('</body></html>')

with open(OUT_HTML, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(html))

print('Wrote HTML report to', OUT_HTML)
