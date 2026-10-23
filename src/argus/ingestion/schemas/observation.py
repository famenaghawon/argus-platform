"""Common Observation contract every ingestor must satisfy."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Protocol

from pydantic import BaseModel, Field, field_validator


class Source(str, Enum):
    DHIS2 = "dhis2"
    FHIR = "fhir"
    SORMAS = "sormas"
    WASTEWATER = "wastewater"
    CLIMATE = "climate"
    NEWS = "news"


class Metric(str, Enum):
    # Clinical
    CASES = "cases"
    ILI_RATE = "ili_rate"
    HOSPITALIZATIONS = "hospitalizations"
    # Wastewater
    PATHOGEN_COPIES = "pathogen_copies_per_ml"
    AMR_GENE_COPIES = "amr_gene_copies_per_ml"
    # Climate
    TEMP_C = "temperature_celsius"
    PRECIP_MM = "precipitation_mm"
    # News / event signals
    EVENT_COUNT = "event_count"
    TONE = "avg_tone"


class Observation(BaseModel):
    """A single fused-ready observation. Never contains PII."""
    source: Source
    metric: Metric
    geo_id: str = Field(..., description="ISO 3166-2 or DHIS2 org unit UID")
    geo_name: str | None = None
    timestamp: datetime = Field(..., description="UTC, start of the aggregation window")
    resolution: Literal["day", "week", "month"] = "week"
    value: float
    unit: str | None = None
    provenance_url: str | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("timestamp", "ingested_at")
    @classmethod
    def _must_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware (UTC)")
        return v


class Ingestor(Protocol):
    source: Source

    async def fetch(self, **kwargs) -> list[Observation]: ...
