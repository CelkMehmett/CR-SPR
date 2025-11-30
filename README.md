# CRISPR-FinAI — Minimal demo & README

This repository contains a minimal, static demonstration of the "CRISPR" concept used in the CRISPR-FinAI demo (a simplified subset of the original large demo).

Files of interest
- `crispr-demo.html` — Minimal demo: a single page with a small "Genome Snapshot" modal. Safe to host on GitHub Pages.
- `CRISPR_ARTICLE.md` — Short article describing the concept and comparisons to other models.

How to run locally

1. Serve the repo root with a simple HTTP server (Python 3):

```bash
python3 -m http.server 8001
# then open http://127.0.0.1:8001/crispr-demo.html
```

2. Or open `crispr-demo.html` directly in the browser for a static preview (no server needed for this simple demo).

GitHub Pages (one-time setup)

1. Create a GitHub repo (or use an existing one).
2. Add a remote and push the default branch (main):

```bash
# replace with your repo URL
git remote add origin git@github.com:username/crispr-demo.git
git branch -M main
git push -u origin main
```

3. To publish the minimal demo on GitHub Pages, push the `gh-pages` branch (this repo already contains a local `gh-pages` branch with `index.html` set up):

```bash
# push gh-pages to GitHub (you will be prompted for credentials or SSH keys)
git push -u origin gh-pages
```

Notes
- This demo is intentionally minimal and contains no real trading logic or API keys. It's for demonstration and documentation only.
- If you'd like, I can also prepare a small `LICENSE` file (MIT by default), or split CSS/JS into `assets/` for a cleaner structure.

If you want me to push the changes to a remote repo or open a PR, provide the remote URL and I'll prepare the push commands (I will not push without your approval).

---
# 🧬 CRISPR-FinAI — Bio-Inspired Adaptive Financial Intelligence

> **Think like biology. Code like AI. Optimize like evolution.**

A revolutionary AI system inspired by CRISPR gene-editing principles, designed for **financial modeling and self-repairing algorithms**. The framework can **detect**, **edit**, and **stabilize** model parameters with surgical precision — like CRISPR edits DNA — but applied to financial data and AI model weights.

## 🧠 Core Concept

Each AI module acts like a biological layer in a living system:

- **🔬 Detector Layer** → detects anomalies, data drift, or faulty parameters (analogous to genome sequencing)
- **🧭 Guide Layer** → identifies precise targets for correction, using attention mechanisms (like guide-RNA)
- **✂️ Editor Layer** → performs the actual "gene edit": modifies model weights, trading rules, or optimization hyperparameters (like Cas proteins)
- **🔧 Repair Layer** → ensures model stability post-edit through feedback, regularization, or self-healing mechanisms
- **📚 Audit Layer** → maintains complete edit history with full traceability and rollback capability

## 💹 System Goals

- Apply **CRISPR-like fine-tuning** to live financial models
- Enable **self-healing AI**: the system detects its own performance degradation and corrects itself
- Maintain full **auditability** — each edit must be explainable, logged, and reversible
- Achieve measurable performance gains in backtests (Sharpe ratio, drawdown, hit rate)

## � COMPLETE IMPLEMENTATION STATUS

✅ **PRODUCTION READY** - All core components implemented and integrated:

- ✅ **Core Architecture**: Abstract base classes and interfaces
- ✅ **Financial Genome**: Complete parameter organization system  
- ✅ **Data Pipeline**: Multi-source financial data loading
- ✅ **Detector Layer**: Isolation forest anomaly detection with statistical drift
- ✅ **Guide Layer**: Attention-based parameter targeting system
- ✅ **Editor Layer**: Genetic algorithm parameter optimization
- ✅ **Repair Layer**: Cellular repair with gradient surgery & emergency protocols
- ✅ **Audit Layer**: Cryptographic audit trails with compliance monitoring
- ✅ **Evaluation Framework**: Comprehensive backtesting and benchmarking
- ✅ **CLI Integration**: Complete command-line interface and orchestration
- ✅ **Demo Notebooks**: Full system demonstrations and examples

