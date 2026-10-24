"""Pydantic models for API responses."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ObservationResponse(BaseModel):
    source: str
    metric: str
    geo_id: str
    timestamp: datetime
    value: float
    unit: Optional[str] = None


class BacktestRow(BaseModel):
    timestamp: datetime
    observed: float
    threshold: float
    alert: bool


class BacktestResponse(BaseModel):
    geo_id: str
    metric: str
    results: List[BacktestRow]


class MetricsResponse(BaseModel):
    sensitivity: float
    specificity: float
    false_alarm_rate: float
    lead_time_median_days: Optional[float] = None
    n_onsets: int
    n_alerts: int
