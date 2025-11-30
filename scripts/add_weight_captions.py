#!/usr/bin/env python3
"""
Compute simple per-symbol metrics from the latest telemetry snapshot and inject
human-readable captions into `reports/all_stocks_report.html` under each symbol card.

Metrics computed per symbol:
- timestamps: count
- first/last non-null values and percent change
- std deviation (volatility)
- simple linear trend (slope over index)
- max drawdown (peak->trough relative)

This script is conservative and will only replace the first <p ...> paragraph under each
`<div class='card' id='SYMBOL'>` block.
"""
import json
import os
import re
import sys
from math import isfinite
from statistics import mean, pstdev

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'snapshots')
REPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'reports', 'all_stocks_report.html')


def find_latest_snapshot(dirpath):
    js = [os.path.join(dirpath, f) for f in os.listdir(dirpath) if f.endswith('.json')]
    if not js:
        raise FileNotFoundError('No snapshot JSON files in snapshots dir')
    js.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return js[0]


def safe_float_list(lst):
    out = []
    for v in lst:
        try:
            if v is None:
                continue
            fv = float(v)
            if not isfinite(fv):
                continue
            out.append(fv)
        except Exception:
            continue
    return out


def max_drawdown(series):
    if not series:
        return 0.0
    peak = series[0]
    max_dd = 0.0
    for v in series:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak and peak != 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def linear_slope(series):
    # Fit slope to indices 0..n-1 via simple least squares
    n = len(series)
    if n < 2:
        return 0.0
    xs = list(range(n))
    ys = series
    xmean = mean(xs)
    ymean = mean(ys)
    num = sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys))
    den = sum((x - xmean) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


def format_pct(x):
    try:
        return f"{x*100:.2f}%"
    except Exception:
        return 'N/A'


def build_caption(sym, wh):
    # wh: {'timestamps': [...], 'weights': {sym: [...]}}
    ts = wh.get('timestamps', [])
    wmap = wh.get('weights', {})
    series_raw = wmap.get(sym) or wmap.get(sym.upper()) or wmap.get(sym.lower())
    clean = safe_float_list(series_raw or [])
    n = len(ts)
    n_vals = len(clean)
    if n_vals == 0:
        return f"Embedded weight history with {n} timestamp(s). No numeric weights recorded for {sym}."
    first = clean[0]
    last = clean[-1]
    pct = None
    if first and first != 0:
        pct = (last - first) / first
    s = 0.0
    try:
        s = pstdev(clean) if len(clean) > 1 else 0.0
    except Exception:
        s = 0.0
    slope = linear_slope(clean)
    dd = max_drawdown(clean)
    trend = 'increasing' if slope > 1e-6 else ('decreasing' if slope < -1e-6 else 'flat')
    # Compose text
    parts = []
    parts.append(f"Embedded weight history with {n} timestamp(s). ")
    parts.append(f"Series points: {n_vals}. ")
    parts.append(f"First→Last: {first:.4f} → {last:.4f} ({format_pct(pct) if pct is not None else 'N/A'}). ")
    parts.append(f"Trend: {trend} (slope={slope:.4g}). ")
    parts.append(f"Volatility (std)={s:.4g}. Max drawdown={format_pct(dd)}.")
    return ''.join(parts)


def main():
    snap = None
    try:
        latest = find_latest_snapshot(SNAPSHOT_DIR)
    except Exception as e:
        print('No snapshot found:', e)
        return

    print('Using snapshot:', latest)
    with open(latest, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    telemetry = data.get('metadata', {}).get('telemetry') or {}
    wh = telemetry.get('weight_history') or {}
    if not wh:
        print('No weight_history found in snapshot telemetry')
        return

    # Read report
    with open(REPORT_PATH, 'r', encoding='utf-8') as fh:
        html = fh.read()

    # For each <div class='card' id='SYMBOL'>, replace the first <p ...>...</p> after the h2
    pattern = re.compile(r"(<div class='card' id='(?P<sym>[^']+)'>\s*<h2>.*?</h2>\s*)<p[^>]*>.*?</p>", re.DOTALL)

    def repl(match):
        sym = match.group('sym')
        caption = build_caption(sym, wh)
        newp = f"<p style='color:#444'>{caption}</p>"
        return match.group(1) + newp

    new_html, nsub = pattern.subn(repl, html)
    print(f'Replaced captions for {nsub} symbol cards')

    # Backup original
    bak = REPORT_PATH + '.bak'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8') as fh:
            fh.write(html)

    with open(REPORT_PATH, 'w', encoding='utf-8') as fh:
        fh.write(new_html)

    print('Updated report at', REPORT_PATH)


if __name__ == '__main__':
    main()
