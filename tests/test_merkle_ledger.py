import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.merkle_ledger import MerkleLedger


def test_merkle_basic():
    m = MerkleLedger()
    ids = []
    for i in range(5):
        rec = {'i': i, 'v': f'value-{i}'}
        ids.append(m.append(rec))
    r = m.root()
    assert isinstance(r, str)
    # verify inclusion proof for leaf 2
    proof = m.inclusion_proof(2)
    assert isinstance(proof, list)
    leaf_hash = ids[2]
    ok = MerkleLedger.verify_proof(leaf_hash, proof, r)
    assert ok
