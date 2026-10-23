"""Data-quality gates applied before fusion."""
from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    keys = ["source", "metric", "geo_id", "timestamp"]
    before = len(df)
    out = df.drop_duplicates(subset=keys, keep="last")
    if len(out) < before:
        log.warning("Dropped %d duplicate observations", before - len(out))
    return out


def reject_negatives(df: pd.DataFrame) -> pd.DataFrame:
    """Counts and concentrations must be >= 0."""
    out = df[df["value"] >= 0]
    if len(out) < len(df):
        log.warning("Dropped %d negative observations", len(df) - len(out))
    return out


def report_missingness(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return (
        df.assign(missing=df["value"].isna())
          .groupby(["source", "metric"])["missing"]
          .mean()
          .reset_index()
          .rename(columns={"missing": "missing_rate"})
    )