🚀 **READY FOR DEPLOYMENT**: End-to-end CRISPR-FinAI system with biological precision!

## �🏗️ Architecture

```
🧬 CRISPR-FinAI Framework
├── 🔬 Detector Layer (Genome Sequencing)
│   ├── IsolationDetector - Advanced anomaly detection ✅
│   └── Statistical drift analysis ✅
├── 🧭 Guide Layer (Guide-RNA Targeting)
│   ├── AttentionGuide - Neural parameter targeting ✅
│   └── Rule-based targeting strategies ✅
├── ✂️ Editor Layer (Cas-AI Cutting)
│   ├── GeneticAlgorithmEditor - Evolutionary optimization ✅
│   └── Multi-strategy parameter modification ✅
├── 🔧 Repair Layer (Cellular Repair)
│   ├── Gradient surgery and regularization ✅
│   └── Emergency stabilization protocols ✅
├── 📚 Audit Layer (Genetic Archive)
│   ├── Complete edit history logging ✅
│   └── Rollback and recovery systems ✅
├── 📊 Evaluation Framework
│   ├── Comprehensive backtesting system ✅
│   └── Benchmark comparison and analysis ✅
└── 🧬 Financial Genome
    ├── Parameter organization by "chromosomes" ✅
    └── Gene-level edit tracking and constraints ✅
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd crispr-fin-ai

# Install dependencies
pip install -r requirements.txt

# Optional: Install in development mode
pip install -e .
```

## 📡 Telemetry & Demo

A small proof-of-concept demo server and frontend are included under `poc/presentation_v2/`.

- Run the demo server:

```bash
# from the repository root
python poc/presentation_v2/server.py
```

- The server listens on port 8008 by default. Open the simple frontend at:

    http://localhost:8008/

- Useful demo endpoints (read-only):
    - `/current_parameters` — compact snapshot summary including `telemetry` when available
    - `/telemetry` — returns telemetry JSON for the latest in-memory snapshot
    - `/snapshots` and `/snapshots/<id>` — list and fetch persisted snapshots

- Security: when `DEMO_TOKEN` is set in the environment the server requires that token to access most endpoints. For local development leave `DEMO_TOKEN` unset.

- Enabling MLflow (optional):

    - The demo will attempt to call the editor MLflow helper if the env var `MLFLOW_EXPERIMENT` is set. You can also set `MLFLOW_TRACKING_URI` to point to your MLflow server.

    ```bash
    # Example: enable MLflow logging of demo runs (must have MLflow server available)
    export MLFLOW_TRACKING_URI=http://localhost:5000
    export MLFLOW_EXPERIMENT="crispr-demo"
    python poc/presentation_v2/server.py
    ```

    If MLflow isn't installed or the server is unreachable the demo will continue to function — MLflow calls are defensive and optional.


### Basic Usage

```python
from src.core import FinancialGenome
from src.detector import IsolationDetector
from src.guide import AttentionGuide
from src.editor import GeneticAlgorithmEditor
from src.data import FinancialDataLoader

# 1. Load financial data
loader = FinancialDataLoader()
data = loader.load_market_data(['AAPL', 'GOOGL'], period='2y')
training_data = loader.prepare_training_data(['AAPL', 'GOOGL'])

# 2. Create a financial model genome
genome = FinancialGenome("TradingModel_v1", "trading_strategy")

# Add some example parameters
genome.add_gene("strategy", "momentum_threshold", 0.05, 
               constraints={'min': 0.01, 'max': 0.20})
genome.add_gene("strategy", "stop_loss", 0.02,
               constraints={'min': 0.005, 'max': 0.10})
genome.add_gene("risk", "position_size", 0.10,
               constraints={'min': 0.01, 'max': 0.50})

# 3. Initialize CRISPR components
detector = IsolationDetector(contamination=0.1)
guide = AttentionGuide(max_targets=3)
editor = GeneticAlgorithmEditor()

# 4. Train detector on healthy data
detector.fit(training_data['train'])

# 5. Detect anomalies in new data
detection_result = detector.detect(training_data['val'])

# 6. If anomalies detected, identify targets for editing
if detection_result.is_anomalous:
    targets = guide.identify_targets(detection_result, genome)
    
    # 7. Apply precision edits
    for target in targets:
        edit_result = editor.edit(target, genome)
        print(f"Edit {edit_result.edit_id}: {edit_result.success}")
```

