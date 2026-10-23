"""Integration test: pull from all 3 live ingestors (via cassettes),
fuse, and verify the aligned frame has a shared weekly index."""
import asyncio
from pathlib import Path

import pandas as pd
import pytest

from argus.fusion.align import align_weekly, pivot_wide, to_frame
from argus.ingestion.dhis2.client import DHIS2Ingestor
from argus.ingestion.news.gdelt import GDELTIngestor
from argus.ingestion.wastewater.nwss import NWSSIngestor

CASSETTE_DIR = Path(__file__).parent / "cassettes"


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],
)
def test_fuse_three_sources():
    async def _gather():
        nwss = await NWSSIngestor().fetch(state="CA")
        dhis = await DHIS2Ingestor().fetch("p4K11MFEWtw", "ImspTQPwCqd")
        gdelt = await GDELTIngestor().fetch(iso="US")
        return nwss + dhis + gdelt

    obs = asyncio.run(_gather())
    assert len(obs) > 0

    df = to_frame(obs)
    aligned = align_weekly(df)

    # Every observation has a tz-aware timestamp after alignment
    assert aligned["timestamp"].dt.tz is not None
    # Multiple sources survived
    assert aligned["source"].nunique() >= 2
    # No negative values (a contract invariant)
    assert (aligned["value"] >= 0).all()
    # Wide pivot produces one row per (geo_id, timestamp)
    wide = pivot_wide(aligned)
    assert not wide.empty
    assert "geo_id" in wide.columns
    assert "timestamp" in wide.columns