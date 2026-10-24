"""Federated learning server.

Status: **stub** — a working implementation requires Flower / NVFlare.
"""
from __future__ import annotations


def start_server(address: str = "0.0.0.0:8080", n_rounds: int = 10) -> None:
    """Aggregate client updates for `n_rounds` rounds.

    Not implemented. A real version would:
    1. Accept connections from N clients.
    2. Broadcast global weights, wait for updates.
    3. Aggregate via federated averaging (or DP-FedAvg).
    4. Repeat for `n_rounds`.
    """
    raise NotImplementedError(
        "Federated server not yet implemented. See docs/limitations.md."
    )