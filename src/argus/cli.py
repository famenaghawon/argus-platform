"""Argus command-line interface."""
from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

import typer
from rich import print

from argus.fusion.align import align_weekly, to_frame
from argus.fusion.quality import drop_duplicates, reject_negatives
from argus.ingestion.climate.era5 import ERA5Ingestor
from argus.ingestion.dhis2.client import DHIS2Ingestor
from argus.ingestion.fhir.bundle import FHIRBundleIngestor
from argus.ingestion.news.gdelt import GDELTIngestor
from argus.ingestion.wastewater.nwss import NWSSIngestor

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def climate(geo: str = "NG", start: str = "2024-01-01", end: str = "2024-01-31"):
    """Fetch ERA5 climate for a bbox and geo id (real Copernicus data)."""
    obs = asyncio.run(ERA5Ingestor().fetch(
        geo_id=geo, start=date.fromisoformat(start), end=date.fromisoformat(end),
    ))
    print(f"[green]Fetched {len(obs)} climate observations[/green]")


@app.command()
def news(iso: str = "NG"):
    """Fetch latest GDELT 15-minute export filtered to a country."""
    obs = asyncio.run(GDELTIngestor().fetch(iso=iso))
    print(f"[green]Fetched {len(obs)} news observations[/green]")


@app.command()
def wastewater(state: str = "GA"):
    """Fetch CDC NWSS wastewater signal."""
    obs = asyncio.run(NWSSIngestor().fetch(state=state))
    print(f"[green]Fetched {len(obs)} wastewater observations[/green]")


@app.command()
def dhis2(data_element: str, org_unit: str):
    """Fetch DHIS2 analytics from play.dhis2.org demo."""
    obs = asyncio.run(DHIS2Ingestor().fetch(data_element, org_unit))
    print(f"[green]Fetched {len(obs)} DHIS2 observations[/green]")


@app.command()
def fhir(bundle: str, condition: str = "59621000"):
    """Parse a Synthea-generated FHIR bundle."""
    obs = asyncio.run(FHIRBundleIngestor().fetch(bundle, condition))
    print(f"[green]Fetched {len(obs)} FHIR observations[/green]")


@app.command()
def pipeline(
    state: str = "CA",
    iso: str = "NG",
    out: str = "data/fused.parquet",
):
    """Run NWSS + GDELT (+ ERA5 if configured), fuse, write parquet."""
    async def _run():
        obs = []
        # NWSS (always works)
        obs += await NWSSIngestor().fetch(state=state)
        # GDELT (always works)
        obs += await GDELTIngestor().fetch(iso=iso)
        # ERA5 (only if ~/.cdsapirc exists)
        try:
            obs += await ERA5Ingestor().fetch(geo_id=iso)
        except Exception as e:
            print(f"[yellow]Skipping ERA5 (configure ~/.cdsapirc to enable): {e}[/yellow]")
        return obs

    observations = asyncio.run(_run())
    if not observations:
        print("[red]No observations returned from any source.[/red]")
        raise typer.Exit(code=1)

    df = to_frame(observations)
    df = reject_negatives(drop_duplicates(df))
    df = align_weekly(df)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"[bold green]Wrote {len(df)} fused rows -> {out}[/bold green]")


if __name__ == "__main__":
    app()
