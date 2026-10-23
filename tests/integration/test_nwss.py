"""Integration test for the NWSS wastewater ingestor.

First run RECORDS the CDC Socrata response into a cassette.
Subsequent runs REPLAY from the cassette (no network), so CI stays
deterministic and independent of upstream endpoint drift.
To refresh after a genuine upstream change:

    Remove-Item tests/integration/cassettes/test_nwss_ca.yaml
    pytest tests/integration/test_nwss.py
"""
import asyncio
from pathlib import Path

import pytest

from argus.ingestion.wastewater.nwss import NWSSIngestor

CASSETTE_DIR = Path(__file__).parent / "cassettes"
CASSETTE_DIR.mkdir(exist_ok=True)


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",  # record once, then replay
)
def test_nwss_ca_returns_observations():
    obs = asyncio.run(NWSSIngestor().fetch(state="CA"))
    assert len(obs) > 0, "expected at least one weekly observation for CA"
    sample = obs[0]
    assert sample.geo_id == "US-CA"
    assert sample.metric.value == "pathogen_copies_per_ml"
    assert sample.value > 0
    assert sample.source.value == "wastewater"
