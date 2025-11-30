#!/usr/bin/env python3
"""
Copy paper trading demo results to the poc/presentation_v2/ directory
for easy access/serving.
"""
import os
import shutil
import sys
from pathlib import Path

DEMO_OUT_PATHS = {
    'summary': '/tmp/paper_run_demo_summary.json',
    'trades': '/tmp/paper_run_demo_trades.csv',
    'equity': '/tmp/paper_run_demo_equity.png',
}

TARGET_DIR = os.path.join(os.path.dirname(__file__), '..', 'poc', 'presentation_v2', 'paper_trading_results')


def publish_results():
    """Copy results from /tmp to project directory."""
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    copied = []
    for name, src_path in DEMO_OUT_PATHS.items():
        if os.path.exists(src_path):
            dst_path = os.path.join(TARGET_DIR, os.path.basename(src_path))
            shutil.copy2(src_path, dst_path)
            copied.append((name, dst_path))
            print(f'✓ Copied {name}: {dst_path}')
        else:
            print(f'⊘ {name} not found: {src_path}')
    
    print(f'\nPublished {len(copied)}/{len(DEMO_OUT_PATHS)} paper trading results to: {TARGET_DIR}')
    return TARGET_DIR


if __name__ == '__main__':
    target = publish_results()
    print(f'\nLive demo can now reference these files from: {target}/')
