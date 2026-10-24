"""FastAPI application for Argus Platform."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup tasks if needed (e.g., warming caches)
    yield
    # Teardown tasks


app = FastAPI(
    title="Argus Platform API",
    description="Multi-source public health intelligence system",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Basic liveness check."""
    return {"status": "ok"}


@app.get("/observations", response_model=list[ObservationResponse])
async def get_observations(
    state: str = Query("CA", description="Two-letter US state code for NWSS"),
):
    """Fetch and normalize live wastewater observations."""
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
):
    """Run a rolling-origin backtest using the Farrington algorithm."""
    try:
        ingestor = NWSSIngestor()
        obs = await ingestor.fetch(state=state)
        
        if not obs:
            raise HTTPException(status_code=404, detail="No observations found for state")

        df = align_weekly(to_frame(obs))
        metric = Metric.PATHOGEN_COPIES.value
        geo_id = f"US-{state.upper()}"
        
        results = run_farrington_backtest(
            df, metric_name=metric, geo_id=geo_id, warmup=warmup, z_threshold=1.96
        )
        
        rows = [
            BacktestRow(
                timestamp=row["timestamp"],
                observed=row["observed"],
                threshold=row["threshold"],
                alert=row["alert"],
            )
            for _, row in results.iterrows()
        ]
        
        return BacktestResponse(
            geo_id=geo_id,
            metric=metric,
            results=rows,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts", response_model=MetricsResponse)
async def get_alerts_metrics(
    state: str = Query("CA", description="Two-letter US state code"),
    p90_window: int = Query(6, description="Trailing window to define an onset"),
):
    """Evaluate the performance of the Farrington detector on recent data."""
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
