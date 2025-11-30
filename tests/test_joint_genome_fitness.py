from src.editor.ga_editor import FitnessFunction, Individual
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite


def simple_objective(genome_dict, context=None):
    # genome_dict is expected to be a flat dict when evaluating temp genome
    # objective: prefer larger 'strategies.alpha' and smaller 'strategies.beta'
    a = float(genome_dict.get('strategies.alpha', 0.0))
    b = float(genome_dict.get('strategies.beta', 0.0))
    return a - b


def test_joint_genome_fitness_applies_edited_values():
    # Setup genome
    genome = FinancialGenome('fit_test')
    genome.add_chromosome('strategies')
    genome.add_gene('strategies', 'alpha', 0.5)
    genome.add_gene('strategies', 'beta', 1.0)

    # Targets corresponding to the two params
    t1 = TargetSite('strategies.alpha', genome.get_parameter('strategies.alpha'), 0.8, 0.9, 1, 'adjust', 'increase alpha')
    t2 = TargetSite('strategies.beta', genome.get_parameter('strategies.beta'), 0.6, 0.9, 1, 'adjust', 'decrease beta')

    # Create individual encoding edited_values that should improve objective
    ind = Individual(genome={'edited_values': [0.8, 0.6]})

    # Create fitness function with our simple objective and weights that
    # focus solely on performance so the returned value equals the objective.
    ff = FitnessFunction(objective_function=simple_objective, weights={'performance': 1.0, 'stability': 0.0, 'simplicity': 0.0})

    context = {'targets': [t1, t2], 'model_genome': genome}

    fitness = ff.evaluate(ind, context)

    # Compute expected objective applied to edited genome
    expected = 0.8 - 0.6

    assert abs(fitness - expected) < 1e-6
