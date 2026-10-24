"""Residual neural network learning a correction to SEIR predictions."""
from __future__ import annotations

import torch
import torch.nn as nn


class ResidualNet(nn.Module):
    """Small MLP: takes feature vector, outputs a scalar correction (log scale).

    Input dim = 1 (SEIR log prediction) + 1 (previous observed log value) +
    1 (week-of-year sine) + 1 (week-of-year cosine) = 4 by default.
    """

    def __init__(self, input_dim: int = 4, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)
