import sys
import os
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from poc.run_self_healing import run
from types import SimpleNamespace


def test_run_smoke(tmp_path):
    ns = SimpleNamespace(csv=None, out_dir=str(tmp_path))
    # run should not raise
    run(ns)
    # log file should exist only if drift detected; ensure no exception
    # check out_dir exists
    assert os.path.isdir(str(tmp_path))
