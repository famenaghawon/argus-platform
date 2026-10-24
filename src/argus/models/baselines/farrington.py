"""Farrington-style outbreak detection (log-normal variant).

For continuous-valued signals (concentrations, ratios, etc.) we fit on the
log1p scale and use a normal approximation with residual standard deviation
as the dispersion term. This is the "log-normal Farrington" used in
practice for water/wastewater surveillance; the classic quasi-Poisson
version is for integer count data and does not transfer cleanly.

Reference: Farrington et al. (1996), JRSS-A 159:547-563, adapted for
continuous signals as recommended in ECDC's "Algorithm for the detection
of outbreaks" technical report.
"""
from __future__ import annotations

import numpy as np


def _fit_log_linear(
    y_log: np.ndarray, X: np.ndarray
) -> tuple[np.ndarray, float]:
    """Fit ordinary least squares on log scale. Return (beta, residual_std)."""
    beta, residuals, _, _ = np.linalg.lstsq(X, y_log, rcond=None)
    y_hat = X @ beta
    resid = y_log - y_hat
    std = float(np.std(resid, ddof=max(1, X.shape[1]))) + 1e-6
    return beta, std


def farrington_threshold(
    historical_counts: np.ndarray,
    z_threshold: float = 2.58,
    trend: bool = True,
    seasonality: bool = True,
) -> float:
    """Calculate the upper threshold for the next time step.

    Args:
        historical_counts: 1D array of *weekly observed values* on the original
            scale (e.g. concentration in copies/ml). The function log1p-transforms
            internally.
        z_threshold: number of standard deviations for the upper bound.
        trend: whether to include a linear time trend.
        seasonality: whether to include annual seasonality (requires >= 52 weeks).

    Returns:
        Threshold on the ORIGINAL scale (same units as historical_counts).
    """
    historical_counts = np.asarray(historical_counts, dtype=float)
    n = len(historical_counts)
    if n < 5:
        return float(np.max(historical_counts, initial=0) + 1)

    # Log transform — this is where the algorithm actually operates
    y_log = np.log1p(np.maximum(historical_counts, 0))

    t = np.arange(1, n + 1)
    columns = [np.ones(n)]
    if trend:
        columns.append(t)
    if seasonality and n >= 52:
        freq = 2 * np.pi / 52.1775
        columns.append(np.sin(freq * t))
        columns.append(np.cos(freq * t))

    X = np.column_stack(columns)

    t_next = np.array([n + 1])
    next_cols = [np.ones(1)]
    if trend:
        next_cols.append(t_next)
    if seasonality and n >= 52:
        freq = 2 * np.pi / 52.1775
        next_cols.append(np.sin(freq * t_next))
        next_cols.append(np.cos(freq * t_next))
    X_next = np.column_stack(next_cols)

    try:
        beta, sigma = _fit_log_linear(y_log, X)
        mu_log_next = float(X_next @ beta)[0]
    except Exception:
        # Fallback: use mean and std of the log history
        mu_log_next = float(np.mean(y_log))
        sigma = float(np.std(y_log)) + 1e-6

    # Upper bound on log scale
    upper_log = mu_log_next + z_threshold * sigma

    # Back-transform to original scale
    return float(np.expm1(upper_log))
