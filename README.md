# Argus Platform

Federated, standards-compliant public health early-warning platform.

## What is real vs. stubbed

| Source | Status | Endpoint |
|---|---|---|
| ERA5 climate | live | Copernicus CDS API (requires `~/.cdsapirc`) |
| GDELT news/events | live | `data.gdeltproject.org/gdeltv2/lastupdate.txt` |
| CDC NWSS wastewater | live | `data.cdc.gov/resource/2ew6-ywp6.csv` |
| DHIS2 | live demo | `https://play.dhis2.org/40.1.0/api` |
| FHIR R4 | live *format* | Synthea-generated bundles |
| SORMAS | interface | REST API defined against fixtures |
| Twitter / X | not integrated | replaced by GDELT |

## Quick start

