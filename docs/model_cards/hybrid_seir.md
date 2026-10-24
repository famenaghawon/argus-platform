# Model Card: Hybrid SEIR + Residual Neural Net

## Overview
- **Type:** Hybrid mechanistic + neural
- **Task:** Weekly forecast / threshold computation
- **Architecture:** SEIR (deterministic ODE) + small MLP residual

## How It Works
1. Run a deterministic SEIR simulation for `n_weeks`.
2. Take the log1p of both SEIR output and observed series.
3. Train a small MLP (2 hidden layers, 32 units) to predict the
   residual between SEIR prediction and actual observation.
4. Next-week threshold = `expm1(SEIR_log_next + residual_pred + z * residual_std)`.

## Inputs
- 1-D array of weekly observations, at least 60 weeks for stable training.

## Outputs
- Upper threshold (float, same units as input).

## Performance
- NWSS California: thresholds in 10^8 range, within 30% of Farrington thresholds.
- Trains in ~0.5s on CPU for 40 epochs (small net).

## Limitations
- SEIR parameters (beta/sigma/gamma) are fixed defaults, not fitted.
  A more sophisticated model would learn these alongside the residual.
- Residual net sees only 4 features (SEIR prediction, previous observation,
  weekly sin/cos). Adding climate covariates would improve accuracy.
- Trains a fresh model for each backtest week (rolling origin) — expensive.
  Production deployment should cache or use walk-forward retraining.

## Ethical / deployment considerations
- Same as Farrington: alerts require human review.
- The residual net can overfit on short series (< 60 weeks). Do not train
  on less than 60 weeks without strong regularization.