# Interoperability

## Sources Ingested

| Source | Protocol | Auth |
|---|---|---|
| DHIS2 | Web API (JSON) | HTTP Basic (demo) / OAuth2 (production) |
| FHIR R4 | Bundle JSON | N/A (file-based) |
| NWSS | Socrata CSV | Public |
| GDELT | HTTP + zip TSV | Public |
| ERA5 | Copernicus CDS API | API key in `~/.cdsapirc` |

## Standards Followed

- **DHIS2 Analytics**: uses `analytics.json` with `dimension=dx:...&dimension=ou:...&dimension=pe:...`, the standard API for both DHIS2 2.x and 40.x.
- **FHIR R4**: `Condition` resources parsed into `Observation` objects via SNOMED code filter.
- **Observations contract**: all ingestor output conforms to `argus.ingestion.schemas.observation.Observation`, ensuring downstream code can treat any source uniformly.

## Not Yet Implemented

- FHIR **output** (`DetectedIssue` for alerts)
- DHIS2 **write-back** (posting alerts as DHIS2 `Event`s)
- OAuth2 / OIDC on the API (currently unauthenticated)
