from datetime import datetime
import sys
import os
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite

OUT_DIR = os.path.join(os.path.dirname(__file__), "poc", "presentation_v2", "snapshots")
os.makedirs(OUT_DIR, exist_ok=True)

# Expanded symbol list: a large set of equities + commodity tickers / ETFs
SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK-B", "JPM", "JNJ",
    "V", "PG", "MA", "UNH", "HD", "BAC", "XOM", "CVX", "DIS", "INTC",
    "KO", "PFE", "CSCO", "NFLX", "ADBE", "CMCSA", "T", "VZ", "WMT", "NKE",
    # Commodities / ETFs
    "CL", "GC", "SI", "NG", "HG", "GLD", "SLV", "USO", "DBA", "XLE"
]

# GA params - moderate to keep runtime reasonable
POPULATION_SIZE = 120
NUM_GENERATIONS = 30
MUTATION_RATE = 0.15


def main():
    print(f"Running expanded GA with {len(SYMBOLS)} symbols: pop={POPULATION_SIZE}, gens={NUM_GENERATIONS}")

    # Build a simple FinancialGenome with per-symbol strategy chromosomes and a couple of editable genes
    model = FinancialGenome('expanded_run_multi_assets')
    targets = []

    for symbol in SYMBOLS:
        chrom = f"{symbol}_strategy"
        try:
            model.add_chromosome(chrom)
            # Add a few representative genes
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
        except Exception:
            # If adding a chromosome/gene fails for a symbol, skip it but continue
            print(f"Warning: skipping symbol {symbol} due to genome construction error")

    editor = GeneticAlgorithmEditor(name='expanded_run_editor', config=EditingConfig(population_size=POPULATION_SIZE, num_generations=NUM_GENERATIONS, mutation_rate=MUTATION_RATE, elitism_ratio=0.1))
    context = {'targets': targets, 'model_genome': model}

    print(f'Starting expanded GA: symbols={len(targets)//2} pop={POPULATION_SIZE} gens={NUM_GENERATIONS} mut={MUTATION_RATE}')
    try:
        # initialize joint population
        editor._population = editor._initialize_population_batch(targets, context)
    except Exception:
        pass

    try:
        best = editor._evolve_population(context)
    except Exception as e:
        print('Evolution failed:', e)
        raise

    stats = {}
    try:
        stats = editor.get_evolution_statistics() or {}
    except Exception:
        pass

    snap = model.create_snapshot()
    meta = snap.setdefault('metadata', {})
    meta['telemetry'] = stats
    meta['run_info'] = {'symbols': SYMBOLS, 'population_size': POPULATION_SIZE, 'num_generations': NUM_GENERATIONS, 'mutation_rate': MUTATION_RATE}
    now = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    fn = os.path.join(OUT_DIR, f'{now}_expanded_run_snapshot.json')
    with open(fn, 'w', encoding='utf-8') as fh:
        json.dump(snap, fh, default=str, indent=2)

    print('Wrote expanded run snapshot to', fn)
    print('Telemetry timestamps:', len(stats.get('weight_history', {}).get('timestamps', [])))


if __name__ == '__main__':
    main()
