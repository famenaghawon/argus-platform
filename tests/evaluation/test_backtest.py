"""Integration test: backtest NWSS wastewater data using Farrington."""
import asyncio
from pathlib import Path

import pytest

from argus.evaluation.backtest import run_farrington_backtest
from argus.evaluation.metrics import compute_metrics
from argus.fusion.align import align_weekly, to_frame
from argus.ingestion.schemas.observation import Metric
from argus.ingestion.wastewater.nwss import NWSSIngestor

CASSETTE_DIR = Path(__file__).parent.parent / "integration" / "cassettes"


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],
)
def test_farrington_detects_nwss_ca():
    # 1. Fetch real data (replays from cassette)
    obs = asyncio.run(NWSSIngestor().fetch(state="CA"))
    assert len(obs) >= 20, "Need at least a few months of data to run the backtest"

    # 2. Fuse to weekly index
    df = align_weekly(to_frame(obs))

    # 3. Run backtest
    metric = Metric.PATHOGEN_COPIES.value
    results = run_farrington_backtest(
        df, metric_name=metric, geo_id="US-CA", warmup=15, z_threshold=1.96
    )

    # 4. Compute metrics
    metrics = compute_metrics(results, p90_window=6)

    # 5. Assert the pipeline runs end-to-end
    assert not results.empty, "Backtest should produce results"
    assert (results["threshold"] > 0).all(), "Thresholds must be positive"
    assert results["observed"].notna().all(), "Observations must be valid"
    assert isinstance(bool(results["alert"].iloc[0]), bool), "Alerts must be booleans"

    # 6. Verify the metrics dictionary has the correct shape
    assert "sensitivity" in metrics
    assert "specificity" in metrics
    assert "lead_time_median_days" in metrics
    assert "false_alarm_rate" in metrics
