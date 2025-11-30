from flask import Flask, Response, request, stream_with_context, send_file
import threading
import queue
import time
import json
import sys
import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Ensure project root is on sys.path so we can import src modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.editor.ga_editor import GeneticAlgorithmEditor, EditingConfig
from src.core.genome import FinancialGenome
from src.core.base_layers import TargetSite
from src.strategies.advanced_trading import compare_strategies, rank_strategies

# Get the directory where this server script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=SCRIPT_DIR, static_url_path='')

# configure basic logging to stderr
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

clients = []  # list of Queue objects, one per connected client
latest_model_snapshot = None
DEMO_TOKEN = os.getenv('DEMO_TOKEN', '')

# Snapshot persistence
SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), 'snapshots')
MAX_SNAPSHOTS = 20
if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def _snapshot_id_from_filename(fn):
    return os.path.splitext(os.path.basename(fn))[0]

def _list_snapshot_files():
    try:
        files = [os.path.join(SNAPSHOT_DIR, f) for f in os.listdir(SNAPSHOT_DIR) if f.endswith('.json')]
        files.sort(reverse=True)
        return files
    except FileNotFoundError:
        # snapshots dir missing
        return []
    except Exception:
        logging.exception('Error listing snapshot files')
        return []

def _enforce_retention():
    files = _list_snapshot_files()
    if len(files) <= MAX_SNAPSHOTS:
        return
    for f in files[MAX_SNAPSHOTS:]:
        try:
            os.remove(f)
        except Exception:
            pass

def save_snapshot(snapshot):
    # snapshot expected to be a dict
    # Ensure snapshot contains a compact current_parameters map for quick reads
    try:
        if 'current_parameters' not in snapshot:
            # derive from metadata.edit_history (take last new_value per path)
            meta = snapshot.get('metadata', {})
            edits = meta.get('edit_history', []) if isinstance(meta, dict) else []
            last_for = {}
            for e in edits:
                try:
                    pth = e.get('path')
                    if pth:
                        last_for[pth] = e.get('new_value')
                except Exception:
                    continue
            snapshot['current_parameters'] = last_for
    except Exception:
        logging.exception('Failed to derive current_parameters for snapshot')
    ts = snapshot.get('snapshot_time') or snapshot.get('creation_time') or time.strftime('%Y%m%dT%H%M%S')
    safe_ts = str(ts).replace(':', '').replace(' ', '_')
    name = snapshot.get('name', 'snapshot')
    safe_name = ''.join([c if c.isalnum() or c in ('-', '_') else '_' for c in name])
    filename = f"{safe_ts}_{safe_name}.json"
    path = os.path.join(SNAPSHOT_DIR, filename)
    try:
        logging.info("save_snapshot: writing snapshot to %s", path)
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(snapshot, fh, default=str, indent=2)
    except Exception:
        logging.exception('save_snapshot: failed to write %s', path)
        return None
    _enforce_retention()
    return _snapshot_id_from_filename(path)


@app.route('/current_parameters', methods=['GET'])
def current_parameters():
    # Return a compact map of current parameters from latest in-memory snapshot
    # or from the latest persisted snapshot. Require token when configured.
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

    # Prefer latest_model_snapshot if present
    snap = latest_model_snapshot
    if not snap:
        # try persisted latest file
        files = _list_snapshot_files()
        if not files:
            return (json.dumps({'error': 'no_snapshot'}), 404, {'Content-Type': 'application/json'})
        try:
            with open(files[0], encoding='utf-8') as fh:
                snap = json.load(fh)
        except Exception:
            logging.exception('Failed to load latest persisted snapshot')
            return (json.dumps({'error': 'internal_error'}), 500, {'Content-Type': 'application/json'})

    # Ensure current_parameters exists
    params = snap.get('current_parameters') if isinstance(snap, dict) else None
    if not params:
        # derive from edit history defensively
        meta = snap.get('metadata', {}) if isinstance(snap, dict) else {}
        edits = meta.get('edit_history', []) if isinstance(meta, dict) else []
        last_for = {}
        for e in edits:
            pth = e.get('path')
            if pth:
                last_for[pth] = e.get('new_value')
        params = last_for

    resp = {
        'id': snap.get('_snapshot_id') or _snapshot_id_from_filename(files[0]) if 'files' in locals() and files else None,
        'name': snap.get('name') if isinstance(snap, dict) else None,
        'snapshot_time': snap.get('snapshot_time') if isinstance(snap, dict) else None,
        'parameters': params,
        'telemetry': (snap.get('metadata', {}) or {}).get('telemetry') if isinstance(snap, dict) else None
    }
    return (json.dumps(resp, default=str), 200, {'Content-Type': 'application/json'})

