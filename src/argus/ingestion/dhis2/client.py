"""DHIS2 Web API client — defaults to the public demo (play.dhis2.org)."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from argus.ingestion.schemas.observation import Ingestor, Metric, Observation, Source
from argus.ingestion._http import client as http_client

# play.dhis2.org/40.1.0 is a 302 alias to play.im.dhis2.org/stable-2-40-12.
# Point at the canonical host to avoid redirects entirely; this also
# produces cleaner cassette recordings.
DEMO_BASE = "https://play.im.dhis2.org/stable-2-40-12"


class DHIS2Ingestor(Ingestor):
    source = Source.DHIS2

    # Demo server credentials are publicly documented at the login page
    # ("Log in with admin / district"). Hardcoding them here is safe for
    # the demo instance; for any real DHIS2 endpoint, the caller must
    # supply username and password explicitly.
    def __init__(
        self,
        base_url: str = DEMO_BASE,
        username: str | None = "admin",
        password: str | None = "district",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password) if username else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with http_client(timeout=30, auth=self.auth) as c:
            r = await c.get(f"{self.base_url}/api/{path}", params=params or {})
            r.raise_for_status()
            return r.json()

    async def fetch(
        self,
        data_element_uid: str,
        org_unit_uid: str,
        period: str = "LAST_12_MONTHS",
    ) -> list[Observation]:
        payload = await self._get(
            "analytics.json",
            {
                "dimension": [
                    f"dx:{data_element_uid}",
                    f"ou:{org_unit_uid}",
                    "pe:" + period,
                ],
                "displayProperty": "NAME",
            },
        )
        headers = [h["name"] for h in payload.get("headers", [])]
        rows = payload.get("rows", [])
        out: list[Observation] = []
        for row in rows:
            rec = dict(zip(headers, row))
            pe = rec.get("Period") or rec.get("pe")
            ou = rec.get("Organisation unit") or rec.get("ou")
            val = rec.get("Value") or rec.get("value")
            if val is None:
                continue
            # DHIS2 period formats vary: 202401, 2024W12, 2024Q1...
            ts = _parse_dhis2_period(pe)
            if ts is None:
                continue
            out.append(Observation(
                source=Source.DHIS2, metric=Metric.CASES, geo_id=ou,
                timestamp=ts, resolution="month", value=float(val),
                provenance_url=f"{self.base_url}/api/analytics.json?dimension=dx:{data_element_uid}",
            ))
        return out


def _parse_dhis2_period(pe: str | None) -> datetime | None:
    if not pe:
        return None
    try:
        if "W" in pe:
            y, w = pe.split("W")
            return datetime.fromisocalendar(int(y), int(w), 1).replace(tzinfo=timezone.utc)
        if "Q" in pe:
            y, q = pe.split("Q")
            return datetime(int(y), (int(q) - 1) * 3 + 1, 1, tzinfo=timezone.utc)
        if len(pe) == 6:
            return datetime(int(pe[:4]), int(pe[4:]), 1, tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
    return None