## 📁 Project Structure

```
crispr-fin-ai/
├── src/                           # Core system modules
│   ├── core/                      # Base abstractions and genome
│   │   ├── base_layers.py        # Abstract base classes
│   │   └── genome.py             # Financial genome structure
│   ├── data/                      # Data loading and preprocessing
│   │   └── loader.py             # Financial data sequencer
│   ├── detector/                  # Anomaly detection (genome sequencing)
│   │   └── isolation_detector.py # Isolation forest detector
│   ├── guide/                     # Parameter targeting (guide-RNA)
│   │   └── guide_agent.py        # Attention-based targeting
│   ├── editor/                    # Parameter editing (Cas-AI)
│   │   └── ga_editor.py          # Genetic algorithm editor
│   ├── repair/                    # Stability maintenance
│   ├── audit/                     # Edit history and logging
│   └── eval/                      # Performance evaluation
├── notebooks/                     # Jupyter demonstrations
│   ├── genome_map.ipynb          # Model parameter visualization
│   └── rl_edit_simulation.ipynb  # RL editing experiments
├── poc/                          # Proof of concept scripts
│   └── run_backtest.py          # Main backtesting script
├── data/                         # Data storage
├── logs/                         # System logs
└── tests/                        # Unit tests
```

## 🧬 Biological Analogies

| Biological Component | CRISPR-FinAI Component | Function |
|---------------------|------------------------|----------|
| DNA Sequencing | Isolation Detector | Analyze model "genome" for mutations |
| Guide-RNA | Attention Guide | Target specific parameters for editing |
| PAM Sequence | Parameter Context | Identify valid edit locations |
| Cas9/Cas12 Proteins | Genetic Algorithm Editor | Execute precise parameter cuts/edits |
| DNA Repair Mechanisms | Repair Layer | Stabilize model after modifications |
| Laboratory Notebook | Audit Layer | Track all genetic modifications |
| Genetic Lineage | Edit History | Trace parameter evolution over time |

## 🔬 Advanced Features

### Adaptive Anomaly Detection
- **Isolation Forest**: Detects outliers in high-dimensional parameter space
- **Statistical Drift Detection**: Monitors distribution changes over time
- **Adaptive Thresholds**: Self-adjusting sensitivity based on recent performance

### Neural Parameter Targeting
- **Multi-Head Attention**: Identifies parameter dependencies and relationships
- **Importance Scoring**: Prioritizes critical parameters for editing
- **Off-Target Prevention**: Validates edits to avoid unintended consequences

### Evolutionary Parameter Editing
- **Multiple Mutation Strategies**: Gaussian, uniform, adaptive, polynomial
- **Crossover Techniques**: Arithmetic, uniform, simulated binary crossover
- **Multi-Objective Optimization**: Balance performance, stability, and simplicity

### Self-Healing Mechanisms
- **Gradient Surgery**: Corrects unstable gradients post-edit
- **Emergency Protocols**: Rapid stabilization for critical failures
- **Rollback Systems**: Complete edit reversal with one command

## 📊 Performance Metrics

The system tracks comprehensive performance metrics:

- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Worst peak-to-trough decline
- **Hit Rate**: Percentage of profitable trades/predictions
- **Volatility**: Standard deviation of returns
- **Calmar Ratio**: Annual return / max drawdown
- **Edit Success Rate**: Percentage of beneficial parameter edits
- **Stability Score**: Model robustness after edits

