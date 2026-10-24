"""FastAPI application for Argus Platform."""
from __future__ import annotations

import logging
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request

from argus.api.schemas import (
    BacktestResponse,
    BacktestRow,
    MetricsResponse,
    ObservationResponse,
)
from argus.evaluation.backtest import run_farrington_backtest
from argus.evaluation.metrics import compute_metrics
from argus.fusion.align import align_weekly, to_frame
from argus.ingestion.schemas.observation import Metric
from argus.ingestion.wastewater.nwss import NWSSIngestor
from argus.models.hybrid.hybrid_model import HybridDetector

# ---------------------------------------------------------------------------
# 1. Structured logging setup (from screenshot 1)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("argus.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Argus Platform API",
    description="Multi-source public health intelligence system",
    version="0.2.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# 2. Request logging middleware with exception handling (from screenshot 2)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.time() - start) * 1000
        log.exception(
            f"{request.method} {request.url.path} -> 500 ({duration_ms:.0f}ms)"
        )
        raise
    
    duration_ms = (time.time() - start) * 1000
    log.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.0f}ms)"
    )
    return response


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/observations", response_model=list[ObservationResponse])
async def get_observations(
    state: str = Query("CA", description="Two-letter US state code for NWSS"),
):
    try:
        ingestor = NWSSIngestor()
        obs = await ingestor.fetch(state=state)
        return [ObservationResponse(**o.model_dump()) for o in obs]
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/backtest", response_model=BacktestResponse)
async def get_backtest(
    state: str = Query("CA", description="Two-letter US state code"),
    warmup: int = Query(15, description="Weeks required before testing starts"),
    model: str = Query("farrington", description="'farrington' or 'hybrid'"),
):
    # Optional endpoint-specific log (from screenshot 2)
    log.info(f"backtest: state={state} model={model} warmup={warmup}")

    if model not in ("farrington", "hybrid"):
        raise HTTPException(
            status_code=400, detail="model must be 'farrington' or 'hybrid'"
        )

    try:
        ingestor = NWSSIngestor()
        obs = await ingestor.fetch(state=state)
        if not obs:
            raise HTTPException(
                status_code=404, detail="No observations found for state"
            )

        df = align_weekly(to_frame(obs))
        metric = Metric.PATHOGEN_COPIES.value
        geo_id = f"US-{state.upper()}"

        if model == "hybrid":
            # Fit a fresh hybrid model for each test week (rolling origin).
            # Note: this is O(n_train) PyTorch trainings — slow for long series.
            # Optimization (early stopping, smaller net) is a follow-up.
            series_df = (
                df[df["metric"] == metric]
                .sort_values("timestamp")
                .reset_index(drop=True)
            )
            if len(series_df) <= warmup:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Not enough data: {len(series_df)} weeks available, "
                        f"need > warmup={warmup}"
                    ),
                )
            rows = []
            for i in range(warmup, len(series_df)):
                history = series_df["value"].iloc[:i].values
                detector = HybridDetector(epochs=40)
                detector.fit(history)
                thresh = detector.predict_threshold(history, z=1.96)
                obs_val = float(series_df["value"].iloc[i])
                rows.append(
                    BacktestRow(
                        timestamp=series_df["timestamp"].iloc[i],
                        observed=obs_val,
                        threshold=thresh,
                        alert=obs_val > thresh,
                    )
                )
            results_df = None
        else:
            results = run_farrington_backtest(
                df,
                metric_name=metric,
                geo_id=geo_id,
                warmup=warmup,
                z_threshold=1.96,
            )
            rows = [
                BacktestRow(
                    timestamp=r["timestamp"],
                    observed=r["observed"],
                    threshold=r["threshold"],
                    alert=r["alert"],
                )
                for _, r in results.iterrows()
            ]
            results_df = results

        return BacktestResponse(geo_id=geo_id, metric=metric, results=rows)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts", response_model=MetricsResponse)
async def get_alerts_metrics(
    state: str = Query("CA", description="Two-letter US state code"),
    p90_window: int = Query(6, description="Trailing window to define an onset"),
):
    # Optional endpoint-specific log (from screenshot 2)
    log.info(f"alerts: state={state} p90_window={p90_window}")

    try:
        ingestor = NWSSIngestor()
        obs = await ingestor.fetch(state=state)
        df = align_weekly(to_frame(obs))
        metric = Metric.PATHOGEN_COPIES.value
        geo_id = f"US-{state.upper()}"
        results = run_farrington_backtest(
            df, metric_name=metric, geo_id=geo_id, warmup=15, z_threshold=1.96
        )
        metrics = compute_metrics(results, p90_window=p90_window)
        return MetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
