"""
Public MLflow API router for leaderboard and best-model queries.
Provides lightweight, unauthenticated endpoints under /public/mlflow/* for dashboards
and visualizations that don't expose write access.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

router = APIRouter()


def _safe_float(v):
    try:
        return float(v)
    except Exception:
        return None


@router.get("/public/mlflow/leaderboard", tags=["MLflow Public"])
async def public_mlflow_leaderboard(metric: str = Query("sharpe_ratio", description="Metric to rank by"),
                                   top_n: int = Query(10, ge=1, le=200, description="Number of top results")):
    """Return a simple leaderboard (top N) across all MLflow experiments.
    This endpoint is intentionally read-only and unauthenticated so dashboards can call it.
    """
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"mlflow not available: {exc}")

    client = MlflowClient()

    rows: List[Dict[str, Any]] = []
    try:
        # Prefer listing experiments via client if available
        if hasattr(client, 'list_experiments'):
            experiments = client.list_experiments()
            for exp in experiments:
                # fetch up to 1000 runs per experiment (adjust if needed)
                runs = client.search_runs([exp.experiment_id], filter_string="", max_results=1000)
                for r in runs:
                    tags = r.data.tags or {}
                    params = r.data.params or {}
                    metrics = r.data.metrics or {}

                    symbol = tags.get("symbol") or params.get("symbol") or tags.get("tags.symbol")
                    model = tags.get("model") or params.get("model") or tags.get("tags.model")

                    value = metrics.get(metric) or metrics.get(metric.lower())
                    sharpe = metrics.get("sharpe_ratio") or metrics.get("sharpe")
                    total_return = metrics.get("total_return") or metrics.get("return")

                    rows.append({
                        "experiment": exp.name,
                        "run_id": r.info.run_id,
                        "symbol": symbol,
                        "model": model,
                        "metric": _safe_float(value),
                        "sharpe": _safe_float(sharpe),
                        "total_return": _safe_float(total_return),
                        "start_time": r.info.start_time
                    })
        else:
            # Fallback: use mlflow.search_runs to get run ids, then fetch each run via client
            df = mlflow.search_runs(experiment_ids=None, filter_string="", max_results=1000)
            for run_id in df['run_id'].tolist():
                r = client.get_run(run_id)
                exp = client.get_experiment(r.info.experiment_id)
                tags = r.data.tags or {}
                params = r.data.params or {}
                metrics = r.data.metrics or {}

                symbol = tags.get("symbol") or params.get("symbol") or tags.get("tags.symbol")
                model = tags.get("model") or params.get("model") or tags.get("tags.model")

                value = metrics.get(metric) or metrics.get(metric.lower())
                sharpe = metrics.get("sharpe_ratio") or metrics.get("sharpe")
                total_return = metrics.get("total_return") or metrics.get("return")

                rows.append({
                    "experiment": exp.name if exp is not None else None,
                    "run_id": r.info.run_id,
                    "symbol": symbol,
                    "model": model,
                    "metric": _safe_float(value),
                    "sharpe": _safe_float(sharpe),
                    "total_return": _safe_float(total_return),
                    "start_time": r.info.start_time
                })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"error querying mlflow: {exc}")

    # filter out rows without a metric value
    filtered = [r for r in rows if r.get("metric") is not None]
    # sort descending by metric
    sorted_rows = sorted(filtered, key=lambda x: x["metric"], reverse=True)

    return {"metric": metric, "top_n": top_n, "results": sorted_rows[:top_n]}


@router.get("/public/mlflow/best_models", tags=["MLflow Public"])
async def public_mlflow_best_models(metric: str = Query("sharpe_ratio", description="Metric to rank by")):
    """Return best model per symbol across MLflow experiments.
    Groups by symbolic tag (symbol) and returns the top model for each.
    """
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"mlflow not available: {exc}")

    client = MlflowClient()

    by_symbol = {}
    try:
        if hasattr(client, 'list_experiments'):
            experiments = client.list_experiments()
            for exp in experiments:
                runs = client.search_runs([exp.experiment_id], filter_string="", max_results=1000)
                for r in runs:
                    tags = r.data.tags or {}
                    params = r.data.params or {}
                    metrics = r.data.metrics or {}

                    symbol = tags.get("symbol") or params.get("symbol")
                    model = tags.get("model") or params.get("model")
                    value = metrics.get(metric) or metrics.get(metric.lower())
                    if symbol is None:
                        continue
                    try:
                        val = float(value) if value is not None else None
                    except Exception:
                        val = None

                    if val is None:
                        continue

                    existing = by_symbol.get(symbol)
                    if not existing or val > existing["metric"]:
                        by_symbol[symbol] = {
                            "symbol": symbol,
                            "model": model,
                            "metric": val,
                            "run_id": r.info.run_id,
                            "experiment": exp.name
                        }
        else:
            df = mlflow.search_runs(experiment_ids=None, filter_string="", max_results=1000)
            for run_id in df['run_id'].tolist():
                r = client.get_run(run_id)
                exp = client.get_experiment(r.info.experiment_id)
                tags = r.data.tags or {}
                params = r.data.params or {}
                metrics = r.data.metrics or {}

                symbol = tags.get("symbol") or params.get("symbol")
                model = tags.get("model") or params.get("model")
                value = metrics.get(metric) or metrics.get(metric.lower())
                if symbol is None:
                    continue
                try:
                    val = float(value) if value is not None else None
                except Exception:
                    val = None

                if val is None:
                    continue

                existing = by_symbol.get(symbol)
                if not existing or val > existing["metric"]:
                    by_symbol[symbol] = {
                        "symbol": symbol,
                        "model": model,
                        "metric": val,
                        "run_id": r.info.run_id,
                        "experiment": exp.name if exp is not None else None
                    }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"error querying mlflow: {exc}")

    # return as list
    results = list(by_symbol.values())
    # sort by metric desc
    results.sort(key=lambda x: x["metric"], reverse=True)

    return {"metric": metric, "results": results}