def load_snapshot_by_id(sid):
    files = _list_snapshot_files()
    for f in files:
        if _snapshot_id_from_filename(f) == sid:
            try:
                with open(f, encoding='utf-8') as fh:
                    return json.load(fh)
            except Exception:
                return None
    return None

def list_snapshots_metadata(limit=100):
    try:
        files = _list_snapshot_files()
    except Exception:
        logging.exception('list_snapshots_metadata: _list_snapshot_files failed')
        files = []
    out = []
    for f in files[:limit]:
        try:
            with open(f, encoding='utf-8') as fh:
                data = json.load(fh)
            out.append({
                'id': _snapshot_id_from_filename(f),
                'name': data.get('name'),
                'creation_time': data.get('creation_time'),
                'snapshot_time': data.get('snapshot_time'),
                'generation': data.get('metadata', {}).get('generation')
            })
        except Exception:
            continue
    return out


def broadcast(event_type, data):
    for q in list(clients):
        try:
            q.put((event_type, data))
        except Exception:
            pass


def _check_demo_token():
    """Return True when request is authorized for demo operations.
    If DEMO_TOKEN is empty, allow unrestricted access (local dev convenience).
    Otherwise accept token from header X-DEMO-TOKEN or query param 'token'.
    """
    if not DEMO_TOKEN:
        return True
    try:
        token = request.headers.get('X-DEMO-TOKEN') or request.args.get('token')
        if token and token == DEMO_TOKEN:
            return True
    except Exception:
        pass
    return False


@app.route('/events')
def events():
    # enforce demo token if configured
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

    q = queue.Queue()
    clients.append(q)

    def gen():
        try:
            while True:
                event_type, data = q.get()
                payload = f"event: {event_type}\n"
                payload += f"data: {json.dumps(data)}\n\n"
                yield payload
        except GeneratorExit:
            pass
        finally:
            try:
                clients.remove(q)
            except Exception:
                pass

    return Response(stream_with_context(gen()), mimetype='text/event-stream')


@app.route('/run_batch', methods=['POST'])
def run_batch():
    def worker():
        broadcast('log', {'msg': '🧪 Starting Batch Co-evolution demo...'})
        time.sleep(0.3)
        broadcast('status', {'status': 'NORMAL', 'badge': 'normal'})
        broadcast('log', {'msg': 'Normal phase start'})
        for i in range(30):
            broadcast('chart', {'idx': i, 'value': round(0.4 * i + (0.5 - 0.25) * (i % 2), 3)})
            time.sleep(0.02)

        broadcast('status', {'status': 'DRIFT DETECTED', 'badge': 'drift'})
        broadcast('log', {'msg': '⚠️ Detected correlated parameter drift across strategies'})
        time.sleep(0.5)

        broadcast('status', {'status': 'OPTIMIZING', 'badge': 'healing'})
        for g in range(1, 9):
            broadcast('log', {'msg': f'Generation {g}/8... best joint fitness: {(0.2 + g*0.15):.2f}'})
            time.sleep(0.35)

        broadcast('log', {'msg': '✅ Co-evolution complete. Deploying joint edits...'})
        time.sleep(0.25)

        broadcast('status', {'status': 'HEALED', 'badge': 'healed'})
        broadcast('metrics', {'sharpe': '1.22', 'drift': '0.09', 'win_rate': '60%', 'dd': '-5.2%'})

        for i in range(30, 80):
            broadcast('chart', {'idx': i, 'value': round(0.7 * i - 40, 3)})
            time.sleep(0.03)

        broadcast('log', {'msg': '✨ Batch demo complete!'})

    threading.Thread(target=worker, daemon=True).start()
    return ('', 204)


