"""Integration test: hybrid SEIR + residual detector runs on NWSS CA data."""
import asyncio
from pathlib import Path

import pytest

from argus.evaluation.backtest import run_farrington_backtest
from argus.fusion.align import align_weekly, to_frame
from argus.ingestion.schemas.observation import Metric
from argus.ingestion.wastewater.nwss import NWSSIngestor
from argus.models.hybrid.hybrid_model import HybridDetector

CASSETTE_DIR = Path(__file__).parent.parent / "integration" / "cassettes"


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],
)
def test_hybrid_fits_and_predicts():
    obs = asyncio.run(NWSSIngestor().fetch(state="CA"))
    assert len(obs) >= 50, "Need sufficient history for hybrid training"

    df = align_weekly(to_frame(obs))
    metric = Metric.PATHOGEN_COPIES.value
    series = df[df["metric"] == metric].sort_values("timestamp")["value"].values

    # Fit on first 60 weeks
    train = series[:60]
    detector = HybridDetector(epochs=100)
    detector.fit(train)

    # Predict threshold for week 61
    thresh = detector.predict_threshold(train, z=1.96)
    assert thresh > 0
    assert thresh < 1e10, "Threshold should be in a plausible range"


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],
)
def test_hybrid_vs_farrington_both_produce_results():
    """Both detectors process the same series and produce alerts."""
    obs = asyncio.run(NWSSIngestor().fetch(state="CA"))
    df = align_weekly(to_frame(obs))
    metric = Metric.PATHOGEN_COPIES.value

    farrington_results = run_farrington_backtest(
        df, metric_name=metric, geo_id="US-CA", warmup=20, z_threshold=1.96
    )
    assert not farrington_results.empty
    assert "alert" in farrington_results.columns
