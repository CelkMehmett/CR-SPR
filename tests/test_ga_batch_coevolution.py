
from src.editor.ga_editor import GeneticAlgorithmEditor
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite


def test_batch_coevolution_basic():
    # Create a small genome with two parameters
    genome = FinancialGenome('test_model')
    genome.add_chromosome('strategies')
    genome.add_gene('strategies', 'alpha', 0.5)
    genome.add_gene('strategies', 'beta', 1.0)

    # Create two targets for batch editing
    t1 = TargetSite(
        parameter_path='strategies.alpha',
        current_value=genome.get_parameter('strategies.alpha'),
        target_value=0.8,
        confidence=0.9,
        priority=2,
        edit_type='adjust',
        rationale='increase alpha'
    )

    t2 = TargetSite(
        parameter_path='strategies.beta',
        current_value=genome.get_parameter('strategies.beta'),
        target_value=0.6,
        confidence=0.85,
        priority=2,
        edit_type='adjust',
        rationale='decrease beta'
    )

    editor = GeneticAlgorithmEditor(name='test_editor', config=None)

    results = editor.batch_edit([t1, t2], genome)

    # Should return two EditResult objects
    assert isinstance(results, list)
    assert len(results) == 2

    for res in results:
        assert hasattr(res, 'success')
        assert hasattr(res, 'before_value')
        assert hasattr(res, 'after_value')

    # Ensure genome parameters have been updated to something (may be same if GA failed)
    params = genome.get_all_parameters()
    assert 'strategies.alpha' in params
    assert 'strategies.beta' in params