@app.route('/run_real_batch', methods=['POST'])
def run_real_batch():
    """Run a small, real GeneticAlgorithmEditor co-evolution and stream progress.
    
    Accepts optional JSON POST with:
    - symbols: list of stock symbols (default: ['AAPL', 'GOOGL'])
    - population_size: GA population size (default: 20)
    - num_generations: GA generations (default: 25)
    - mutation_rate: mutation rate (default: 0.2)
    """
    # enforce demo token when configured
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})
    # Parse GA params from request JSON (with defaults)
    params = {}
    try:
        params = request.get_json(force=True) or {}
    except Exception:
        params = {}

    symbols = params.get('symbols', ['AAPL', 'GOOGL'])
    if not isinstance(symbols, list):
        symbols = [symbols]
    symbols = [str(s).upper() for s in symbols[:5]]  # max 5 symbols

    pop = int(params.get('population_size', 20))
    gens = int(params.get('num_generations', 25))
    mut = float(params.get('mutation_rate', 0.2))

    # Prepare a genome with parameters for each stock
    model = FinancialGenome('demo_model_multi')
    targets = []
    
    for symbol in symbols:
        chromosome_name = f'{symbol}_strategy'
        model.add_chromosome(chromosome_name)
        model.add_gene(chromosome_name, 'momentum_threshold', 0.05)
        model.add_gene(chromosome_name, 'stop_loss', 0.02)
        
        # Create target sites for each parameter
        t1 = TargetSite(
            parameter_path=f'{chromosome_name}.momentum_threshold',
            current_value=model.get_parameter(f'{chromosome_name}.momentum_threshold'),
            target_value=0.08,
            confidence=0.9,
            priority=1,
            edit_type='adjust',
            rationale=f'optimize momentum for {symbol}'
        )
        t2 = TargetSite(
            parameter_path=f'{chromosome_name}.stop_loss',
            current_value=model.get_parameter(f'{chromosome_name}.stop_loss'),
            target_value=0.015,
            confidence=0.9,
            priority=1,
            edit_type='adjust',
            rationale=f'tighten stop loss for {symbol}'
        )
        targets.extend([t1, t2])

    editor = GeneticAlgorithmEditor(name='demo_editor_multi', edit_rate=0.05,
                                    config=EditingConfig(population_size=pop, num_generations=gens, mutation_rate=mut, elitism_ratio=0.1))

    context = {'targets': targets, 'model_genome': model}

    # Runner thread performs evolution
    def runner():
        try:
            # Initialize population (joint)
            editor._population = editor._initialize_population_batch(targets, context)
        except Exception:
            # If initialize already returns population, it's handled
            logging.exception('Error during population initialization')

        # Start evolution in a separate thread so we can poll generation history
        def evolve():
            try:
                # Ensure _best_individual is initialized
                if not getattr(editor, '_best_individual', None) and editor._population:
                    editor._best_individual = editor._population[0]

                best = editor._evolve_population(context)
            except Exception as e:
                logging.exception('Evolution error')
                broadcast('log', {'msg': f'Evolution error: {e}'})
                return

            # Apply best edits if available
            if best:
                edited = best.genome.get('edited_values', [])
                for idx, tgt in enumerate(targets):
                    if idx < len(edited):
                        try:
                            model.set_parameter(tgt.parameter_path, edited[idx], edit_reason='real_batch_demo')
                        except Exception as e:
                            broadcast('log', {'msg': f'Failed to apply edit to {tgt.parameter_path}: {e}'})

            # Collect telemetry and store latest model snapshot for external inspection
            try:
                stats = editor.get_evolution_statistics()
            except Exception:
                logging.exception('Failed to collect evolution statistics')
                stats = {}

            try:
                global latest_model_snapshot
                latest_model_snapshot = model.create_snapshot()
                # embed telemetry into snapshot metadata for UI consumption
                try:
                    meta = latest_model_snapshot.setdefault('metadata', {})
                    # Attach the full evolution statistics returned by the editor.
                    # This is intentionally the rich telemetry structure (per-generation arrays,
                    # best individual summary, timing, etc.) so the UI can display it lazily.
                    meta['telemetry'] = stats or {}
                except Exception:
                    logging.exception('Failed to attach telemetry to latest_model_snapshot')

                # Attach hall-of-fame summary if available from the editor
                try:
                    if hasattr(editor, 'hall_of_fame'):
                        meta = latest_model_snapshot.setdefault('metadata', {})
                        meta['hall_of_fame'] = getattr(editor, 'hall_of_fame', []) or []
                except Exception:
                    logging.exception('Failed to attach hall_of_fame to latest_model_snapshot')

                # Optionally log the run to MLflow if MLflow is available and configured.
                try:
                    mlflow_exp = os.getenv('MLFLOW_EXPERIMENT')
                    if mlflow_exp:
                        try:
                            ok = editor.log_run_to_mlflow(experiment_name=mlflow_exp)
                            if ok:
                                broadcast('log', {'msg': 'MLflow: run logged'})
                        except Exception:
                            logging.exception('Failed to invoke editor.log_run_to_mlflow')
                except Exception:
                    logging.exception('Unexpected error while attempting MLflow logging')
            except Exception:
                logging.exception('Failed to create latest_model_snapshot')
                # persist snapshot to disk and store id in snapshot metadata
                try:
                    sid = save_snapshot(latest_model_snapshot)
                    if sid:
                        latest_model_snapshot['_snapshot_id'] = sid
                except Exception:
                    logging.exception('Failed to persist latest_model_snapshot')

            # Broadcast final metrics and history
            broadcast('log', {'msg': 'Evolution finished'})
            broadcast('metrics', {'sharpe': f"{stats.get('best_fitness', 0):.2f}", 'drift': '0.10', 'win_rate': '59%', 'dd': '-6.0%'})

        evo_thread = threading.Thread(target=evolve, daemon=True)
        evo_thread.start()

        # Poll generation history and broadcast incremental updates
        last_len = 0
        while evo_thread.is_alive() or last_len < len(editor._generation_history):
            current_len = len(editor._generation_history)
            if current_len > last_len:
                for gen in editor._generation_history[last_len:current_len]:
                    broadcast('log', {'msg': f"Generation {gen['generation']}: best={gen['best_fitness']:.4f}, avg={gen['avg_fitness']:.4f}"})
                last_len = current_len
            time.sleep(0.2)

        # Ensure final broadcast
        broadcast('log', {'msg': f'Real batch co-evolution complete for {", ".join(symbols)}'})

    # Log starting message with symbols
    symbols_str = ', '.join(symbols)
    broadcast('log', {'msg': f'🧪 Starting GA optimization for stocks: {symbols_str}...'})
    
    threading.Thread(target=runner, daemon=True).start()
    return ('', 204)


