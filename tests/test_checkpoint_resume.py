import os
from src.editor.ga_editor import GeneticAlgorithmEditor, Individual


def test_checkpoint_save_and_restore(tmp_path):
    # Create editor and set a small, deterministic population
    editor = GeneticAlgorithmEditor(seed=42)
    editor.config.population_size = 3

    # Build a small population and generation history
    editor._population = [Individual(genome={'x': i}, fitness=float(i)) for i in range(3)]
    editor._best_individual = editor._population[-1]
    editor._generation_history = [
        {'generation': 0, 'best_fitness': 0.0},
        {'generation': 1, 'best_fitness': 1.0}
    ]

    # Save expected snapshots
    expected_best_fitness = editor._best_individual.fitness
    expected_pop_len = len(editor._population)
    expected_gen_history = list(editor._generation_history)

    # Save checkpoint
    chk_path = tmp_path / 'ga_checkpoint.pkl'
    editor.save_checkpoint(str(chk_path))

    # Mutate in-memory state to ensure load restores
    editor._population = []
    editor._best_individual = None
    editor._generation_history = []

    # Create a fresh editor and load checkpoint
    new_editor = GeneticAlgorithmEditor()
    new_editor.load_checkpoint(str(chk_path))

    assert len(new_editor._population) == expected_pop_len
    assert getattr(new_editor._best_individual, 'fitness', None) == expected_best_fitness
    assert new_editor._generation_history == expected_gen_history

    # Clean up
    try:
        os.unlink(str(chk_path))
    except Exception:
        pass
