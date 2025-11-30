#!/usr/bin/env python3
"""Assemble selected project artifacts into a single PDF report.

Writes /tmp/crispr_full_report.pdf containing:
 - Short conversation summary
 - Key changed source files (generator, dashboard client, server)
 - GA smoke snapshot(s)
 - One or two representative dashboard HTML files (as raw text)

This script uses reportlab (pip install reportlab).
"""
import io
import json
import glob
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
from reportlab.lib.units import mm

OUT = '/tmp/crispr_full_report.pdf'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Files to include (if present)
files = [
    'scripts/generate_dashboards.py',
    'src/visualization/dashboard.py',
    'poc/presentation_v2/server.py',
    'scripts/run_ga_smoke.py',
]

# Snapshots and tmp outputs
extra_json = glob.glob('/tmp/ga_smoke_snapshot.json') + glob.glob('poc/presentation_v2/snapshots/*.json')
# Dashboards to include (a few examples if present)
dash_files = [
    'dashboards/index.html',
    'dashboards/aapl_dashboard.html',
]

styles = getSampleStyleSheet()
mono = ParagraphStyle('Mono', parent=styles['Normal'], fontName='Courier', fontSize=9, leading=11)
heading = ParagraphStyle('Heading', parent=styles['Heading1'], fontSize=14, leading=16)
subh = ParagraphStyle('SubH', parent=styles['Heading2'], fontSize=12, leading=14)

story = []

# Title
story.append(Paragraph('CRISPR - Aggregated Results Report', heading))
story.append(Spacer(1, 6))
story.append(Paragraph(f'Generated: {datetime.utcnow().isoformat()}Z', styles['Normal']))
story.append(Spacer(1, 12))

# Short summary (reconstructed from repository state)
summary = """
This report bundles recent analysis artifacts and telemetry produced while instrumenting the Genetic Algorithm editor and generating dashboards.
Included artifacts: GA smoke snapshots, modified dashboard embedding script, dashboard client code, and the demo server snapshot.
These results were produced during an interactive session that:
 - Instrumented per-generation weight recording in the GA editor
 - Added canonicalization to `scripts/generate_dashboards.py` and `src/visualization/dashboard.py`
 - Ran a smoke GA and saved a snapshot to /tmp and persisted snapshots in poc/presentation_v2/snapshots
 - Embedded a canonical `window.__INITIAL_WEIGHT_HISTORY` into dashboards/*.html
"""
story.append(Paragraph('Summary', subh))
story.append(Spacer(1,6))
story.append(Paragraph(summary.strip().replace('\n','<br/>'), styles['Normal']))
story.append(Spacer(1,12))

# Include key files
for f in files:
    fp = os.path.join(ROOT, f)
    if os.path.exists(fp):
        story.append(Paragraph(f'File: {f}', subh))
        story.append(Spacer(1,4))
        try:
            text = open(fp, 'r', encoding='utf-8', errors='replace').read()
            # limit size to avoid enormous PDFs
            MAX = 20000
            if len(text) > MAX:
                text = text[:MAX] + '\n\n... (truncated) ...'
            story.append(Preformatted(text, mono))
        except Exception as e:
            story.append(Paragraph(f'Failed to read {f}: {e}', styles['Normal']))
        story.append(PageBreak())

# Include JSON snapshots
if extra_json:
    story.append(Paragraph('Snapshots & JSON outputs', subh))
    story.append(Spacer(1,6))
    for jfn in extra_json:
        try:
            text = open(jfn, 'r', encoding='utf-8', errors='replace').read()
            # pretty-format if JSON
            try:
                obj = json.loads(text)
                pretty = json.dumps(obj, indent=2, ensure_ascii=False)
            except Exception:
                pretty = text
            story.append(Paragraph(f'JSON: {os.path.basename(jfn)}', styles['Normal']))
            story.append(Spacer(1,4))
            story.append(Preformatted(pretty, mono))
            story.append(Spacer(1,6))
        except Exception as e:
            story.append(Paragraph(f'Failed to read {jfn}: {e}', styles['Normal']))
    story.append(PageBreak())

# Include small selection of dashboards as raw HTML
for df in dash_files:
    fp = os.path.join(ROOT, df)
    if os.path.exists(fp):
        story.append(Paragraph(f'Dashboard: {df}', subh))
        story.append(Spacer(1,4))
        try:
            text = open(fp, 'r', encoding='utf-8', errors='replace').read()
            MAX = 30000
            if len(text) > MAX:
                text = text[:MAX] + '\n\n... (truncated) ...'
            story.append(Preformatted(text, mono))
            story.append(PageBreak())
        except Exception as e:
            story.append(Paragraph(f'Failed to read {df}: {e}', styles['Normal']))

# Footer
story.append(Paragraph('End of report', styles['Normal']))

# Build PDF
os.makedirs(os.path.dirname(OUT), exist_ok=True)
print('Writing PDF to', OUT)
doc = SimpleDocTemplate(OUT, pagesize=A4,
                        rightMargin=20*mm,leftMargin=20*mm,
                        topMargin=20*mm,bottomMargin=20*mm)

try:
    doc.build(story)
    print('PDF generation complete:', OUT)
except Exception as e:
    print('PDF generation failed:', e)
    raise
