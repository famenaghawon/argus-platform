"""ERA5-Land daily temperature & precipitation via Copernicus CDS."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone

import cdsapi
import xarray as xr

from argus.ingestion.schemas.observation import Ingestor, Metric, Observation, Source


class ERA5Ingestor(Ingestor):
    source = Source.CLIMATE

    def __init__(self, cache_dir: str = "data/cache/era5") -> None:
        self.cache_dir = cache_dir
        self.client = cdsapi.Client()  # reads ~/.cdsapirc

    async def fetch(
        self,
        area: tuple[float, float, float, float] = (7.0, 2.0, 4.0, 5.0),  # Nigeria bbox
        geo_id: str = "NG",
        start: date = date(2024, 1, 1),
        end: date = date(2024, 1, 31),
    ) -> list[Observation]:
        # CDS API is sync — run in a thread so the event loop is not blocked
        return await asyncio.to_thread(self._fetch_sync, area, geo_id, start, end)

    def _fetch_sync(self, area, geo_id, start, end):
        target = f"{self.cache_dir}/{geo_id}_{start}_{end}.nc"
        self.client.retrieve(
            "reanalysis-era5-land",
            {
                "variable": ["2m_temperature", "total_precipitation"],
                "year": [str(start.year)],
                "month": [f"{m:02d}" for m in range(start.month, end.month + 1)],
                "day": [f"{d:02d}" for d in range(1, 32)],
                "time": "00:00",
                "area": list(area),
                "format": "netcdf",
            },
            target,
        )
        ds = xr.open_dataset(target)
        df = ds.mean(dim=["latitude", "longitude"]).to_dataframe().reset_index()

        out: list[Observation] = []
        for _, row in df.iterrows():
            ts = row["valid_time"].to_pydatetime().replace(tzinfo=timezone.utc)
            out.append(Observation(
                source=Source.CLIMATE, metric=Metric.TEMP_C, geo_id=geo_id,
                timestamp=ts, resolution="day", value=float(row["t2m"]) - 273.15, unit="C",
                provenance_url="https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land",
            ))
            out.append(Observation(
                source=Source.CLIMATE, metric=Metric.PRECIP_MM, geo_id=geo_id,
                timestamp=ts, resolution="day", value=float(row["tp"]) * 1000, unit="mm",
                provenance_url="https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land",
            ))
        return out
