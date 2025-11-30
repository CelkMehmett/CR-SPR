import os
import subprocess


def test_crispr_smoke_runs(tmp_path):
    out_csv = tmp_path / 'out.csv'
    audit = tmp_path / 'audit.jsonl'
    model_dir = tmp_path / 'models'
    cmd = [
        'python3',
        os.path.join(os.path.dirname(__file__), '..', 'scripts', 'bench_crispr_controller.py'),
        '--n-stocks', '1',
        '--iters', '1',
        '--seed', '7',
        '--out', str(out_csv),
        '--lstm-epochs', '1'
    ]
    env = os.environ.copy()
    # ensure controller writes to our tmp paths
    env['PYTHONUNBUFFERED'] = '1'
    # run with cwd set to repo root
    repo_root = os.path.join(os.path.dirname(__file__), '..')
    p = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, timeout=60)
    assert p.returncode == 0, f"stderr: {p.stderr.decode()[:200]}"
    # check audit file exists (default path)
    assert os.path.exists(os.path.join(repo_root, 'bench_crispr_audit.jsonl'))
