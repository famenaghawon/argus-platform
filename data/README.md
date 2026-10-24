# Data

Runtime data (parquet caches, cassette-derived DataFrames) goes here.

**Nothing in this folder is committed to git** — see `.gitignore`:
- `data/cache/` — ERA5 NetCDF cache
- `data/*.parquet` — pipeline output (regenerate with `argus pipeline`)

The folder exists in git (via `.gitkeep`) so downstream code that writes
here (`argus pipeline`, ERA5 cache) doesn't fail on first run.

## Regenerating data

    argus pipeline --state CA --iso NG
    # → data/fused.parquet

## Test fixtures

Integration tests use VCR cassettes (see `tests/integration/cassettes/`),
not raw data files.