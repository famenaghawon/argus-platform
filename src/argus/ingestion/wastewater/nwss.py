"""CDC National Wastewater Surveillance System - public CSV via Socrata."""
from __future__ import annotations

import io
from datetime import timezone

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from argus.ingestion._http import client as http_client
from argus.ingestion.schemas.observation import Ingestor, Metric, Observation, Source

NWSS_RESOURCE = "g653-rqe2"


class NWSSIngestor(Ingestor):
    source = Source.WASTEWATER

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _get(self, url: str) -> str:
        async with http_client(timeout=60) as c:
            r = await c.get(url, headers={"Accept": "text/csv"})
            r.raise_for_status()
            return r.text

    async def fetch(self, state: str = "GA", pathogen: str = "sars-cov-2") -> list[Observation]:
        # The dataset only has key_plot_id, date, pcr_conc_lin, normalization.
        # State is embedded in key_plot_id, e.g. NWSS_ca_2705_Treatment...
        # So we use SoQL LIKE to filter case-insensitively on "_<state>_".
        st = state.lower()
        url = (
            f"https://data.cdc.gov/resource/{NWSS_RESOURCE}.csv"
            f"?%24where=lower(key_plot_id)+like+%27%25_{st}_%25%27"
            f"&%24order=date+ASC"
            f"&%24limit=50000"
        )

        csv = await self._get(url)
        df = pd.read_csv(io.StringIO(csv))

        if df.empty or "date" not in df.columns or "pcr_conc_lin" not in df.columns:
            return []

        # Belt-and-braces: filter client-side too (the LIKE is case-insensitive
        # but exact token matching is important to avoid _ca_ matching _sc_ etc.)
        if "key_plot_id" in df.columns:
            df = df[df["key_plot_id"].astype(str).str.contains(f"_{st}_", case=False, na=False)]

        df["ts"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
        df = df.dropna(subset=["ts"])
        if df.empty:
            return []

        df["week"] = (
            df["ts"].dt.tz_convert("UTC").dt.normalize()
            - pd.to_timedelta(df["ts"].dt.day_of_week, unit="D")
        )

        out: list[Observation] = []
        for week, grp in df.groupby("week"):
            values = pd.to_numeric(grp["pcr_conc_lin"], errors="coerce").dropna()
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
                provenance_url=f"https://data.cdc.gov/resource/{NWSS_RESOURCE}.csv",
            ))
        return out