## 🔧 Configuration

The system is highly configurable through multiple layers:

```python
# Detector Configuration
detector_config = {
    'contamination': 0.1,          # Expected anomaly fraction
    'n_estimators': 100,           # Isolation trees
    'sensitivity': 0.95            # Detection threshold
}

# Editor Configuration  
editor_config = EditingConfig(
    population_size=50,            # GA population size
    num_generations=100,           # Evolution iterations
    mutation_rate=0.1,             # Parameter mutation probability
    crossover_rate=0.8            # Parameter crossover probability
)

# Guide Configuration
guide_config = {
    'max_targets': 5,              # Simultaneous edit targets
    'min_confidence': 0.7,         # Minimum targeting confidence
    'attention_heads': 8           # Neural attention heads
}
```

## 🧪 Experimental Features

### Future Enhancements (Roadmap)

1. **Reinforcement Learning Editor**: RL agent that learns optimal editing strategies
2. **Multi-Model Co-Evolution**: Simultaneous optimization of ensemble models
3. **Real-Time Streaming**: Live market data integration and real-time edits
4. **Distributed Computation**: Parallel evolution across multiple nodes
5. **Advanced Repair Mechanisms**: More sophisticated stability techniques

## 📈 Example Use Cases

### 1. Trading Strategy Optimization
```python
# Optimize momentum trading parameters
genome.add_gene("momentum", "lookback_period", 20)
genome.add_gene("momentum", "threshold", 0.02)
genome.add_gene("momentum", "exit_signal", 0.01)

# System automatically detects regime changes and adjusts parameters
```

### 2. Risk Model Calibration
```python
# Auto-calibrate VaR model parameters
genome.add_gene("risk", "confidence_level", 0.95)
genome.add_gene("risk", "holding_period", 1)
genome.add_gene("risk", "decay_factor", 0.94)

# System detects model breakdown and re-calibrates
```

### 3. Portfolio Rebalancing
```python
# Dynamic portfolio weight optimization
for asset in assets:
    genome.add_gene("portfolio", f"{asset}_weight", 0.1)

# System evolves optimal weights based on market conditions
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black src/
```

Makefile
--------

This repository ships a convenient `Makefile` with common developer and operator targets. If you prefer `make` over typing long pip/pytest commands, use the Makefile from the project root.

Common targets:

- `make install-dev` — install development dependencies (developer convenience)
- `make install-ops` — install operator/ops dependencies used by CLI tools (`boto3`, `cryptography`, etc.)
- `make install-ci`  — install a lightweight set of dependencies used inside CI (`requirements-ci.txt`)
- `make test`        — run the test suite (equivalent to `pytest`)
- `make lint`        — run ruff/linters if available

Example

```bash
# install a local dev environment
make install-dev

# run tests
make test
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the revolutionary CRISPR-Cas9 gene editing system
- Built on the shoulders of giants in financial AI and evolutionary computation
- Special thanks to the open-source scientific computing community

## 📞 Contact

For questions, suggestions, or collaboration opportunities:

- **Project Lead**: [Your Name]
- **Email**: [your.email@example.com]
- **GitHub**: [github.com/username/crispr-fin-ai]

---

> *"Just as CRISPR revolutionized genetics by enabling precise DNA editing, CRISPR-FinAI revolutionizes financial AI by enabling precise model editing. We're not just building models — we're evolving them."*

**Think like biology. Code like AI.** 🧬

## 🔐 Advanced: Cross-Account AWS KMS & Assume-Role Setup

To use a KMS-encrypted key for checkpoint encryption/decryption, set the following environment variables:

- `CHECKPOINT_KEY_KMS_CIPHERTEXT`: Base64-encoded AWS KMS ciphertext blob (output of `aws kms encrypt ...`).
- `CHECKPOINT_AWS_ASSUME_ROLE_ARN`: (Optional) ARN of an IAM role to assume before calling KMS (for cross-account decryption).

The system will:
- Assume the specified role using AWS STS (if provided).
- Call KMS.Decrypt to obtain the plaintext key.
- Use the key for AES-GCM encryption/decryption of checkpoint blobs.

### Example: Encrypt a key with AWS KMS

```bash
# Generate a random 32-byte key
openssl rand -hex 32 > key.hex

