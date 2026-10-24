# Data Governance

## Data Classification

| Class | Examples | Handling |
|---|---|---|
| Public | NWSS wastewater (CDC), GDELT events, ERA5 climate | Stored, processed, no restrictions |
| Restricted | DHIS2 demo analytics (in production: national ministry data) | Requires agreement; API access only |
| Sensitive | Individual case records (not ingested by Argus) | Out of scope |

## Argus never stores individual-level records.

All ingestion is aggregated to `(geo_id, metric, timestamp, resolution)` before storage or transmission. The `Observation` Pydantic model enforces this at the type level: there is no field for person identity, no free-form notes, no provenance that could re-identify a case.

## Differential Privacy

Where external integration requires exporting aggregates, we apply Laplace noise (epsilon ≥ 1.0) to counts before release. This is implemented in `argus.federated.dp` (currently a stub).

## Retention

Cassettes in `tests/integration/cassettes/` contain only public data (CDC, GDELT, demo DHIS2). Production deployments should implement per-source retention policies externally.
