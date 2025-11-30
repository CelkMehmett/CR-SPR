import sys
sys.path.insert(0, '.')

from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite

# Create a minimal genome with one strategy/chromosome and one parameter
gen = FinancialGenome(name='test_genome')
gen.add_chromosome('AAPL_strategy')
gen.add_gene('AAPL_strategy', 'momentum_threshold', 0.5, param_type='strategy')

# Create a simple target site for editing
target = TargetSite(
    parameter_path='AAPL_strategy.momentum_threshold',
    current_value=0.5,
    target_value=0.6,
    confidence=0.9,
    priority=1,
    edit_type='adjust',
    rationale='smoke test'
)

# Small, fast GA for smoke test
config = EditingConfig(population_size=8, num_generations=6, mutation_rate=0.3, elitism_ratio=0.25)
editor = GeneticAlgorithmEditor(name='smoke_editor', config=config, seed=12345)

print('Running GA smoke test...')
res = editor.edit(target, gen)
print('Edit result:', res.success, 'after_value:', res.after_value)

stats = editor.get_evolution_statistics()
print('\nWeight history (timestamps, weights):')
print(stats.get('weight_history'))

# Save a tiny snapshot to /tmp for inspection
import json
open('/tmp/ga_smoke_snapshot.json', 'w').write(json.dumps({'stats': stats}, default=str))
print('Snapshot written to /tmp/ga_smoke_snapshot.json')
