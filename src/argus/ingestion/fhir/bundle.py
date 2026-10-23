"""FHIR R4 Bundle ingestor (tested against Synthea output)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from argus.ingestion.schemas.observation import Ingestor, Metric, Observation, Source


class FHIRBundleIngestor(Ingestor):
    source = Source.FHIR

    async def fetch(self, bundle_path: str, condition_code: str = "59621000") -> list[Observation]:
        """condition_code: SNOMED — 59621000 = Essential hypertension (example)."""
        data = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        entries = data.get("entry", [])
        counts: dict[str, dict[str, int]] = {}

        for e in entries:
            res = e.get("resource", {})
            if res.get("resourceType") != "Condition":
                continue
            code = res.get("code", {}).get("coding", [{}])[0].get("code")
            if code != condition_code:
                continue
            onset = res.get("onsetDateTime") or res.get("recordedDate")
            if not onset:
                continue
            ts = datetime.fromisoformat(onset.replace("Z", "+00:00"))
            week = ts.strftime("%Y-W%V")
            counts.setdefault(week, {"n": 0})
            counts[week]["n"] += 1

        out: list[Observation] = []
        for week, c in counts.items():
            year, wk = week.split("-W")
            ts = datetime.fromisocalendar(int(year), int(wk), 1).replace(tzinfo=timezone.utc)
            out.append(Observation(
                source=Source.FHIR, metric=Metric.CASES, geo_id="SYNTHEA",
                timestamp=ts, resolution="week", value=float(c["n"]),
                provenance_url="https://synthea.mitre.org/",
            ))
        return out
