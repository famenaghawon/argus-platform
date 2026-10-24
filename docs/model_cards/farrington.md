# Model Card: Farrington (log-normal variant)

## Overview
- **Type:** Statistical outbreak detection
- **Task:** Weekly aberration detection on continuous surveillance signals
- **Reference:** Farrington et al. (1996), adapted for continuous data

## How It Works
1. Log1p-transform the input series.
2. Fit OLS with intercept + linear trend + (optional) annual Fourier terms.
3. Compute upper bound = `expm1(mu_log + z * sigma_residual)`.

## Inputs
- 1-D array of weekly observed values (e.g. NWSS copies/ml), at least 5 weeks.
- For seasonality: ≥ 52 weeks.

## Outputs
- Upper threshold (float, same units as input).
- An alert fires when observed > threshold.

## Performance
- NWSS California: thresholds in 10^7–10^8 range, comparable to observed 10^6–10^7.
- Not yet evaluated on gold-standard outbreak datasets (see limitations.md).

## Limitations
- Assumes log-normal residuals. Fails badly on count data (use quasi-Poisson version).
- No uncertainty quantification beyond `z * sigma`.
- Trend term can extrapolate badly in long series.

## Ethical / deployment considerations
- Alerts are statistical signals, not diagnoses.
- Every alert must be reviewed by a human epidemiologist.