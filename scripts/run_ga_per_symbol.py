#!/usr/bin/env python3
"""
Run GA independently for each symbol and persist per-symbol weight histories.
Each symbol gets its own GA run, generating individual optimized parameters.

Output: per-symbol snapshots with weight history telemetry.
"""
import json
import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.genome import FinancialGenome

SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'TSLA', 'META', 'NFLX', 'ADBE', 'ACGL',
    'JPM', 'BAC', 'WFC', 'GS', 'BLK',
    'XOM', 'CVX', 'COP', 'MPC', 'PSX',
]

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), 'poc', 'presentation_v2', 'snapshots')
PER_SYMBOL_DIR = os.path.join(SNAPSHOT_DIR, 'per_symbol_results')


def run_ga_for_symbol(symbol: str, population_size: int = 40, num_generations: int = 15):
    """
    Run GA for a single symbol using random weight mutations.
    """
    print(f"\n{'='*60}")
    print(f"Running GA for {symbol}: pop={population_size} gens={num_generations}")
    print(f"{'='*60}")

    try:
        # Create genome with a simple chromosome for the symbol
        genome = FinancialGenome(name=f"genome_{symbol}", model_type="trading_strategy")
        genome.add_chromosome(f'{symbol}_params')
        
        # Add parameters for this symbol
        genome.add_gene(
            chromosome=f'{symbol}_params',
            gene_name='momentum_threshold',
            value=0.05,
            param_type='hyperparameter',
            constraints={'min': 0.01, 'max': 0.15}
        )
        genome.add_gene(
            chromosome=f'{symbol}_params',
            gene_name='stop_loss',
            value=0.02,
            param_type='hyperparameter',
            constraints={'min': 0.005, 'max': 0.05}
        )
        genome.add_gene(
            chromosome=f'{symbol}_params',
            gene_name='position_size',
            value=0.1,
            param_type='hyperparameter',
            constraints={'min': 0.05, 'max': 0.25}
        )

        # Configure and run GA
        config = EditingConfig(
            population_size=population_size,
            num_generations=num_generations,
            mutation_rate=0.15,
            elitism_ratio=0.1,
        )

        editor = GeneticAlgorithmEditor(genome=genome, config=config)
        best_individual = editor.run()
        stats = editor.get_evolution_statistics()

        print(f"✓ GA complete for {symbol}")
        print(f"  Best fitness: {stats.get('best_fitness', 'N/A')}")
        print(f"  Generations: {stats.get('num_generations_configured', num_generations)}")

        # Extract weight history
        weight_history = stats.get('weight_history', {})

        return {
            'symbol': symbol,
            'success': True,
            'best_fitness': stats.get('best_fitness', 0.0),
            'weight_history': weight_history,
            'num_generations': stats.get('num_generations_configured', num_generations),
            'statistics': stats,
        }
    except Exception as e:
        print(f"✗ GA failed for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'symbol': symbol,
            'success': False,
            'error': str(e),
            'weight_history': {},
        }


def persist_per_symbol_result(symbol: str, result: dict, base_dir: str):
    """
    Save per-symbol GA result to a JSON file.
    """
    os.makedirs(base_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    filename = f'{timestamp}_{symbol}_ga_result.json'
    filepath = os.path.join(base_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, indent=2, default=str)

    print(f"  Saved to: {filepath}")
    return filepath


def main():
    print(f"Running per-symbol GA models for {len(SYMBOLS)} symbols")
    print(f"Target directory: {PER_SYMBOL_DIR}\n")

    os.makedirs(PER_SYMBOL_DIR, exist_ok=True)

    all_results = []
    successful = 0

    for symbol in SYMBOLS:
        result = run_ga_for_symbol(symbol, population_size=30, num_generations=12)
        all_results.append(result)

        if result['success']:
            successful += 1
            persist_per_symbol_result(symbol, result, PER_SYMBOL_DIR)
        else:
            print(f"  ⚠ Skipped {symbol} due to error")

    # Summary
    print(f"\n{'='*60}")
    print(f"Per-symbol GA run complete: {successful}/{len(SYMBOLS)} successful")
    print(f"{'='*60}\n")

    # Write summary
    summary_file = os.path.join(PER_SYMBOL_DIR, 'summary.json')
    with open(summary_file, 'w', encoding='utf-8') as fh:
        json.dump({
            'timestamp': datetime.utcnow().isoformat(),
            'total_symbols': len(SYMBOLS),
            'successful': successful,
            'results': all_results,
        }, fh, indent=2, default=str)

    print(f"Wrote summary to: {summary_file}")
    print(f"\nPer-symbol results available in: {PER_SYMBOL_DIR}/")


if __name__ == '__main__':
    main()