# Encrypt with KMS (replace <key-id> and <region>)
aws kms encrypt --key-id <key-id> --plaintext fileb://key.hex --output text --query CiphertextBlob --region <region> > key.b64
```

Set the environment variable in your deployment:

```bash
export CHECKPOINT_KEY_KMS_CIPHERTEXT=$(cat key.b64)
# For cross-account, also set:
export CHECKPOINT_AWS_ASSUME_ROLE_ARN=arn:aws:iam::<account-id>:role/<role-name>
```

### Example: Python code to assume role and decrypt

```python
import boto3, base64
role_arn = 'arn:aws:iam::<account-id>:role/<role-name>'
kms_ct = base64.b64decode(open('key.b64', 'rb').read())
sts = boto3.client('sts')
resp = sts.assume_role(RoleArn=role_arn, RoleSessionName='crispr-kms')
creds = resp['Credentials']
session = boto3.Session(
    aws_access_key_id=creds['AccessKeyId'],
    aws_secret_access_key=creds['SecretAccessKey'],
    aws_session_token=creds['SessionToken']
)
kms = session.client('kms')
key = kms.decrypt(CiphertextBlob=kms_ct)['Plaintext']
```

See `core/crypto_utils.py` for implementation details.

## 🔑 Disk cache key retrieval (SSM / KMS)

The on-disk cache (`core.disk_cache.DiskCache`) can obtain its AES-GCM encryption key from several sources. This is useful so you don't have to store plaintext keys in environment variables.

Resolution order (default behavior):

1. explicit constructor `key` argument (bytes)

2. environment variable `DISK_CACHE_KEY` (plaintext)

3. SSM Parameter Store path in `DISK_CACHE_KEY_SSM_PATH` (SecureString, WithDecryption=True)

4. KMS ciphertext (base64) in `DISK_CACHE_KEY_KMS_CIPHERTEXT` (will call KMS.Decrypt)

Optional cross-account / role assumption:

- `DISK_CACHE_KEY_ROLE_ARN` — optional ARN of an IAM role to assume (STS) before calling SSM or KMS. You can also pass `role_arn` to the `DiskCache` constructor.

Environment variables

- `DISK_CACHE_KEY` — plaintext key (not recommended for production)

- `DISK_CACHE_KEY_SSM_PATH` — SSM parameter name (e.g. `/prod/keys/disk-cache`) containing the plaintext key as a SecureString

- `DISK_CACHE_KEY_KMS_CIPHERTEXT` — base64-encoded KMS ciphertext (result of `aws kms encrypt`)

- `DISK_CACHE_KEY_ROLE_ARN` — optional role ARN to assume before calling SSM/KMS

Example: use SSM parameter (recommended)

```bash
export DISK_CACHE_KEY_SSM_PATH=/prod/keys/disk-cache
export DISK_CACHE_KEY_ROLE_ARN=arn:aws:iam::123456789012:role/CrisprDecryptRole

Running integration tests with LocalStack
---------------------------------------

You can run the LocalStack-based integration tests locally to validate SSM/KMS flows without hitting real AWS.

1. Install LocalStack (recommended in a virtualenv):

```bash
python -m pip install --upgrade pip
pip install localstack
```

2. Start LocalStack (detached):

```bash
localstack start -d
```

3. Prepare resources and run the integration test:

