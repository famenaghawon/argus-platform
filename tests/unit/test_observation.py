"""Unit tests for the Observation schema."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from argus.ingestion.schemas.observation import Metric, Observation, Source


def test_observation_accepts_valid_input():
    o = Observation(
        source=Source.WASTEWATER,
        metric=Metric.PATHOGEN_COPIES,
        geo_id="US-CA",
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        value=1e7,
    )
    assert o.geo_id == "US-CA"
    assert o.value == 1e7


def test_observation_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        Observation(
            source=Source.WASTEWATER,
            metric=Metric.PATHOGEN_COPIES,
            geo_id="US-CA",
            timestamp=datetime(2025, 1, 1),   # no tzinfo
            value=1e7,
        )


def test_observation_serializes_roundtrip():
    original = Observation(
        source=Source.NEWS,
        metric=Metric.EVENT_COUNT,
        geo_id="NG",
        timestamp=datetime(2025, 6, 1, tzinfo=timezone.utc),
        value=42.0,
    )
    reloaded = Observation.model_validate(original.model_dump())
    assert reloaded == original