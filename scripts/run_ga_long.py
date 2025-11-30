#!/usr/bin/env python3
"""Run a longer GA (for deeper telemetry) and persist snapshot.

Defaults: population=100, generations=50, symbols include equities+commodities.
Writes snapshot to poc/presentation_v2/snapshots.
"""
import sys, os, json
from datetime import datetime
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite

symbols = ['AAPL','MSFT','GOOGL','CL','GC','SI']
pop = 100
gens = 50
mut = 0.2

model = FinancialGenome('long_run_multi_assets')
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
    targets.extend([t1,t2])

editor = GeneticAlgorithmEditor(name='long_run_editor', config=EditingConfig(population_size=pop, num_generations=gens, mutation_rate=mut, elitism_ratio=0.1))
context = {'targets': targets, 'model_genome': model}

print(f'Starting long GA: symbols={symbols} pop={pop} gens={gens} mut={mut}')
try:
    editor._population = editor._initialize_population_batch(targets, context)
except Exception:
    pass

try:
    best = editor._evolve_population(context)
except Exception as e:
    print('Evolution failed:', e)
    sys.exit(1)

stats = {}
try:
    stats = editor.get_evolution_statistics() or {}
except Exception:
    pass

snap = model.create_snapshot()
meta = snap.setdefault('metadata', {})
meta['telemetry'] = stats
meta['run_info'] = {'symbols': symbols, 'population_size': pop, 'num_generations': gens, 'mutation_rate': mut}
now = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
path = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'snapshots')
os.makedirs(path, exist_ok=True)
fn = os.path.join(path, f'{now}_long_run_multi_assets.json')
with open(fn, 'w', encoding='utf-8') as fh:
    json.dump(snap, fh, default=str, indent=2)

print('Wrote long-run snapshot to', fn)
print('Telemetry timestamps:', len(stats.get('weight_history', {}).get('timestamps', [])))