```bash
# create a sample SSM parameter and KMS ciphertext used by the test
aws --endpoint-url=http://localhost:4566 ssm put-parameter --name /ci/keys/disk-cache --value "$(openssl rand -hex 32)" --type SecureString --overwrite
KEY_ID=$(aws --endpoint-url=http://localhost:4566 kms create-key --query KeyMetadata.KeyId --output text)
openssl rand -hex 32 > key.bin
aws --endpoint-url=http://localhost:4566 kms encrypt --key-id $KEY_ID --plaintext fileb://key.bin --output text --query CiphertextBlob > key.b64

export RUN_INTEGRATION=1
export DISK_CACHE_KEY_SSM_PATH=/ci/keys/disk-cache
export DISK_CACHE_KEY_KMS_CIPHERTEXT=$(cat key.b64)
PYTHONPATH=. pytest tests/test_integration_localstack.py -q
```

Stop LocalStack when done:

```bash
localstack stop
```
python -c "from core.disk_cache import DiskCache; dc=DiskCache('./.cache')"
```

Example: use KMS ciphertext

```bash
# produce a KMS ciphertext (replace <key-id>)
aws kms encrypt --key-id <key-id> --plaintext fileb://key.bin --output text --query CiphertextBlob > key.b64
export DISK_CACHE_KEY_KMS_CIPHERTEXT=$(cat key.b64)
export DISK_CACHE_KEY_ROLE_ARN=arn:aws:iam::123456789012:role/CrisprDecryptRole
python -c "from core.disk_cache import DiskCache; dc=DiskCache('./.cache')"
```

Notes

- `boto3` (and `botocore`) is required when using SSM or KMS options; DiskCache will raise a clear RuntimeError if boto3 is unavailable.

- The implementation prefers using the repository helper `_assume_role_session` (from `core.kms_utils`) if present, so role-assumption behavior is consistent across modules.

## 🛠️ CLI tools

Two small helper scripts are included in `scripts/` to help with key management and migration:

`scripts/disk_key_tool.py`

- `encrypt-with-kms --key-file key.bin --key-id <kms-key-id>`

    - Reads `key.bin`, encrypts it with KMS, and prints base64 ciphertext. Use this value as `DISK_CACHE_KEY_KMS_CIPHERTEXT`.

    - Optional flags: `--region`, `--role-arn` (assume role before calling KMS).

- `upload-to-ssm --key-file key.bin --param-name /prod/keys/disk-cache`

    - Uploads the key as a SecureString to SSM Parameter Store. Use the SSM path as `DISK_CACHE_KEY_SSM_PATH`.

    - Optional flags: `--region`, `--role-arn`, `--description`.

Examples

```bash
# Encrypt a key with KMS and print base64 ciphertext
python scripts/disk_key_tool.py encrypt-with-kms --key-file key.bin --key-id arn:aws:kms:us-east-1:123:key/abcd

# Upload a key to SSM
python scripts/disk_key_tool.py upload-to-ssm --key-file key.bin --param-name /prod/keys/disk-cache
```

`scripts/rekey_disk_cache.py`

- Re-encrypt all files in a DiskCache directory using a new key. Useful for key rotation or migration when you must change the encryption root.

Basic usage

```bash
# Re-encrypt using explicit key files
python scripts/rekey_disk_cache.py --cache-dir ./.kms_cache --old-key-file old.key --new-key-file new.key

# Re-encrypt using SSM/KMS sources (with assumed role)
python scripts/rekey_disk_cache.py --cache-dir ./.kms_cache --old-ssm /prod/keys/old --new-kms-ct $(cat new_kms_ct.b64) --old-role-arn arn:aws:iam::123:role/A
```

Options

- `--backup-dir` — optional directory to store backups of original files before overwrite. By default a `.bak` file is written next to each entry.

- Keys may be provided via `--*-key-file`, `--*-ssm`, or `--*-kms-ct` mirroring the DiskCache resolution semantics.

Developer & operator convenience

We provide a small `Makefile` with common targets to simplify local setup:

```bash
# install development tools (optional)
make install-dev

# install ops/runtime dependencies
make install-ops

# install minimal CI deps
make install-ci

# run tests
make test

# run lint
make lint
```
