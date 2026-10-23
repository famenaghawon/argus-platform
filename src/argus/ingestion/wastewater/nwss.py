"""CDC National Wastewater Surveillance System - public CSV via Socrata."""
from __future__ import annotations

import io
from datetime import timezone

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from argus.ingestion.schemas.observation import Ingestor, Metric, Observation, Source
from argus.ingestion._http import client as http_client

# Resource IDs verified via Socrata catalog:
#   2ew6-ywp6  NWSS Public SARS-CoV-2 Wastewater Metric Data
#   j9g8-acpt  CDC Wastewater Data for SARS-CoV-2
NWSS_RESOURCE = "g653-rqe2"
NWSS_URL = (
    "https://data.cdc.gov/resource/" + NWSS_RESOURCE + ".csv"
    "?$limit=50000"
    "&$order=date+DESC"
)


class NWSSIngestor(Ingestor):
    source = Source.WASTEWATER

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _get(self) -> str:
        async with http_client(timeout=60) as c:
            r = await c.get(NWSS_URL, headers={"Accept": "text/csv"})
            r.raise_for_status()
            return r.text

    async def fetch(self, state: str = "GA", pathogen: str = "sars-cov-2") -> list[Observation]:
        csv = await self._get()
        df = pd.read_csv(io.StringIO(csv))

        state_col = next(
            (c for c in ("state", "state_territory") if c in df.columns), None
        )
        date_col = next(
            (c for c in ("date", "sample_collect_date") if c in df.columns), None
        )

        # g653-rqe2 has no 'state' column; extract from key_plot_id like
        # "CDC_VERILY_md_2952_..."  ->  "md"
        if state_col is None and "key_plot_id" in df.columns:
            df["_derived_state"] = (
                df["key_plot_id"].astype(str).str.extract(r"_([a-z]{2})_\d", expand=False)
            )
            state_col = "_derived_state"
        conc_col = next(
            (c for c in ("pcr_conc_lin",
                         "pcr_target_avg_conc_lin",
                         "sars_cov_2_conc_lin",
                         "pcr_target_avg_conc") if c in df.columns),
            None,
        )
        if not (state_col and date_col and conc_col):
            return []

        df = df[df[state_col].astype(str).str.upper() == state.upper()]
        df["ts"] = pd.to_datetime(df[date_col], utc=True, errors="coerce")
        df = df.dropna(subset=["ts"])
        if df.empty:
            return []

        df["week"] = (
    df["ts"].dt.tz_convert("UTC").dt.normalize()
    - pd.to_timedelta(df["ts"].dt.day_of_week, unit="D")
)

        out: list[Observation] = []
        for week, grp in df.groupby("week"):
            values = pd.to_numeric(grp[conc_col], errors="coerce").dropna()
            if values.empty:
                continue
            out.append(Observation(
                source=Source.WASTEWATER,
                metric=Metric.PATHOGEN_COPIES,
                geo_id=f"US-{state.upper()}",
                timestamp=week.to_pydatetime().replace(tzinfo=timezone.utc),
                resolution="week",
                value=float(values.median()),
                unit="copies_per_ml",
                provenance_url=(
                    f"https://data.cdc.gov/resource/{NWSS_RESOURCE}.csv"
                ),
            ))
        return out
