#!/usr/bin/env python3
"""Render all dashboards to PNGs, parse embedded telemetry and assemble a comprehensive PDF report.

Outputs: /tmp/crispr_all_stocks_report.pdf
"""
import os
import re
import json
import subprocess
import glob
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import mm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DASH_DIR = os.path.join(ROOT, 'dashboards')
OUT_PDF = '/tmp/crispr_all_stocks_report.pdf'
IMG_DIR = '/tmp/crispr_dash_screens'
os.makedirs(IMG_DIR, exist_ok=True)

styles = getSampleStyleSheet()
heading = ParagraphStyle('Heading', parent=styles['Heading1'], fontSize=16)
subh = ParagraphStyle('SubH', parent=styles['Heading2'], fontSize=12)
body = styles['Normal']
mono = ParagraphStyle('Mono', parent=styles['Normal'], fontName='Courier', fontSize=9)

# find dashboard files
files = sorted(glob.glob(os.path.join(DASH_DIR, '*_dashboard.html')))

# regex to extract embedded JSON
token_re = re.compile(r"window\.__INITIAL_WEIGHT_HISTORY\s*=\s*(\{.*?\});", re.S)

# helper: load latest persisted snapshot to access run-level metadata if available
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

reports = []
for f in files:
    base = os.path.basename(f)
    symbol = base.replace('_dashboard.html','')
    img_path = os.path.join(IMG_DIR, f"{symbol}.png")
    # render with chrome
    url = 'file://' + os.path.abspath(f)
    try:
        subprocess.run(['/usr/bin/google-chrome', '--headless', '--disable-gpu', f'--screenshot={img_path}', '--window-size=1400,900', url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # try stable binary if available
        try:
            subprocess.run(['/usr/bin/google-chrome-stable', '--headless', '--disable-gpu', f'--screenshot={img_path}', '--window-size=1400,900', url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print('Render failed for', symbol, e)
            img_path = None
    # parse embedded payload
    caption = 'No embedded telemetry found.'
    try:
        txt = open(f, 'r', encoding='utf-8', errors='replace').read()
        m = token_re.search(txt)
        if m:
            js = m.group(1)
            try:
                wh = json.loads(js)
            except Exception:
                # try to fix trailing commas or single quotes
                fixed = js.replace("'", '"')
                wh = json.loads(fixed)
            timestamps = wh.get('timestamps', []) if isinstance(wh, dict) else []
            weights = wh.get('weights', {}) if isinstance(wh, dict) else {}
            # prepare a richer textual summary
            if timestamps:
                n = len(timestamps)
                # determine latest weight for this symbol
                my_weight = None
                if symbol in weights:
                    arr = weights.get(symbol)
                    if isinstance(arr, list) and len(arr) > 0:
                        my_weight = arr[-1]
                # compute trend using first and last non-null values
                def first_last_nonnull(arr):
                    if not isinstance(arr, list):
                        return (None, None)
                    first = next((x for x in arr if x is not None), None)
                    last = next((x for x in reversed(arr) if x is not None), None)
                    return (first, last)

                # Build top weights snapshot (latest) for quick context
                top = []
                for k, v in weights.items():
                    val = None
                    if isinstance(v, list) and len(v) > 0:
                        # take last non-null
                        val = next((x for x in reversed(v) if x is not None), None)
                    elif v is not None:
                        val = v
                    top.append((k, val))
                # sort by val desc (None last)
                top_sorted = sorted(top, key=lambda x: (x[1] is None, -(x[1] or 0)))[:5]
                top_str = ', '.join([f"{k}: {v if v is not None else 'N/A'}" for k, v in top_sorted])

                # trend for the symbol
                trend = 'N/A'
                if symbol in weights and isinstance(weights[symbol], list):
                    fval, lval = first_last_nonnull(weights[symbol])
                    if fval is None or lval is None:
                        trend = 'insufficient data'
                    else:
                        if abs(lval - fval) < 1e-6:
                            trend = 'stable'
                        elif lval > fval:
                            trend = 'increasing'
                        else:
                            trend = 'decreasing'

                # include best_per_generation summary from latest snapshot telemetry when available
                best_summary = ''
                try:
                    if isinstance(latest_telemetry, dict):
                        bpg = latest_telemetry.get('best_per_generation')
                        if isinstance(bpg, list) and bpg:
                            best_summary = f"Best fitness (per generation): first={bpg[0]:.4f}, last={bpg[-1]:.4f}. "
                except Exception:
                    best_summary = ''

                caption = (f'Embedded weight history with {n} timestamp(s). Trend for {symbol}: {trend}. '
                           f'Latest weight (if available): {my_weight if my_weight is not None else "N/A"}. '
                           f'Sample top weights: {top_str}. {best_summary}').strip()
            else:
                caption = 'Embedded telemetry present but no timestamps.'
    except Exception as e:
        caption = f'Failed to parse embedded telemetry: {e}'

    reports.append({'symbol': symbol, 'html': f, 'img': img_path, 'caption': caption})

# Load model comparison data if present
model_comp = None
comp_path = os.path.join(ROOT, 'strategy_comparison_results.json')
if os.path.exists(comp_path):
    try:
        model_comp = json.load(open(comp_path, 'r', encoding='utf-8'))
    except Exception:
        model_comp = None

# Build PDF
doc = SimpleDocTemplate(OUT_PDF, pagesize=A4, rightMargin=20*mm,leftMargin=20*mm,topMargin=20*mm,bottomMargin=20*mm)
story = []
story.append(Paragraph('CRISPR - All Stocks Results', heading))
story.append(Spacer(1,6))
story.append(Paragraph(f'Generated: {datetime.utcnow().isoformat()}Z', body))
story.append(Spacer(1,12))

for r in reports:
    story.append(Paragraph(f"{r['symbol']}", subh))
    story.append(Spacer(1,6))
    if r['img'] and os.path.exists(r['img']):
        im = Image(r['img'])
        # scale to page width
        im.drawWidth = 160*mm
        im.drawHeight = im.drawWidth * (im.imageHeight / im.imageWidth)
        story.append(im)
    else:
        story.append(Paragraph('(screenshot not available)', body))
    story.append(Spacer(1,6))
    story.append(Paragraph(r['caption'], body))
    story.append(PageBreak())

# Add model comparison section
story.append(Paragraph('Model Comparison', heading))
story.append(Spacer(1,6))
if model_comp:
    try:
        pretty = json.dumps(model_comp, indent=2, ensure_ascii=False)
        # break into paragraphs (not ideal for huge JSON)
        for line in pretty.splitlines():
            story.append(Paragraph(line, mono))
    except Exception as e:
        story.append(Paragraph(f'Failed to include model comparison: {e}', body))
else:
    story.append(Paragraph('No `strategy_comparison_results.json` found or failed to parse.', body))

story.append(PageBreak())
story.append(Paragraph('End of report', body))

print('Writing PDF to', OUT_PDF)
doc.build(story)
print('Done')
