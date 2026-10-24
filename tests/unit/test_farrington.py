"""Unit tests for the Farrington threshold math."""
import numpy as np

from argus.models.baselines.farrington import farrington_threshold


def test_threshold_above_max_on_tight_signal():
    history = np.full(60, 1e7)  # perfectly flat signal
    thresh = farrington_threshold(history)
    assert thresh > 1e7
    assert thresh < 1e8, "on a flat signal, threshold should be close to the mean"


def test_threshold_handles_short_history():
    history = np.array([1.0, 2.0, 3.0])
    thresh = farrington_threshold(history)
    assert thresh > 3.0


def test_threshold_scales_with_noise():
    np.random.seed(0)
    quiet = np.random.uniform(1e7, 1.1e7, 60)
    noisy = np.random.uniform(0.5e7, 2e7, 60)
    thresh_quiet = farrington_threshold(quiet)
    thresh_noisy = farrington_threshold(noisy)
    assert thresh_noisy / 1e7 > thresh_quiet / 1e7, "noisy signal -> wider threshold"


def test_threshold_never_negative():
    history = np.abs(np.random.randn(60)) * 1e6
    thresh = farrington_threshold(history)
    assert thresh > 0