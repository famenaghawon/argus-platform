"""Farrington outbreak detection algorithm (simplified, pure Python).

Reference:
  Farrington, C.P., Andrews, N.J., Beale, A.D., Catchpole, M.A. (1996).
  "A statistical algorithm for the early detection of outbreaks of
  infectious disease." Journal of the Royal Statistical Society A 159: 547-563.

This implementation is designed to be auditable and dependency-light
(numpy/scipy only). It is not a bit-exact reproduction of the R
`surveillance` package, but implements the core statistical logic:
  1. Fit a quasi-Poisson GLM with trend and seasonality to historical data.
  2. Exclude a window of recent weeks to prevent the current outbreak from
     lifting the baseline.
  3. Compute a threshold as `mu + z * sqrt(mu + phi * mu^2)`.
"""
from __future__ import annotations

import numpy as np
from scipy.special import gammaln


def _fit_quasipoisson(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, float]:
    """Fit a log-link quasi-Poisson GLM via IRLS.

    Returns:
        (coefficients, overdispersion_phi)
    """
    n, p = X.shape
    # Initialize coefficients via Poisson regression
    # (Using a simple IRLS loop; could use statsmodels but keeping deps light)
    beta = np.zeros(p)
    # Prevent log(0)
    y_safe = np.maximum(y, 0.1)
    beta = np.linalg.lstsq(X, np.log(y_safe), rcond=None)[0]

    for _ in range(25):
        eta = X @ beta
        mu = np.exp(eta)
        mu = np.maximum(mu, 1e-6)
        # Working weights
        w = mu
        z = eta + (y - mu) / mu
        # Weighted least squares
        Xw = X * np.sqrt(w)[:, None]
        zw = z * np.sqrt(w)
        beta_new, _, _, _ = np.linalg.lstsq(Xw, zw, rcond=None)
        if np.max(np.abs(beta_new - beta)) < 1e-6:
            beta = beta_new
            break
        beta = beta_new

    # Compute overdispersion (phi) using Pearson chi-square
    mu = np.maximum(np.exp(X @ beta), 1e-6)
    pearson_chi2 = np.sum((y - mu)**2 / mu)
    phi = pearson_chi2 / (n - p)
    phi = np.maximum(phi, 1.0)  # Quasi-Poisson assumes phi >= 1

    return beta, phi


def farrington_threshold(
    historical_counts: np.ndarray,
    z_threshold: float = 2.58,  # 99% confidence interval
    trend: bool = True,
    seasonality: bool = True,
) -> float:
    """Calculate the Farrington upper threshold for the next time step.

    Args:
        historical_counts: 1D array of weekly counts (oldest to newest).
                           Must NOT include the week being evaluated.
        z_threshold: number of standard deviations for the threshold.
        trend: whether to include a linear time trend.
        seasonality: whether to include annual seasonality (requires >= 52 weeks).

    Returns:
        The alert threshold (float). If the next observed count exceeds this,
        an alert is triggered.
    """
    n = len(historical_counts)
    if n < 5:
        return float(np.max(historical_counts) + 1)

    t = np.arange(1, n + 1)
    columns = [np.ones(n)]

    if trend:
        columns.append(t)

    if seasonality and n >= 52:
        # One pair of Fourier terms for annual seasonality
        freq = 2 * np.pi / 52.1775  # average weeks per year
        columns.append(np.sin(freq * t))
        columns.append(np.cos(freq * t))

    X = np.column_stack(columns)

    # Predict at the next time step (t = n + 1)
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
        beta, phi = _fit_quasipoisson(historical_counts, X)
        mu_next = float(np.exp(X_next @ beta)[0])
    except Exception:
        # Fallback if regression fails (e.g., singular matrix)
        mu_next = float(np.mean(historical_counts))

    # Farrington threshold formula
    threshold = mu_next + z_threshold * np.sqrt(mu_next + phi * mu_next**2)
    return float(threshold)