#!/usr/bin/env python3
"""Assemble report including a screenshot image into a single PDF.
Produces /tmp/crispr_full_report_with_screenshot.pdf
"""
import io, os, glob, json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak, Image
from reportlab.lib.units import mm

OUT = '/tmp/crispr_full_report_with_screenshot.pdf'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

styles = getSampleStyleSheet()
mono = ParagraphStyle('Mono', parent=styles['Normal'], fontName='Courier', fontSize=9, leading=11)
heading = ParagraphStyle('Heading', parent=styles['Heading1'], fontSize=14, leading=16)
subh = ParagraphStyle('SubH', parent=styles['Heading2'], fontSize=12, leading=14)

story = []
story.append(Paragraph('CRISPR - Aggregated Results Report (with screenshot)', heading))
story.append(Spacer(1, 6))
story.append(Paragraph(f'Generated: {datetime.utcnow().isoformat()}Z', styles['Normal']))
story.append(Spacer(1, 12))

# Include screenshot if present
img_path = '/tmp/aapl_dashboard.png'
if os.path.exists(img_path):
    story.append(Paragraph('Rendered Dashboard Screenshot (AAPL)', subh))
    story.append(Spacer(1,6))
    try:
        im = Image(img_path)
        im.drawHeight = 160*mm * (im.imageHeight/im.imageWidth)
        im.drawWidth = 160*mm
        story.append(im)
        story.append(PageBreak())
    except Exception as e:
        story.append(Paragraph('Failed to include image: ' + str(e), styles['Normal']))
        story.append(Spacer(1,6))

# Reuse content from previous assemble script (include key files)
files = [
    'scripts/generate_dashboards.py',
    'src/visualization/dashboard.py',
    'poc/presentation_v2/server.py',
    'scripts/run_ga_smoke.py',
]
for f in files:
    fp = os.path.join(ROOT, f)
    if os.path.exists(fp):
        story.append(Paragraph(f'File: {f}', subh))
        story.append(Spacer(1,4))
        try:
            text = open(fp, 'r', encoding='utf-8', errors='replace').read()
            MAX = 20000
            if len(text) > MAX:
                text = text[:MAX] + '\n\n... (truncated) ...'
            story.append(Preformatted(text, mono))
        except Exception as e:
            story.append(Paragraph(f'Failed to read {f}: {e}', styles['Normal']))
        story.append(PageBreak())

# Include snapshots
extra_json = glob.glob('/tmp/ga_smoke_snapshot.json') + glob.glob('poc/presentation_v2/snapshots/*.json')
if extra_json:
    story.append(Paragraph('Snapshots & JSON outputs', subh))
    story.append(Spacer(1,6))
    for jfn in extra_json:
        try:
            text = open(jfn, 'r', encoding='utf-8', errors='replace').read()
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

# Finish
story.append(Paragraph('End of report', styles['Normal']))

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
