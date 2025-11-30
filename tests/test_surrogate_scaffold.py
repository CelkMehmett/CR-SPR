
from src.editor import surrogate
from src.editor.ga_editor import Individual
import numpy as np


def make_ind(vec, fitness):
    return Individual(genome={'x': np.array(vec)}, fitness=float(fitness))


def test_surrogate_scaffold():
    # Build a tiny population with numeric genomes
    pop = [make_ind([i, i + 0.1], fitness=float(i * 0.5)) for i in range(6)]

    available = surrogate.is_surrogate_available()

    model = surrogate.train_surrogate(pop, max_estimators=10)

    if not available:
        assert model is None
    else:
        # model should be a fitted estimator; predictions should be a list of floats
        preds = surrogate.predict_surrogate(model, pop)
        assert preds is not None
        assert isinstance(preds, list)
        assert len(preds) == len(pop)
