"""
REST API Server for CRISPR-FinAI
Provides programmatic access to model performance, backtesting, and system health.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import uvicorn
from enum import Enum
from core.rl_service import RLService
from core.rl_checkpoint import list_checkpoints, load_checkpoint
from core.rl_checkpoint import save_checkpoint as save_checkpoint_blob
from core.crypto_utils import decrypt_blob
from fastapi.responses import StreamingResponse
from core.alerts import alert_manager, Alert
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
import tempfile
from core.autolab import AutoLab
from core.cas_ai import CasAICore
from core.drift_detector import DriftDetector
from core.merkle_ledger import MerkleLedger
import os
import binascii
import base64
from fastapi import Response

# RL service singleton
rl_service = RLService()


class RLStartRequest(BaseModel):
    symbols: List[str]
    models: List[str]
    controller_type: str = 'epsilon'
    rounds: int = 100
    light_mode: bool = True
    checkpoint_name: str = 'default'


class RLLoadRequest(BaseModel):
    name: str

# Initialize FastAPI app
app = FastAPI(
    title="CRISPR-FinAI API",
    description="Real-time model performance monitoring and backtesting API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get('/metrics')
def metrics_endpoint():
    """Expose Prometheus metrics if prometheus_client is installed; otherwise return 204."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        # prometheus not installed: return No Content so scrapers skip
        return Response(status_code=204)



@app.on_event('startup')
def register_prometheus_collectors():
    """Register default collectors (Process, Platform) if prometheus_client is installed."""
    try:
        from prometheus_client import core as prom_core
        # Older prometheus_client exposes ProcessCollector via helpers; safest to try multiple options
        try:
            prom_core.REGISTRY.register(prom_core.ProcessCollector())
        except Exception:
            pass
        try:
            prom_core.REGISTRY.register(prom_core.PlatformCollector())
        except Exception:
            pass
    except Exception:
        # prometheus_client not available — nothing to do
        return


# Lifecycle events: hydrate ledger on startup and persist on shutdown
@app.on_event('startup')
def _startup_load_ledger():
    try:
        ledger = autolab.ledger if autolab is not None else ledger_fallback
        ledger.load_sqlite()
    except Exception:
        pass


@app.on_event('shutdown')
def _shutdown_save_ledger():
    try:
        ledger = autolab.ledger if autolab is not None else ledger_fallback
        ledger.save_sqlite()
    except Exception:
        pass

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
API_KEY = "your-secret-api-key-here"  # In production, use environment variables

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API authentication token."""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials


# ============================================================================
# Models (Pydantic Schemas)
# ============================================================================

class ModelStatus(str, Enum):
    """Model operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRIFTING = "drifting"
    HEALING = "healing"


class TimeRange(str, Enum):
    """Time range for metrics."""
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1m"
    QUARTER = "3m"
    YEAR = "1y"
    ALL = "all"


class ModelInfo(BaseModel):
    """Model information schema."""
    symbol: str = Field(..., description="Trading symbol")
    model: str = Field(..., description="Model name")
    status: ModelStatus = Field(..., description="Current status")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    annual_return: float = Field(..., description="Annualized return (%)")
    volatility: float = Field(..., description="Volatility (%)")
    max_drawdown: float = Field(..., description="Maximum drawdown (%)")
    win_rate: float = Field(..., description="Win rate (%)")
    last_updated: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "model": "naive_momentum",
                "status": "active",
                "sharpe_ratio": 1.45,
                "annual_return": 18.5,
                "volatility": 15.2,
                "max_drawdown": -12.3,
                "win_rate": 58.5,
                "last_updated": "2024-01-15T10:30:00"
            }
        }


class PerformanceMetrics(BaseModel):
    """Detailed performance metrics."""
    timestamp: datetime
    symbol: str
    model: str
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    daily_return: float
    cumulative_return: float
    volatility: float
    drawdown: float
    trade_count: int
    win_rate: float
    profit_factor: Optional[float] = None


class SystemHealth(BaseModel):
    """System health status."""
    status: str = Field(..., description="Overall system status")
    total_models: int = Field(..., description="Total active models")
    healthy_models: int = Field(..., description="Healthy models count")
    drifting_models: int = Field(..., description="Drifting models count")
    avg_sharpe: float = Field(..., description="Average Sharpe ratio")
    uptime: float = Field(..., description="System uptime (hours)")
    last_check: datetime = Field(..., description="Last health check")


class BacktestRequest(BaseModel):
    """Backtest request parameters."""
    symbol: str = Field(..., description="Trading symbol")
    model: str = Field(..., description="Model to backtest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(100000.0, description="Initial capital")
    commission: float = Field(0.001, description="Commission rate")
    slippage: float = Field(0.0005, description="Slippage rate")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "model": "naive_momentum",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000.0,
                "commission": 0.001,
                "slippage": 0.0005
            }
        }


class BacktestResult(BaseModel):
    """Backtest results."""
    symbol: str
    model: str
    sharpe_ratio: float
    total_return: float
    annual_return: float
    volatility: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float
    execution_time: float  # seconds


