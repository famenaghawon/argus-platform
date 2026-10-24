"""Rolling-origin backtest engine."""
from __future__ import annotations

import numpy as np
import pandas as pd

from argus.models.baselines.farrington import farrington_threshold


def run_farrington_backtest(
    df: pd.DataFrame,
    metric_name: str,
    geo_id: str,
    warmup: int = 52,
    z_threshold: float = 2.58,
) -> pd.DataFrame:
    """Replay a weekly time series through the Farrington detector.

    The detector fits a quasi-Poisson model, which is designed for count
    data. For continuous-valued signals (e.g. pathogen concentrations in
    the 10^7 range), we fit on the log1p scale and report thresholds
    back-transformed to the original units.
    """
    series = (
        df[(df["geo_id"] == geo_id) & (df["metric"] == metric_name)]
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    series = series.groupby("timestamp")["value"].sum().reset_index()

    out = []
    n = len(series)

    for i in range(warmup, n):
        history_raw = series["value"].iloc[:i].values
        current_raw = float(series["value"].iloc[i])
        current_ts = series["timestamp"].iloc[i]

        # farrington_threshold does its own log1p internally; pass raw data
        thresh_raw = farrington_threshold(history_raw, z_threshold=z_threshold)
        alert = bool(current_raw > thresh_raw)

        out.append(
            {
                "timestamp": current_ts,
                "observed": current_raw,
                "threshold": thresh_raw,
                "alert": alert,
            }
        )

    return pd.DataFrame(out)
