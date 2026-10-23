"""Integration tests for the GDELT news ingestor.

First run RECORDS the GDELT HTTP exchange into a cassette.
Subsequent runs REPLAY from the cassette (no network), so CI stays
deterministic and independent of upstream endpoint drift.
"""
import asyncio
from pathlib import Path

import pytest

from argus.ingestion.news.gdelt import GDELTIngestor

CASSETTE_DIR = Path(__file__).parent / "cassettes"
CASSETTE_DIR.mkdir(exist_ok=True)


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
)
def test_gdelt_ng_returns_observations():
    """Nigerian events in a single 15-minute window are sparse; assert only
    that the pipeline ran end-to-end and produced a valid Observation list."""
    obs = asyncio.run(GDELTIngestor().fetch(iso="NG"))
    assert isinstance(obs, list)
    for o in obs:
        assert o.source.value == "news"
        assert o.geo_id == "NG"


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
)
def test_gdelt_us_returns_observations():
    """US has the highest global event volume, but individual 15-min slices
    can still have irregular composition. Assert contract shape, not count."""
    obs = asyncio.run(GDELTIngestor().fetch(iso="US"))
    assert isinstance(obs, list)
    for o in obs:
        assert o.source.value == "news"
        assert o.geo_id == "US"
        assert o.metric.value in {"event_count", "avg_tone"}
        assert o.value is not None