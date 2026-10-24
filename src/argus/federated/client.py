"""Federated learning client.

Status: **stub** — a working implementation requires Flower / NVFlare
and a real cross-institution data-sharing agreement. This module
documents the intended interface.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClientConfig:
    server_address: str = "127.0.0.1:8080"
    client_id: str = "client-0"
    local_epochs: int = 5
    batch_size: int = 32


def start_client(config: ClientConfig, data_path: str) -> None:
    """Start a federated learning client.

    Not implemented. A real version would:
    1. Load the local training data from `data_path`.
    2. Connect to the federated server at `config.server_address`.
    3. Receive global model weights, fine-tune locally, upload back.
    """
    raise NotImplementedError(
        "Federated client not yet implemented. See docs/limitations.md."
    )