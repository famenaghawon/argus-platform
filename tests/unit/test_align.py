"""Unit tests for weekly alignment."""
from datetime import datetime, timezone

import pandas as pd
import pytest

from argus.fusion.align import align_weekly, to_frame
from argus.ingestion.schemas.observation import Metric, Observation, Source


def _obs(ts, val):
    return Observation(
        source=Source.WASTEWATER, metric=Metric.PATHOGEN_COPIES,
        geo_id="US-CA", timestamp=ts, value=val,
    )


def test_to_frame_empty():
    df = to_frame([])
    assert df.empty
    assert "timestamp" in df.columns


def test_align_weekly_preserves_count():
    obs = [
        _obs(datetime(2025, 1, 6, tzinfo=timezone.utc), 1.0),
        _obs(datetime(2025, 1, 13, tzinfo=timezone.utc), 2.0),
    ]
    df = align_weekly(to_frame(obs))
    assert len(df) == 2
    assert df["timestamp"].dt.tz is not None


def test_align_weekly_merges_same_week():
    # Two daily obs in the same week -> one weekly median
    obs = [
        _obs(datetime(2025, 1, 6, tzinfo=timezone.utc), 1.0),
        _obs(datetime(2025, 1, 8, tzinfo=timezone.utc), 3.0),
    ]
    df = align_weekly(to_frame(obs))
    assert len(df) == 1
    assert df["value"].iloc[0] == 2.0