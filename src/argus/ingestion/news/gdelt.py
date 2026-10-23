"""GDELT 2.0 events + tone, joined to a country ISO code."""
from __future__ import annotations

import io
import zipfile
from datetime import timezone

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from argus.ingestion._http import client as http_client
from argus.ingestion.schemas.observation import Ingestor, Metric, Observation, Source

GDELT_LASTUPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# GDELT uses FIPS 10-4 country codes, which are NOT ISO 3166-1 alpha-2.
_ISO_TO_FIPS = {
    "NG": "NI",  # Nigeria
    "KE": "KE",  # Kenya
    "ZA": "SF",  # South Africa
    "EG": "EG",  # Egypt
    "US": "US",  # United States
    "GB": "UK",  # United Kingdom
}


class GDELTIngestor(Ingestor):
    """Pulls the most recent 15-minute GDELT export."""

    source = Source.NEWS

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _fetch_zip(self, url: str) -> bytes:
        async with http_client(timeout=30) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.content

    async def fetch(
        self, iso: str = "NG", keyword: str | None = None
    ) -> list[Observation]:
        async with http_client(timeout=30) as c:
            idx = (await c.get(GDELT_LASTUPDATE)).text

        candidates = [
            line.strip().split()[-1]
            for line in idx.splitlines()
            if ".export." in line.lower() and line.strip().endswith(".zip")
        ]
        if not candidates:
            raise RuntimeError(
                f"GDELT lastupdate.txt contains no export.CSV.zip entry; "
                f"raw content was: {idx[:400]!r}"
            )
        export_url = candidates[0]

        zbytes = await self._fetch_zip(export_url)
        with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
            name = zf.namelist()[0]
            df = pd.read_csv(
                zf.open(name),
                sep="\t",
                header=None,
                dtype=str,
                quoting=3,             # QUOTE_NONE: GDELT does not quote fields
                on_bad_lines="skip",
                engine="python",
                names=[
                    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
                    "Actor1Code", "Actor1Name", "Actor1CountryCode",
                    "Actor1KnownGroupCode",
                    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
                    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
                    "Actor2Code", "Actor2Name", "Actor2CountryCode",
                    "Actor2KnownGroupCode",
                    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
                    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
                    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode",
                    "QuadClass", "GoldsteinScale", "NumMentions", "NumSources",
                    "NumArticles", "AvgTone",
                    "Actor1Geo_Type", "Actor1Geo_Fullname", "Actor1Geo_CountryCode",
                    "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long",
                    "Actor1Geo_FeatureID",
                    "Actor2Geo_Type", "Actor2Geo_Fullname", "Actor2Geo_CountryCode",
                    "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long",
                    "Actor2Geo_FeatureID",
                    "ActionGeo_Type", "ActionGeo_Fullname", "ActionGeo_CountryCode",
                    "ActionGeo_ADM1Code", "ActionGeo_Lat", "ActionGeo_Long",
                    "ActionGeo_FeatureID",
                    "DATEADDED", "SOURCEURL",
                ],
            )

        # FIPS filter
        if iso.upper() not in _ISO_TO_FIPS:
            raise KeyError(
                f"ISO '{iso}' has no GDELT FIPS mapping; "
                f"add it to _ISO_TO_FIPS in {__file__}"
            )
        fips = _ISO_TO_FIPS[iso.upper()]
        df = df[df["ActionGeo_CountryCode"] == fips]
        if keyword:
            df = df[df["SOURCEURL"].str.contains(keyword, case=False, na=False)]
        if df.empty:
            return []

        # Numeric coercion: some GDELT rows have irregular column counts.
        # Coerce to numeric and drop rows where the numeric fields didn't
        # parse. This is what prevents "could not convert string to float".
        df["AvgTone"] = pd.to_numeric(df["AvgTone"], errors="coerce")
        df["NumMentions"] = pd.to_numeric(df["NumMentions"], errors="coerce")
        df = df.dropna(subset=["AvgTone"])
        if df.empty:
            return []

        df["ts"] = pd.to_datetime(
            df["DATEADDED"], format="%Y%m%d%H%M%S", utc=True, errors="coerce"
        )
        df = df.dropna(subset=["ts"])
        if df.empty:
            return []

        df["week"] = (
            df["ts"].dt.tz_convert("UTC").dt.normalize()
            - pd.to_timedelta(df["ts"].dt.day_of_week, unit="D")
        )

        out: list[Observation] = []
        for week, grp in df.groupby("week"):
            ts = week.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            out.append(
                Observation(
                    source=Source.NEWS,
                    metric=Metric.EVENT_COUNT,
                    geo_id=iso.upper(),
                    timestamp=ts,
                    resolution="week",
                    value=float(len(grp)),
                    provenance_url="https://www.gdeltproject.org/",
                )
            )
            out.append(
                Observation(
                    source=Source.NEWS,
                    metric=Metric.TONE,
                    geo_id=iso.upper(),
                    timestamp=ts,
                    resolution="week",
                    value=float(grp["AvgTone"].mean()),
                    provenance_url="https://www.gdeltproject.org/",
                )
            )
        return out