# ============================================================================
# Data Access Layer
# ============================================================================

class DataManager:
    """Manages data access for API endpoints."""

    def __init__(self, data_dir: str = "poc/scale_results_quick"):
        self.data_dir = Path(data_dir)
        self.results_file = self.data_dir / "scale_compare_results.csv"
        self.start_time = datetime.now()

    def load_models(self) -> List[Dict[str, Any]]:
        """Load all models from results."""
        if not self.results_file.exists():
            return []

        df = pd.read_csv(self.results_file)

        models = []
        for _, row in df.iterrows():
            models.append({
                "symbol": row["symbol"],
                "model": row["model"],
                "status": self._get_model_status(row["sharpe"]),
                "sharpe_ratio": float(row["sharpe"]),
                "annual_return": float(row["annual_return"] * 100) if "annual_return" in row else 0.0,
                "volatility": float(row["volatility"] * 100),
                "max_drawdown": float(row["max_drawdown"] * 100) if "max_drawdown" in row else 0.0,
                "win_rate": float(row["win_rate"] * 100),
                "last_updated": datetime.now().isoformat()
            })

        return models

    def _get_model_status(self, sharpe: float) -> str:
        """Determine model status based on Sharpe ratio."""
        if sharpe > 1.0:
            return "active"
        if sharpe > 0.5:
            return "healing"
        if sharpe > 0:
            return "drifting"
        return "inactive"

    def get_model(self, symbol: str, model: str) -> Optional[Dict[str, Any]]:
        """Get specific model information."""
        models = self.load_models()
        for m in models:
            if m["symbol"] == symbol and m["model"] == model:
                return m
        return None

    def get_metrics(self, symbol: Optional[str] = None,
                   model: Optional[str] = None,
                   time_range: TimeRange = TimeRange.DAY,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Get performance metrics with filters."""
        # In production, this would query a time-series database
        # For now, simulate with recent data

        models = self.load_models()

        if symbol:
            models = [m for m in models if m["symbol"] == symbol]
        if model:
            models = [m for m in models if m["model"] == model]

        # Simulate time-series data
        metrics = []
        for m in models[:limit]:
            metrics.append({
                "timestamp": datetime.now().isoformat(),
                "symbol": m["symbol"],
                "model": m["model"],
                "sharpe_ratio": m["sharpe_ratio"],
                "sortino_ratio": m["sharpe_ratio"] * 1.1,  # Approximate
                "calmar_ratio": m["sharpe_ratio"] * 0.8,
                "daily_return": np.random.normal(0.001, 0.02),
                "cumulative_return": m["annual_return"],
                "volatility": m["volatility"],
                "drawdown": m["max_drawdown"],
                "trade_count": np.random.randint(10, 100),
                "win_rate": m["win_rate"],
                "profit_factor": 1.0 + (m["sharpe_ratio"] * 0.2)
            })

        return metrics

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        models = self.load_models()

        healthy = sum(1 for m in models if m["status"] == "active")
        drifting = sum(1 for m in models if m["status"] == "drifting")
        avg_sharpe = np.mean([m["sharpe_ratio"] for m in models]) if models else 0.0

        overall_status = "healthy" if drifting == 0 else "warning" if drifting < 3 else "critical"

        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600

        return {
            "status": overall_status,
            "total_models": len(models),
            "healthy_models": healthy,
            "drifting_models": drifting,
            "avg_sharpe": float(avg_sharpe),
            "uptime": uptime_hours,
            "last_check": datetime.now().isoformat()
        }


# Initialize data manager
data_manager = DataManager()


# Initialize AutoLab singleton (in-memory ledger)
try:
    cas_core = CasAICore()  # defaults are safe for testing
except Exception:
    cas_core = None

autolab = None
if cas_core is not None:
    try:
        autolab = AutoLab(cas_core, drift_detector=DriftDetector(), ledger=MerkleLedger())
    except Exception:
        autolab = None

# Fallback ledger used when AutoLab singleton isn't available (useful for tests)
from core.merkle_ledger import MerkleLedger as _MerkleLedgerFallback
ledger_fallback = _MerkleLedgerFallback()


# Mount public MLflow API (if available)
try:
    from .mlflow_api import router as mlflow_router
    app.include_router(mlflow_router)
except Exception:
    # mlflow_api may fail to import if mlflow missing; keep app functional
    pass


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["General"])
async def root():
    """API root endpoint."""
    return {
        "name": "CRISPR-FinAI API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=SystemHealth, tags=["System"])
async def get_health():
    """
    Get system health status.
    
    Returns overall system health including model counts and performance metrics.
    """
    health = data_manager.get_system_health()
    return SystemHealth(**health)


@app.get("/api/models", response_model=List[ModelInfo], tags=["Models"])
async def get_models(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[ModelStatus] = Query(None, description="Filter by status"),
    min_sharpe: Optional[float] = Query(None, description="Minimum Sharpe ratio"),
    token: str = Depends(verify_token)
):
    """
    Get list of all models with optional filters.
    
    - **symbol**: Filter by trading symbol (e.g., AAPL)
    - **status**: Filter by model status (active, drifting, healing, inactive)
    - **min_sharpe**: Minimum Sharpe ratio threshold
    
    Requires authentication token.
    """
    models = data_manager.load_models()

    # Apply filters
    if symbol:
        models = [m for m in models if m["symbol"] == symbol]
    if status:
        models = [m for m in models if m["status"] == status.value]
    if min_sharpe is not None:
        models = [m for m in models if m["sharpe_ratio"] >= min_sharpe]

    return [ModelInfo(**m) for m in models]


@app.get("/api/models/{symbol}/{model}", response_model=ModelInfo, tags=["Models"])
async def get_model(
    symbol: str,
    model: str,
    token: str = Depends(verify_token)
):
    """
    Get specific model information.
    
    - **symbol**: Trading symbol
    - **model**: Model name
    
    Returns detailed information for the specified model.
    """
    model_info = data_manager.get_model(symbol, model)

    if not model_info:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {symbol}/{model}"
        )

    return ModelInfo(**model_info)


@app.get("/api/metrics", response_model=List[PerformanceMetrics], tags=["Metrics"])
async def get_metrics(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    model: Optional[str] = Query(None, description="Filter by model"),
    time_range: TimeRange = Query(TimeRange.DAY, description="Time range"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    token: str = Depends(verify_token)
):
    """
    Get performance metrics with optional filters.
    
    - **symbol**: Filter by trading symbol
    - **model**: Filter by model name
    - **time_range**: Time range for metrics (1d, 1w, 1m, 3m, 1y, all)
    - **limit**: Maximum number of results (1-1000)
    
    Returns time-series performance data.
    """
    metrics = data_manager.get_metrics(symbol, model, time_range, limit)
    return [PerformanceMetrics(**m) for m in metrics]


@app.post("/api/backtest", response_model=BacktestResult, tags=["Backtesting"])
async def run_backtest(
    request: BacktestRequest,
    token: str = Depends(verify_token)
):
    """
    Run backtest for specified model and parameters.
    
    - **symbol**: Trading symbol
    - **model**: Model to backtest
    - **start_date**: Backtest start date
    - **end_date**: Backtest end date
    - **initial_capital**: Starting capital
    - **commission**: Commission rate
    - **slippage**: Slippage rate
    
    Returns backtest results with performance metrics.
    """
    # In production, this would run actual backtest
    # For now, return simulated results

    start_time = datetime.now()

    # Simulate backtest execution
    model_info = data_manager.get_model(request.symbol, request.model)

    if not model_info:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {request.symbol}/{request.model}"
        )

    # Add some realistic variations
    sharpe = model_info["sharpe_ratio"] + np.random.normal(0, 0.1)
    total_return = np.random.uniform(0.05, 0.25)

    execution_time = (datetime.now() - start_time).total_seconds()

    result = BacktestResult(
        symbol=request.symbol,
        model=request.model,
        sharpe_ratio=sharpe,
        total_return=total_return * 100,
        annual_return=total_return * 100 * (365 / 252),
        volatility=model_info["volatility"],
        max_drawdown=model_info["max_drawdown"],
        win_rate=model_info["win_rate"],
        total_trades=np.random.randint(50, 200),
        profit_factor=1.0 + (sharpe * 0.2),
        execution_time=execution_time
    )

    return result


@app.get("/api/symbols", tags=["Reference"])
async def get_symbols(token: str = Depends(verify_token)):
    """
    Get list of available trading symbols.
    
    Returns all symbols that have active models.
    """
    models = data_manager.load_models()
    symbols = sorted(list(set(m["symbol"] for m in models)))

    return {
        "symbols": symbols,
        "count": len(symbols)
    }


@app.get("/api/model-types", tags=["Reference"])
async def get_model_types(token: str = Depends(verify_token)):
    """
    Get list of available model types.
    
    Returns all model types in the system.
    """
    models = data_manager.load_models()
    model_types = sorted(list(set(m["model"] for m in models)))

    return {
        "models": model_types,
        "count": len(model_types)
    }


# --------------------- RL Service Endpoints ---------------------


@app.post('/api/rl/start', tags=['RL'])
async def api_rl_start(req: RLStartRequest, token: str = Depends(verify_token)):
    try:
        rl_service.start(req.symbols, req.models, controller_type=req.controller_type, rounds=req.rounds, light_mode=req.light_mode, checkpoint_name=req.checkpoint_name)
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/rl/stop', tags=['RL'])
async def api_rl_stop(token: str = Depends(verify_token)):
    try:
        rl_service.stop()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/rl/status', tags=['RL'])
async def api_rl_status(token: str = Depends(verify_token)):
    try:
        return rl_service.status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/rl/checkpoints', tags=['RL'])
async def api_rl_checkpoints(token: str = Depends(verify_token)):
    try:
        return list_checkpoints('./rl_checkpoints.db')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------- AutoLab Control API ---------------------


@app.post('/api/autolab/start', tags=['AutoLab'])
async def api_autolab_start(token: str = Depends(verify_token)):
    """Start the AutoLab background runner."""
    if autolab is None:
        raise HTTPException(status_code=500, detail='AutoLab not available')
    try:
        autolab.run()
        return {"status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/autolab/stop', tags=['AutoLab'])
async def api_autolab_stop(token: str = Depends(verify_token)):
    """Stop the AutoLab background runner."""
    if autolab is None:
        raise HTTPException(status_code=500, detail='AutoLab not available')
    try:
        autolab.stop()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/autolab/step', tags=['AutoLab'])
async def api_autolab_step(token: str = Depends(verify_token)):
    """Run a single AutoLab step synchronously and return the result."""
    if autolab is None:
        raise HTTPException(status_code=500, detail='AutoLab not available')
    try:
        res = autolab.step()
        return {"status": "ok", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/autolab/status', tags=['AutoLab'])
async def api_autolab_status(token: str = Depends(verify_token)):
    """Get AutoLab running status and simple metrics."""
    if autolab is None:
        return {"available": False}
    try:
        return {
            "available": True,
            "running": bool(autolab.running),
            "log_len": len(autolab.log),
            "ledger_root": autolab.ledger_root()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/autolab/root', tags=['AutoLab'])
async def api_autolab_root(token: str = Depends(verify_token)):
    """Return current Merkle ledger root from AutoLab."""
    if autolab is None:
        raise HTTPException(status_code=500, detail='AutoLab not available')
    try:
        return {"root": autolab.ledger_root()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------- Merkle Ledger Persistence ---------------------


@app.post('/api/ledger/save', tags=['Ledger'])
async def api_ledger_save(token: str = Depends(verify_token)):
    """Persist current in-memory ledger to sqlite database."""
    # if AutoLab is not available, use fallback ledger
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        ledger.save_sqlite()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/ledger/load', tags=['Ledger'])
async def api_ledger_load(token: str = Depends(verify_token)):
    """Load ledger from sqlite into memory (replaces current in-memory ledger)."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        ledger.load_sqlite()
        return {"status": "loaded", "count": len(ledger.leaves)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/export', tags=['Ledger'])
async def api_ledger_export(token: str = Depends(verify_token)):
    """Export current ledger as JSON snapshot (returns JSON content)."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        obj = {'leaves': [l.hex() for l in ledger.leaves]}
        return JSONResponse(content=obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LedgerImportRequest(BaseModel):
    leaves_hex: List[str]


@app.post('/api/ledger/import', tags=['Ledger'])
async def api_ledger_import(req: LedgerImportRequest, token: str = Depends(verify_token)):
    """Import a ledger snapshot (list of leaf hex strings) into in-memory ledger."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        ledger.leaves = [bytes.fromhex(h) for h in req.leaves_hex]
        return {"status": "imported", "count": len(ledger.leaves)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/ledger/upload', tags=['Ledger'])
async def api_ledger_upload(file: UploadFile = File(...), token: str = Depends(verify_token)):
    """Upload a JSON snapshot file and import it into the in-memory ledger."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        content = await file.read()
        import json as _json
        obj = _json.loads(content)
        ledger.leaves = [bytes.fromhex(h) for h in obj.get('leaves', [])]
        return {"status": "uploaded", "count": len(ledger.leaves)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/api/ledger/download', tags=['Ledger'])
async def api_ledger_download(token: str = Depends(verify_token)):
    """Download current ledger snapshot as a JSON file attachment."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        import json as _json
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        obj = {'leaves': [l.hex() for l in ledger.leaves]}
        with open(tmp.name, 'w') as f:
            _json.dump(obj, f)
        return FileResponse(path=tmp.name, media_type='application/json', filename='ledger_snapshot.json')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProofVerifyRequest(BaseModel):
    leaf_hex: str
    proof: List[Tuple[str, str]]
    root_hex: str


@app.post('/api/ledger/verify_proof', tags=['Ledger'])
async def api_ledger_verify_proof(req: ProofVerifyRequest, token: str = Depends(verify_token)):
    """Verify an inclusion proof against a provided root."""
    try:
        ok = MerkleLedger.verify_proof(req.leaf_hex, req.proof, req.root_hex)
        return {"valid": bool(ok)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/api/ledger/proof/{index}', tags=['Ledger'])
async def api_ledger_proof(index: int, token: str = Depends(verify_token)):
    """Return inclusion proof for a ledger leaf index."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        proof = ledger.inclusion_proof(index)
        leaf_hex = ledger.leaves[index].hex()
        root = ledger.root()
        return {"index": index, "leaf_hex": leaf_hex, "proof": proof, "root": root}
    except IndexError:
        raise HTTPException(status_code=404, detail='leaf index out of range')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_sign_key() -> bytes:
    """Resolve signing key from LEDGER_SIGN_KEY environment variable.

    Accepts hex string or raw passphrase.
    """
    v = os.environ.get('LEDGER_SIGN_KEY')
    if not v:
        return None
    try:
        # try hex first
        return binascii.unhexlify(v)
    except Exception:
        return v.encode('utf-8')


@app.get('/api/ledger/signed_root', tags=['Ledger'])
async def api_ledger_signed_root(token: str = Depends(verify_token)):
    """Return current ledger root plus HMAC signature (if LEDGER_SIGN_KEY set)."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    root = ledger.root()
    key = _get_sign_key()
    sig = None
    if key and root:
        sig = ledger.sign_root(key)
    return {"root": root, "signature": sig}


class VerifyRootRequest(BaseModel):
    root_hex: str
    signature_hex: str


@app.post('/api/ledger/verify_root', tags=['Ledger'])
async def api_ledger_verify_root(req: VerifyRootRequest, token: str = Depends(verify_token)):
    """Verify a signed root against LEDGER_SIGN_KEY or provided key (future extension)."""
    key = _get_sign_key()
    if not key:
        raise HTTPException(status_code=400, detail='LEDGER_SIGN_KEY not configured')
    ok = MerkleLedger.verify_root_signature(req.root_hex, req.signature_hex, key)
    return {"valid": bool(ok)}


class Ed25519SignRequest(BaseModel):
    private_pem_b64: str  # base64-encoded PEM private key


@app.post('/api/ledger/sign_ed25519', tags=['Ledger'])
async def api_ledger_sign_ed25519(req: Ed25519SignRequest, token: str = Depends(verify_token)):
    """Sign current root using provided Ed25519 private key (base64 PEM). Returns hex signature."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        pem = base64.b64decode(req.private_pem_b64)
        sig = ledger.sign_root_ed25519(pem)
        return {"signature": sig, "root": ledger.root()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class Ed25519VerifyRequest(BaseModel):
    public_pem_b64: str
    signature_hex: str
    root_hex: str


@app.post('/api/ledger/verify_ed25519', tags=['Ledger'])
async def api_ledger_verify_ed25519(req: Ed25519VerifyRequest, token: str = Depends(verify_token)):
    try:
        pub = base64.b64decode(req.public_pem_b64)
        ok = MerkleLedger.verify_root_signature_ed25519(req.root_hex, req.signature_hex, pub)
        return {"valid": bool(ok)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _kms_sign_root(key_id: str = None) -> str:
    """Sign current ledger root using AWS KMS.

    Placeholder implementation: raises HTTPException(501) if boto3 not available or not configured.
    Tests should monkeypatch this function to simulate KMS responses.
    Returns hex signature string on success.
    """
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    root = ledger.root()
    if not root:
        raise HTTPException(status_code=400, detail='no ledger root')

    # resolve config
    key_id = key_id or os.environ.get('LEDGER_KMS_KEY_ID')
    region = os.environ.get('LEDGER_KMS_REGION', 'us-east-1')
    role_arn = os.environ.get('LEDGER_AWS_ASSUME_ROLE_ARN')
    use_mac = os.environ.get('LEDGER_KMS_USE_MAC', 'true').lower() in ('1', 'true', 'yes')

    try:
        from core.kms_utils import kms_generate_mac, kms_sign_digest
        # message to sign is the root bytes
        root_b = bytes.fromhex(root)
        if use_mac:
            if not key_id:
                raise HTTPException(status_code=400, detail='LEDGER_KMS_KEY_ID not configured')
            return kms_generate_mac(key_id, root_b, region=region, role_arn=role_arn)
        # sign using asymmetric key: digest
        import hashlib
        digest = hashlib.sha256(root_b).digest()
        if not key_id:
            raise HTTPException(status_code=400, detail='LEDGER_KMS_KEY_ID not configured')
        return kms_sign_digest(key_id, digest, signing_algorithm=os.environ.get('LEDGER_KMS_SIGN_ALG', 'ECDSA_SHA_256'), region=region, role_arn=role_arn)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _kms_verify_root(root_hex: str, signature_hex: str, key_id: str = None) -> bool:
    """Verify signature via KMS. Uses GenerateMac/VerifyMac for HMAC or Sign/Verify for asymmetric."""
    # resolve config
    key_id = key_id or os.environ.get('LEDGER_KMS_KEY_ID')
    region = os.environ.get('LEDGER_KMS_REGION', 'us-east-1')
    role_arn = os.environ.get('LEDGER_AWS_ASSUME_ROLE_ARN')
    use_mac = os.environ.get('LEDGER_KMS_USE_MAC', 'true').lower() in ('1', 'true', 'yes')
    try:
        from core.kms_utils import kms_verify_mac, kms_verify_signature
        root_b = bytes.fromhex(root_hex)
        if use_mac:
            if not key_id:
                raise HTTPException(status_code=400, detail='LEDGER_KMS_KEY_ID not configured')
            return kms_verify_mac(key_id, root_b, signature_hex, region=region, role_arn=role_arn)
        import hashlib
        digest = hashlib.sha256(root_b).digest()
        if not key_id:
            raise HTTPException(status_code=400, detail='LEDGER_KMS_KEY_ID not configured')
        return kms_verify_signature(key_id, digest, signature_hex, signing_algorithm=os.environ.get('LEDGER_KMS_SIGN_ALG', 'ECDSA_SHA_256'), region=region, role_arn=role_arn)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class KmsSignRequest(BaseModel):
    key_id: Optional[str] = None


@app.post('/api/ledger/sign_kms', tags=['Ledger'])
async def api_ledger_sign_kms(req: KmsSignRequest, token: str = Depends(verify_token)):
    """Sign ledger root with KMS (placeholder).

    Note: by default this returns 501 unless boto3 is available and KMS is configured.
    Tests will monkeypatch `_kms_sign_root` to simulate a response.
    """
    try:
        sig = _kms_sign_root(req.key_id)
        return {"signature": sig, "root": (autolab.ledger if autolab else ledger_fallback).root()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class KmsVerifyRequest(BaseModel):
    root_hex: str
    signature_hex: str
    key_id: Optional[str] = None


@app.post('/api/ledger/verify_kms', tags=['Ledger'])
async def api_ledger_verify_kms(req: KmsVerifyRequest, token: str = Depends(verify_token)):
    try:
        ok = _kms_verify_root(req.root_hex, req.signature_hex, req.key_id)
        return {"valid": bool(ok)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/kms_public_key', tags=['Ledger'])
async def api_ledger_kms_public_key(token: str = Depends(verify_token)):
    """Return PEM public key for configured KMS key id (base64-encoded)."""
    key_id = os.environ.get('LEDGER_KMS_KEY_ID')
    region = os.environ.get('LEDGER_KMS_REGION', 'us-east-1')
    role_arn = os.environ.get('LEDGER_AWS_ASSUME_ROLE_ARN')
    if not key_id:
        raise HTTPException(status_code=400, detail='LEDGER_KMS_KEY_ID not configured')
    try:
        from core.kms_utils import get_cached_public_key
        pem_or_der, alg = get_cached_public_key(key_id, region=region, role_arn=role_arn)
        import base64 as _b64
        return {"public_key_pem_b64": _b64.b64encode(pem_or_der).decode(), "algorithm": alg}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/ledger/snapshot/{name}', tags=['Ledger'])
async def api_ledger_save_snapshot(name: str, token: str = Depends(verify_token)):
    """Save a named snapshot of the current ledger to sqlite."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        ledger.save_snapshot(name)
        return {"status": "saved", "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/snapshots', tags=['Ledger'])
async def api_ledger_list_snapshots(token: str = Depends(verify_token)):
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        snaps = ledger.list_snapshots()
        return {"snapshots": snaps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/ledger/snapshot/load/{name}', tags=['Ledger'])
async def api_ledger_load_snapshot(name: str, token: str = Depends(verify_token)):
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        ledger.load_snapshot(name)
        return {"status": "loaded", "name": name}
    except KeyError:
        raise HTTPException(status_code=404, detail='snapshot not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/ledger/snapshot/{name}', tags=['Ledger'])
async def api_ledger_delete_snapshot(name: str, token: str = Depends(verify_token)):
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        ledger.delete_snapshot(name)
        return {"status": "deleted", "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/snapshot/export/{name}', tags=['Ledger'])
async def api_ledger_export_snapshot(name: str, token: str = Depends(verify_token)):
    """Export a named snapshot as JSON file attachment."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        # load into a temp ledger and export
        tmp = MerkleLedger()
        tmp.load_snapshot(name)
        import json as _json
        import tempfile
        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        with open(tf.name, 'w') as f:
            _json.dump({'leaves': [l.hex() for l in tmp.leaves]}, f)
        return FileResponse(path=tf.name, media_type='application/json', filename=f'{name}_snapshot.json')
    except KeyError:
        raise HTTPException(status_code=404, detail='snapshot not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SignatureRecordRequest(BaseModel):
    key_id: Optional[str] = None
    method: Optional[str] = None
    signature_hex: str
    metadata: Optional[Dict[str, Any]] = None


@app.post('/api/ledger/signature', tags=['Ledger'])
async def api_ledger_record_signature(req: SignatureRecordRequest, token: str = Depends(verify_token)):
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        ledger.save_signature(req.signature_hex, key_id=req.key_id or '', method=req.method or '', metadata=req.metadata or {})
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/signatures', tags=['Ledger'])
async def api_ledger_list_signatures(token: str = Depends(verify_token)):
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        return {"signatures": ledger.list_signatures()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/signature/{sig_id}', tags=['Ledger'])
async def api_ledger_get_signature(sig_id: int, token: str = Depends(verify_token)):
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        return ledger.get_signature(sig_id)
    except KeyError:
        raise HTTPException(status_code=404, detail='signature not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RotateSignatureRequest(BaseModel):
    new_key_id: Optional[str] = None
    method: Optional[str] = None


@app.post('/api/ledger/rotate_signature', tags=['Ledger'])
async def api_ledger_rotate_signature(req: RotateSignatureRequest, token: str = Depends(verify_token)):
    """Rotate signature: sign current root with new key and record it, returning old and new signature info."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        # capture old signatures (latest)
        old = ledger.list_signatures()
        old_top = old[0] if old else None

        # perform sign using KMS helper if key looks like KMS id, otherwise return 400
        key_id = req.new_key_id or os.environ.get('LEDGER_KMS_KEY_ID')
        if not key_id:
            raise HTTPException(status_code=400, detail='no new_key_id provided and LEDGER_KMS_KEY_ID not set')

        # Use KMS sign helper; tests can monkeypatch _kms_sign_root
        sig = _kms_sign_root(key_id)

        # record signature
        ledger.save_signature(sig, key_id=key_id, method=req.method or ('kms' if key_id else 'unknown'), metadata={'rotated_from': old_top['id'] if old_top else None})

        new_top = ledger.list_signatures()[0]
        return {"old": old_top, "new": new_top}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/ledger/snapshot/rotate/{name}', tags=['Ledger'])
async def api_ledger_rotate_snapshot(name: str, req: RotateSignatureRequest, token: str = Depends(verify_token)):
    """Re-sign a named snapshot and record the signature in signature history."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        # load snapshot into temp ledger to compute root
        tmp = MerkleLedger()
        tmp.load_snapshot(name)
        root = tmp.root()
        if not root:
            raise HTTPException(status_code=400, detail='snapshot empty')

        # sign it using KMS helper (tests will monkeypatch)
        key_id = req.new_key_id or os.environ.get('LEDGER_KMS_KEY_ID')
        if not key_id:
            raise HTTPException(status_code=400, detail='no key_id provided')
        sig = _kms_sign_root(key_id)

        # record signature for snapshot: include snapshot name in metadata
        ledger.save_signature(sig, key_id=key_id, method=req.method or 'kms', metadata={'snapshot': name})
        new_top = ledger.list_signatures()[0]
        return {"snapshot": name, "signature": new_top}
    except KeyError:
        raise HTTPException(status_code=404, detail='snapshot not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/snapshot/export_signed/{name}', tags=['Ledger'])
async def api_ledger_export_signed_snapshot(name: str, token: str = Depends(verify_token)):
    """Export a signed snapshot bundle: snapshot JSON, latest signature for that snapshot, and public key info."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        # ensure snapshot exists
        tmp = MerkleLedger()
        tmp.load_snapshot(name)
        snap_obj = {'leaves': [l.hex() for l in tmp.leaves]}

        # find latest signature for this snapshot
        sigs = ledger.list_signatures()
        sig_for_snapshot = None
        for s in sigs:
            if s.get('metadata', {}).get('snapshot') == name:
                sig_for_snapshot = s
                break

        # get public key info (if KMS configured)
        pub_b64 = None
        alg = None
        try:
            key_id = os.environ.get('LEDGER_KMS_KEY_ID')
            if key_id:
                from core.kms_utils import get_cached_public_key
                pem_or_der, alg = get_cached_public_key(key_id, region=os.environ.get('LEDGER_KMS_REGION', 'us-east-1'), role_arn=os.environ.get('LEDGER_AWS_ASSUME_ROLE_ARN'))
                import base64 as _b64
                pub_b64 = _b64.b64encode(pem_or_der).decode()
        except Exception:
            pub_b64 = None

        bundle = {'snapshot': snap_obj, 'signature': sig_for_snapshot, 'public_key_pem_b64': pub_b64, 'algorithm': alg}
        return JSONResponse(content=bundle)
    except KeyError:
        raise HTTPException(status_code=404, detail='snapshot not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/ledger/snapshot/export_signed_file/{name}', tags=['Ledger'])
async def api_ledger_export_signed_snapshot_file(name: str, token: str = Depends(verify_token)):
    """Return the signed snapshot bundle as a downloadable JSON file."""
    ledger = autolab.ledger if autolab is not None else ledger_fallback
    try:
        tmp = MerkleLedger()
        tmp.load_snapshot(name)
        snap_obj = {'leaves': [l.hex() for l in tmp.leaves]}

        sigs = ledger.list_signatures()
        sig_for_snapshot = None
        for s in sigs:
            if s.get('metadata', {}).get('snapshot') == name:
                sig_for_snapshot = s
                break

        pub_b64 = None
        alg = None
        try:
            key_id = os.environ.get('LEDGER_KMS_KEY_ID')
            if key_id:
                from core.kms_utils import get_cached_public_key
                pem_or_der, alg = get_cached_public_key(key_id, region=os.environ.get('LEDGER_KMS_REGION', 'us-east-1'), role_arn=os.environ.get('LEDGER_AWS_ASSUME_ROLE_ARN'))
                import base64 as _b64
                import tempfile as _tf
                import json as _json
                pub_b64 = _b64.b64encode(pem_or_der).decode()

        except Exception:
            pub_b64 = None

        bundle = {'snapshot': snap_obj, 'signature': sig_for_snapshot, 'public_key_pem_b64': pub_b64, 'algorithm': alg}
        import json as _json
        import tempfile as _tf
        tf = _tf.NamedTemporaryFile(delete=False, suffix='.json')
        with open(tf.name, 'w') as f:
            _json.dump(bundle, f)
        return FileResponse(path=tf.name, media_type='application/json', filename=f'{name}_signed_bundle.json')
    except KeyError:
        raise HTTPException(status_code=404, detail='snapshot not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/rl/load_checkpoint', tags=['RL'])
async def api_rl_load_checkpoint(req: RLLoadRequest, token: str = Depends(verify_token)):
    try:
        blob = load_checkpoint('./rl_checkpoints.db', req.name)
        if blob is None:
            raise HTTPException(status_code=404, detail='checkpoint not found')
        # load into current service pipeline if exists
        import pickle
        state = pickle.loads(blob)
        if rl_service.pipeline:
            # recreate controller of saved type if needed
            ctype = state.get('controller_type')
            params = state.get('controller_params', {})
            arms = state.get('arms', rl_service.pipeline.arms)
            if ctype and type(rl_service.pipeline.controller).__name__ != ctype:
                if ctype == 'EpsilonGreedyController':
                    from core.rl_controller import EpsilonGreedyController
                    rl_service.pipeline.controller = EpsilonGreedyController(arms, epsilon=params.get('epsilon', 0.1))
                elif ctype == 'UCB1Controller':
                    from core.rl_controller import UCB1Controller
                    rl_service.pipeline.controller = UCB1Controller(arms, c=params.get('c', 2.0))
                elif ctype == 'SoftmaxController':
                    from core.rl_controller import SoftmaxController
                    rl_service.pipeline.controller = SoftmaxController(arms, tau=params.get('tau', 0.5))
            # set arms if provided
            rl_service.pipeline.arms = arms
            # set counts/values
            for a, c in state.get('counts', {}).items():
                if a in rl_service.pipeline.controller.counts:
                    rl_service.pipeline.controller.counts[a] = c
            for a, v in state.get('values', {}).items():
                if a in rl_service.pipeline.controller.values:
                    rl_service.pipeline.controller.values[a] = v

        return {"status": "loaded"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/rl/export_checkpoint/{name}', tags=['RL'])
async def api_rl_export_checkpoint(name: str, token: str = Depends(verify_token)):
    """Return raw checkpoint blob for a given name."""
    try:
        blob = load_checkpoint('./rl_checkpoints.db', name)
        if blob is None:
            raise HTTPException(status_code=404, detail='checkpoint not found')
        return JSONResponse(content={"name": name, "blob": blob.hex()})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CheckpointUploadRequest(BaseModel):
    name: str
    blob_hex: str


@app.post('/api/rl/import_checkpoint', tags=['RL'])
async def api_rl_import_checkpoint(req: CheckpointUploadRequest, token: str = Depends(verify_token)):
    """Import a checkpoint blob (hex-encoded) into the DB under provided name."""
    try:
        blob = bytes.fromhex(req.blob_hex)
        save_checkpoint_blob('./rl_checkpoints.db', req.name, blob)
        return {"status": "imported", "name": req.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/rl/download_checkpoint/{name}', tags=['RL'])
async def api_rl_download_checkpoint(name: str, token: str = Depends(verify_token)):
    """Download raw checkpoint blob as an attachment. If CHECKPOINT_ENC_KEY present, blob will be decrypted before streaming."""
    try:
        blob = load_checkpoint('./rl_checkpoints.db', name)
        if blob is None:
            raise HTTPException(status_code=404, detail='checkpoint not found')
        # attempt decrypt if key present
        try:
            import os
            if os.environ.get('CHECKPOINT_ENC_KEY') or os.environ.get('CHECKPOINT_KEY_SSM_PATH'):
                blob = decrypt_blob(blob)
        except Exception:
            # if decrypt fails, return raw blob
            pass

        def iter_bytes(b: bytes):
            yield b

        headers = {"Content-Disposition": f'attachment; filename="{name}.ckpt"'}
        return StreamingResponse(iter_bytes(blob), media_type='application/octet-stream', headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------- Alerts API ---------------------


class AlertCreateRequest(BaseModel):
    name: str
    condition: str
    channels: Optional[List[str]] = None


@app.post('/api/alerts', tags=['Alerts'])
async def create_alert(req: AlertCreateRequest, token: str = Depends(verify_token)):
    a = Alert(req.name, req.condition, channels=req.channels)
    alert_manager.register(a)
    return {"status": "created", "alert": a.to_dict()}


@app.get('/api/alerts', tags=['Alerts'])
async def list_alerts(token: str = Depends(verify_token)):
    return alert_manager.list()


@app.delete('/api/alerts/{name}', tags=['Alerts'])
async def delete_alert(name: str, token: str = Depends(verify_token)):
    alert_manager.remove(name)
    return {"status": "deleted", "name": name}


@app.post('/api/alerts/evaluate', tags=['Alerts'])
async def evaluate_alerts(payload: Dict[str, Any], token: str = Depends(verify_token)):
    hits = alert_manager.evaluate(payload.get('metrics', {}))
    return {"hits": hits}


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# Server Startup
# ============================================================================

def main():
    """Start API server."""
    print("\n" + "="*60)
    print("🚀 Starting CRISPR-FinAI API Server")
    print("="*60)
    print("\n📍 Server: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("🔐 Authentication: Bearer token required")
    print(f"\n{'='*60}\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
