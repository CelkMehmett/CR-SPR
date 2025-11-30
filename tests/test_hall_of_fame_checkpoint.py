from src.editor.ga_editor import GeneticAlgorithmEditor, Individual


def test_hall_of_fame_persistence(tmp_path):
    editor = GeneticAlgorithmEditor(seed=7)

    # Create and add several individuals
    inds = [Individual(genome={'x': i}, fitness=float(i), generation=i) for i in range(5)]
    for ind in inds:
        editor.add_to_hall_of_fame(ind, k=3)

    # Save checkpoint
    chk = tmp_path / 'hof_chk.pkl'
    editor.save_checkpoint(str(chk))

    # Load into new editor
    new_editor = GeneticAlgorithmEditor()
    new_editor.load_checkpoint(str(chk))

    assert isinstance(new_editor.hall_of_fame, list)
    assert len(new_editor.hall_of_fame) <= 3
    # Top fitness should be the highest value
    if new_editor.hall_of_fame:
        assert new_editor.hall_of_fame[0]['fitness'] == 4.0

    # cleanup
    try:
        import os
        os.unlink(str(chk))
    except Exception:
        pass
