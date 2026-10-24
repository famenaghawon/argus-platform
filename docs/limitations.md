# Limitations

## What Argus Is

- A federated, standards-compliant early-warning system
- A research prototype validated against three real public data sources
- An API for downstream dashboards and researchers

## What Argus Is Not

- **A diagnostic tool.** Alerts are statistical signals, not clinical assessments.
- **A replacement for national IHR focal points.** Every alert requires human review.
- **Fully validated.** The Farrington and hybrid detectors are implemented correctly but have not been evaluated against a full multi-year gold-standard dataset.

## Known Constraints

1. **Data availability limits the hybrid model.** NWSS for California only has ~90 weeks of history. Hybrid training is therefore light. With 3+ years, model quality would improve substantially.

2. **No model uncertainty calibration yet.** The `z_threshold` in both detectors is a heuristic; conformal prediction intervals are future work.

3. **The API has no authentication.** In production, every endpoint requires OAuth2 + rate limiting. Currently the demo runs unauthenticated.

4. **Federated learning is a stub.** The `argus.federated` module has interfaces but no working implementation.

5. **No live alerting UI.** The `/alerts` endpoint returns metrics; there is no dashboard, email, SMS, or webhook delivery.
