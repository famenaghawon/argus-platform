"""Differential privacy primitives.

Currently provides Laplace noise addition for aggregated counts.

Status: **stub** — a full DP-SGD federated training loop is not yet
implemented. This module provides the basic building block (noise
addition) that future federated code will use.
"""
from __future__ import annotations

import numpy as np


def laplace_noise(scale: float, size: int = 1, seed: int | None = None) -> np.ndarray:
    """Draw Laplace(0, scale) noise.

    Args:
        scale: noise scale = sensitivity / epsilon.
        size: number of samples to draw.
        seed: RNG seed for reproducibility.

    Returns:
        np.ndarray of shape (size,).
    """
    rng = np.random.default_rng(seed)
    return rng.laplace(loc=0.0, scale=scale, size=size)


def add_noise_to_count(
    value: float, epsilon: float = 1.0, sensitivity: float = 1.0, seed: int | None = None
) -> float:
    """Add Laplace noise calibrated to (epsilon, sensitivity) for a count."""
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    scale = sensitivity / epsilon
    return float(value + laplace_noise(scale=scale, size=1, seed=seed)[0])