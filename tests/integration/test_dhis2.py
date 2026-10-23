import asyncio
from pathlib import Path

import pytest

from argus.ingestion.dhis2.client import DHIS2Ingestor

CASSETTE_DIR = Path(__file__).parent / "cassettes"
CASSETTE_DIR.mkdir(exist_ok=True)


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],   # ignore query-string drift
)
def test_dhis2_malaria_returns_observations():
    obs = asyncio.run(DHIS2Ingestor().fetch("p4K11MFEWtw", "ImspTQPwCqd"))
    assert len(obs) > 0
    sample = obs[0]
    assert sample.source.value == "dhis2"
    assert sample.value >= 0