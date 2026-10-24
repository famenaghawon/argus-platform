# Test Fixtures

Static, small, deterministic data used by unit tests. Unlike cassettes
(recorded HTTP exchanges), these are hand-crafted.

- `synthetic_series.json` — a small synthetic weekly series with an obvious outbreak spike.
- `expected_thresholds.json` — reference output for `farrington_threshold` on `synthetic_series.json`.

Keeping these as files (not code) makes it easy to regenerate the expected
values if the algorithm changes and diffs are reviewable.