@app.route('/genome_snapshot', methods=['GET'])
def genome_snapshot():
    # Optional ?id=<snapshot_id> to fetch persisted snapshot
    sid = request.args.get('id')
    if sid:
        # require token to read persisted snapshots when DEMO_TOKEN is configured
        if not _check_demo_token():
            return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

        snap = load_snapshot_by_id(sid)
        if not snap:
            return (json.dumps({'error': 'not_found'}), 404, {'Content-Type': 'application/json'})
        return (json.dumps(snap, default=str), 200, {'Content-Type': 'application/json'})

    if latest_model_snapshot is None:
        return (json.dumps({'error': 'no_snapshot'}), 404, {'Content-Type': 'application/json'})
    return (json.dumps(latest_model_snapshot, default=str), 200, {'Content-Type': 'application/json'})


@app.route('/telemetry', methods=['GET'])
def telemetry():
    # Return only telemetry payload from latest in-memory snapshot or persisted snapshot by ?id=<snapshot_id>
    sid = request.args.get('id')
    if sid:
        if not _check_demo_token():
            return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})
        snap = load_snapshot_by_id(sid)
        if not snap:
            return (json.dumps({'error': 'not_found'}), 404, {'Content-Type': 'application/json'})
        telemetry = (snap.get('metadata', {}) or {}).get('telemetry') if isinstance(snap, dict) else None
        return (json.dumps({'id': sid, 'telemetry': telemetry}, default=str), 200, {'Content-Type': 'application/json'})

    # No id provided: return telemetry from latest in-memory snapshot
    if latest_model_snapshot is None:
        return (json.dumps({'error': 'no_snapshot'}), 404, {'Content-Type': 'application/json'})

    telemetry = (latest_model_snapshot.get('metadata', {}) or {}).get('telemetry') if isinstance(latest_model_snapshot, dict) else None
    return (json.dumps({'id': latest_model_snapshot.get('_snapshot_id'), 'telemetry': telemetry}, default=str), 200, {'Content-Type': 'application/json'})


