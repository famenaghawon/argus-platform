"""Shared async HTTP client with a stable User-Agent.

Several public endpoints (notably GDELT) behave inconsistently for requests
without a User-Agent header -- returning empty 200 responses rather than
data. Always route ingestor HTTP calls through `client()` so the UA and
timeout are consistent across sources and inspectable in VCR cassettes.
"""
from __future__ import annotations

import httpx

USER_AGENT = (
    "argus-platform/0.2 "
    "(+https://github.com/famenaghawon/argus-platform; "
    "public health research)"
)


def client(timeout: float = 30.0, auth: tuple[str, str] | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=timeout,
        auth=auth,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )