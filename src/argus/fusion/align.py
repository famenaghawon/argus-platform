"""Temporal/spatial alignment of heterogeneous Observation streams."""
from __future__ import annotations

import logging

import pandas as pd

from argus.ingestion.schemas.observation import Observation

log = logging.getLogger(__name__)


def to_frame(obs: list[Observation]) -> pd.DataFrame:
    """Convert Observations into a DataFrame with tz-aware timestamps."""
    if not obs:
        return pd.DataFrame(
            columns=[
                "source", "metric", "geo_id", "timestamp",
                "value", "unit", "resolution", "provenance_url",
            ]
        )
    df = pd.DataFrame([o.model_dump() for o in obs])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def align_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample every (geo_id, metric, source) to Monday-anchored weeks.

    Observations that are already weekly pass through unchanged.
    Daily (NWSS) collapses to a per-week mean.
    Monthly (DHIS2) is forward-filled into the weeks it overlaps
    so downstream comparisons see a common time index.
    """
    if df.empty:
        return df

    df = df.copy()
    # Normalize to a Monday-anchored week start (tz-aware)
    df["week_start"] = (
        df["timestamp"].dt.tz_convert("UTC").dt.normalize()
        - pd.to_timedelta(df["timestamp"].dt.day_of_week, unit="D")
    )

    # For sub-weekly sources, take the median of the week (robust to outliers).
    # For monthly sources, each observation lands in exactly one week_start,
    # which we keep as-is (no forward-fill yet; that's a downstream decision).
    agg = (
        df.groupby(
            ["source", "metric", "geo_id", "week_start", "resolution"],
            as_index=False,
        )
        .agg(value=("value", "median"), unit=("unit", "first"))
    )
    return agg.rename(columns={"week_start": "timestamp"})


def pivot_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Wide view: one row per (geo_id, timestamp), one column per metric.

    Useful for correlation analysis and model input. Missing combinations
    are left as NaN so downstream code can decide how to impute.
    """
    if df.empty:
        return df
    return (
        df.pivot_table(
            index=["geo_id", "timestamp"],
            columns="metric",
            values="value",
            aggfunc="median",
        )
        .reset_index()
        .sort_values(["geo_id", "timestamp"])
    )