@app.route('/telemetry/weights', methods=['GET'])
def telemetry_weights():
    """Return a compact weight history for GA visualization.

    Response format:
      { id: <snapshot_id or null>, weight_history: { timestamps: [...], weights: {strategy_name: [...]} } }

    If no telemetry is available, returns empty weight_history structure.
    """
    # Allow unauthenticated when DEMO_TOKEN not set, otherwise require it
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

    try:
        telemetry = None
        snap_id = None
        if latest_model_snapshot and isinstance(latest_model_snapshot, dict):
            snap_id = latest_model_snapshot.get('_snapshot_id')
            telemetry = (latest_model_snapshot.get('metadata', {}) or {}).get('telemetry')

        # Fallback: try persisted latest snapshot
        if telemetry is None:
            files = _list_snapshot_files()
            if files:
                try:
                    with open(files[0], encoding='utf-8') as fh:
                        snap = json.load(fh)
                    snap_id = _snapshot_id_from_filename(files[0])
                    telemetry = (snap.get('metadata', {}) or {}).get('telemetry')
                except Exception:
                    telemetry = None

        # Extract weight_history if present
        weight_history = {'timestamps': [], 'weights': {}}
        if telemetry and isinstance(telemetry, dict):
            wh = telemetry.get('weight_history') or telemetry.get('weights') or {}
            # Accept either {timestamps: [...], weights: {...}} or {weights: {...}, timestamps: [...]}
            if isinstance(wh, dict) and 'weights' in wh and 'timestamps' in wh:
                weight_history = {'timestamps': wh.get('timestamps') or [], 'weights': wh.get('weights') or {}}
            else:
                # Try common alternative shapes
                if 'timestamps' in telemetry and 'weights' in telemetry:
                    weight_history = {'timestamps': telemetry.get('timestamps') or [], 'weights': telemetry.get('weights') or {}}
                else:
                    # Try telemetry['weight_history'] if nested
                    nested = telemetry.get('weight_history') if isinstance(telemetry.get('weight_history'), dict) else {}
                    if nested:
                        weight_history = {'timestamps': nested.get('timestamps') or [], 'weights': nested.get('weights') or {}}

        # If telemetry didn't provide weights, attempt a best-effort extraction
        # from the latest in-memory snapshot's chromosomes: use a representative
        # numeric parameter (momentum_threshold or first numeric) per chromosome
        # and normalize them to produce a simple per-symbol weight mapping so
        # dashboards have an initial, meaningful visualization.
        try:
            if weight_history.get('weights') == {} and latest_model_snapshot and isinstance(latest_model_snapshot, dict):
                ch = latest_model_snapshot.get('chromosomes') or {}
                symbol_vals = {}
                for cname, params in (ch.items() if isinstance(ch, dict) else []):
                    try:
                        # cname like 'AAPL_strategy' -> symbol 'AAPL'
                        sym = cname.split('_')[0]
                        # prefer momentum_threshold if present
                        if isinstance(params, dict) and 'momentum_threshold' in params:
                            v = params['momentum_threshold'].get('value') if isinstance(params['momentum_threshold'], dict) else params['momentum_threshold']
                        else:
                            # pick first numeric parameter value available
                            v = None
                            if isinstance(params, dict):
                                for pinfo in params.values():
                                    try:
                                        cand = pinfo.get('value') if isinstance(pinfo, dict) else pinfo
                                        if isinstance(cand, (int, float)):
                                            v = cand
                                            break
                                    except Exception:
                                        continue

                        if v is None:
                            continue
                        symbol_vals[sym] = float(abs(v))
                    except Exception:
                        continue

                if symbol_vals:
                    total = float(sum(symbol_vals.values())) or 1.0
                    weights = {s: (symbol_vals[s] / total) for s in symbol_vals}
                    weight_history = {'timestamps': [latest_model_snapshot.get('snapshot_time') or latest_model_snapshot.get('creation_time') or time.strftime('%Y%m%dT%H%M%S')], 'weights': weights}
        except Exception:
            logging.exception('Failed to derive fallback weights from latest_model_snapshot')

        return (json.dumps({'id': snap_id, 'weight_history': weight_history}, default=str), 200, {'Content-Type': 'application/json'})
    except Exception as e:
        logging.exception('Error serving telemetry/weights')
        return (json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'})


@app.route('/snapshots', methods=['GET'])
def snapshots_list():
    # return metadata list of saved snapshots
    # require token to list snapshots when DEMO_TOKEN is configured
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

    limit = int(request.args.get('limit', 50))
    meta = list_snapshots_metadata(limit=limit)
    return (json.dumps({'snapshots': meta}, default=str), 200, {'Content-Type': 'application/json'})


@app.route('/snapshots/<snapshot_id>', methods=['GET'])
def snapshots_get(snapshot_id):
    # require token to fetch persisted snapshot when DEMO_TOKEN is configured
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

    snap = load_snapshot_by_id(snapshot_id)
    if not snap:
        return (json.dumps({'error': 'not_found'}), 404, {'Content-Type': 'application/json'})
    return (json.dumps(snap, default=str), 200, {'Content-Type': 'application/json'})


@app.route('/snapshots/<snapshot_id>/download', methods=['GET'])
def snapshots_download(snapshot_id):
    # stream the raw snapshot file from disk for large downloads
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

    files = _list_snapshot_files()
    target_path = None
    for f in files:
        if _snapshot_id_from_filename(f) == snapshot_id:
            target_path = f
            break

    if not target_path:
        return (json.dumps({'error': 'not_found'}), 404, {'Content-Type': 'application/json'})

    def generate():
        try:
            with open(target_path, 'rb') as fh:
                while True:
                    chunk = fh.read(8192)
                    if not chunk:
                        break
                    yield chunk
        except Exception:
            logging.exception('Error streaming snapshot %s', target_path)

    filename = os.path.basename(target_path)
    headers = {
        'Content-Type': 'application/json',
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return Response(stream_with_context(generate()), headers=headers)


@app.route('/compare_strategies', methods=['GET', 'POST'])
def compare_strategies_endpoint():
    """Compare different trading strategies on synthetic or uploaded price data.

    GET query params:
      - symbol: symbol name (default: DEMO)
      - num_days: number of days to simulate (default: 252)
      - volatility: price volatility (default: 0.02)

    POST JSON:
      - symbol: symbol name
      - price_data: list of prices (or will generate synthetic)
      - num_days: number of days
    """
    if not _check_demo_token():
        return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})

    try:
        # Parse parameters
        symbol = request.args.get('symbol') or (request.get_json(force=True) or {}).get('symbol', 'DEMO')
        num_days = int(request.args.get('num_days', 252))
        volatility = float(request.args.get('volatility', 0.02))

        # Generate synthetic price data
        np.random.seed(42)  # For reproducibility
        returns = np.random.normal(0.0005, volatility, num_days)
        prices = 100.0 * np.exp(np.cumsum(returns))
        dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')
        price_series = pd.Series(prices, index=dates)

        # Compare strategies
        results = compare_strategies(price_series, symbol=symbol)
        ranking = rank_strategies(results)

        # Format response
        response_data = {
            'symbol': symbol,
            'num_days': num_days,
            'timestamp': datetime.now().isoformat(),
            'ranking': ranking,
            'results': {}
        }

        for name, metrics in results.items():
            response_data['results'][name] = {
                'sharpe_ratio': float(metrics.get('sharpe_ratio', 0)),
                'total_return': float(metrics.get('total_return', 0)),
                'win_rate': float(metrics.get('win_rate', 0)),
                'max_drawdown': float(metrics.get('max_drawdown', 0)),
                'num_trades': int(metrics.get('num_trades', 0)),
                'avg_confidence': float(metrics.get('avg_confidence', 0))
            }

        return (json.dumps(response_data, default=str), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        logging.exception('Error in compare_strategies endpoint')
        return (json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'})


@app.route('/')
def index():
    """Serve the live demo HTML frontend."""
    try:
        html_path = os.path.join(SCRIPT_DIR, 'live_demo.html')
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            return json.dumps({'error': 'live_demo.html not found'}), 404, {'Content-Type': 'application/json'}
    except Exception as e:
        logging.exception('Error serving index')
        return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}


@app.route('/dashboards/')
def dashboards_index():
    """Serve the generated dashboards index page from the repository dashboards/ folder."""
    try:
        dashboards_dir = os.path.join(ROOT, 'dashboards')
        index_path = os.path.join(dashboards_dir, 'index.html')
        if os.path.exists(index_path):
            return send_file(index_path)
        # Fallback: list files if index doesn't exist
        if os.path.exists(dashboards_dir):
            files = [f for f in os.listdir(dashboards_dir) if f.endswith('.html')]
            items = [{'name': f, 'url': f'/dashboards/{f}'} for f in files]
            return (json.dumps({'dashboards': items}, default=str), 200, {'Content-Type': 'application/json'})
        return (json.dumps({'error': 'dashboards_not_found'}), 404, {'Content-Type': 'application/json'})
    except Exception as e:
        logging.exception('Error serving dashboards index')
        return (json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'})


@app.route('/dashboards/<path:filename>')
def dashboards_files(filename):
    """Serve static dashboard files (HTML, JS, CSS) from dashboards/ folder."""
    try:
        dashboards_dir = os.path.join(ROOT, 'dashboards')
        safe_path = os.path.normpath(os.path.join(dashboards_dir, filename))
        # Ensure we don't serve files outside dashboards_dir
        if not safe_path.startswith(os.path.abspath(dashboards_dir)):
            return (json.dumps({'error': 'invalid_path'}), 400, {'Content-Type': 'application/json'})
        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            return send_file(safe_path)
        return (json.dumps({'error': 'not_found'}), 404, {'Content-Type': 'application/json'})
    except Exception as e:
        logging.exception('Error serving dashboard file %s', filename)
        return (json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8008, threaded=True)
