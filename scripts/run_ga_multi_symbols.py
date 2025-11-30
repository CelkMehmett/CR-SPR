#!/usr/bin/env python3
"""Run a short GA over a list of symbols including commodities and write a server-style snapshot.

Assumptions:
- MarketDataLoader/backtest code can handle the chosen commodity tickers (CL, GC, SI).
- This is a smoke run: small population and generations to produce telemetry quickly.

Output: writes a snapshot JSON into poc/presentation_v2/snapshots with metadata.telemetry populated.
"""
import sys
import os
import time
import json
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite

# Symbols: include equities + commodity tickers
symbols = ['AAPL', 'MSFT', 'GOOGL', 'CL', 'GC', 'SI']
# Reasonable defaults for a smoke run
pop = 12
gens = 8
mut = 0.25

# Build a FinancialGenome and simple targets per symbol
model = FinancialGenome('smoke_multi_assets')
targets = []
for symbol in symbols:
    chrom = f'{symbol}_strategy'
    model.add_chromosome(chrom)
    model.add_gene(chrom, 'momentum_threshold', 0.05)
    model.add_gene(chrom, 'stop_loss', 0.02)
    t1 = TargetSite(
        parameter_path=f'{chrom}.momentum_threshold',
        current_value=model.get_parameter(f'{chrom}.momentum_threshold'),
        target_value=0.08,
        confidence=0.9,
        priority=1,
        edit_type='adjust',
        rationale=f'optimize momentum for {symbol}'
    )
    t2 = TargetSite(
        parameter_path=f'{chrom}.stop_loss',
        current_value=model.get_parameter(f'{chrom}.stop_loss'),
        target_value=0.015,
        confidence=0.9,
        priority=1,
        edit_type='adjust',
        rationale=f'tighten stop loss for {symbol}'
    )
    targets.extend([t1, t2])

editor = GeneticAlgorithmEditor(name='smoke_multi_editor', config=EditingConfig(population_size=pop, num_generations=gens, mutation_rate=mut, elitism_ratio=0.15))

context = {'targets': targets, 'model_genome': model}

print(f"Starting smoke GA for symbols: {', '.join(symbols)} (pop={pop}, gens={gens})")

# Initialize population
try:
    editor._population = editor._initialize_population_batch(targets, context)
except Exception:
    # some implementations may already initialize internally
    pass

# Run evolution
try:
    best = editor._evolve_population(context)
except Exception as e:
    print('Evolution error', e)
    sys.exit(1)

print('Evolution finished, collecting stats...')
try:
    stats = editor.get_evolution_statistics()
except Exception:
    stats = {}

# Create snapshot and persist
snap = model.create_snapshot()
meta = snap.setdefault('metadata', {})
meta['telemetry'] = stats or {}
meta['run_info'] = {'symbols': symbols, 'population_size': pop, 'num_generations': gens, 'mutation_rate': mut}
now = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
fn = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'snapshots', f'{now}_smoke_multi_assets.json')
# Ensure directory exists (in case path differs)
dst_dir = os.path.dirname(fn)
os.makedirs(dst_dir, exist_ok=True)
with open(fn, 'w', encoding='utf-8') as fh:
    json.dump(snap, fh, default=str, indent=2)

print('Wrote snapshot to', fn)
print('Telemetry summary:')
print(json.dumps({'timestamp_count': len(stats.get('weight_history', {}).get('timestamps', [])), 'best_per_generation': stats.get('best_per_generation', [])}, indent=2))
print('Done')
