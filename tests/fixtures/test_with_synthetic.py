"""Tests using the synthetic fixture series."""
import json
from pathlib import Path

import numpy as np

from argus.models.baselines.farrington import farrington_threshold

FIXTURE = Path(__file__).parent / "synthetic_series.json"


def test_outbreak_spike_breaches_threshold():
    data = json.loads(FIXTURE.read_text())
    weeks = np.array(data["weeks"], dtype=float)

    # Compute threshold using weeks 1-39 (pre-outbreak)
    history = weeks[:39]
    thresh = farrington_threshold(history, z_threshold=1.96)

    # The next 3 weeks spike to 320, 410, 390 -- all should be above threshold
    assert all(weeks[39:42] > thresh), (
        f"spike {weeks[39:42].tolist()} should breach threshold {thresh:.1f}"
    )


def test_quiet_period_does_not_breach():
    data = json.loads(FIXTURE.read_text())
    weeks = np.array(data["weeks"], dtype=float)

    # Use weeks 1-20 as history, test weeks 21-38 (quiet period)
    history = weeks[:20]
    thresh = farrington_threshold(history, z_threshold=1.96)

    quiet = weeks[21:39]
    assert all(quiet < thresh), (
        f"quiet period {quiet.tolist()} should not breach threshold {thresh:.1f}"
    )