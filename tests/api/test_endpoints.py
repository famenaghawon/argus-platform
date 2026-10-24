"""API tests using the TestClient and VCR cassettes."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from argus.api.main import app

CASSETTE_DIR = Path(__file__).parent.parent / "integration" / "cassettes"
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],
)
def test_observations_endpoint():
    response = client.get("/observations?state=CA")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["geo_id"] == "US-CA"
    assert data[0]["source"] == "wastewater"


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],
)
def test_backtest_endpoint():
    response = client.get("/backtest?state=CA&warmup=15")
    assert response.status_code == 200
    data = response.json()
    assert data["geo_id"] == "US-CA"
    assert len(data["results"]) > 0
    assert "threshold" in data["results"][0]
    assert "alert" in data["results"][0]


@pytest.mark.vcr(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    match_on=["method", "scheme", "host", "path"],
)
def test_metrics_endpoint():
    response = client.get("/alerts?state=CA&p90_window=6")
    assert response.status_code == 200
    data = response.json()
    assert "sensitivity" in data
    assert "specificity" in data
    assert "false_alarm_rate" in data
