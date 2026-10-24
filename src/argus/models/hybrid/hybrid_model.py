"""Hybrid SEIR + ResidualNet detector, drop-in replacement for Farrington."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam

from argus.models.hybrid.residual_net import ResidualNet
from argus.models.hybrid.seir import SEIRParams, simulate_seir


class HybridDetector:
    """Fit SEIR + residual on a weekly series, predict next-week thresholds."""

    def __init__(
        self,
        seir_params: SEIRParams | None = None,
        epochs: int = 200,
        learning_rate: float = 1e-2,
        seed: int = 42,
    ):
        self.seir_params = seir_params or SEIRParams()
        self.epochs = epochs
        self.lr = learning_rate
        self.seed = seed
        self.residual_net: ResidualNet | None = None
        self.residual_std: float = 1.0

    def _features(self, seir_log: np.ndarray, prev_log: np.ndarray) -> np.ndarray:
        """Build the residual net input from SEIR prediction and previous obs."""
        n = len(seir_log)
        weeks = np.arange(n) % 52.1775
        sin_w = np.sin(2 * np.pi * weeks / 52.1775)
        cos_w = np.cos(2 * np.pi * weeks / 52.1775)
        return np.stack([seir_log, prev_log, sin_w, cos_w], axis=-1).astype(np.float32)

    def fit(self, history: np.ndarray) -> None:
        """Fit the residual net on the historical series (log1p scale)."""
        torch.manual_seed(self.seed)
        history = np.asarray(history, dtype=float)
        y_log = np.log1p(history)

        seir = simulate_seir(self.seir_params, n_weeks=len(history))
        seir_log = np.log1p(seir * 1e7)  # arbitrary scale to line up with concentrations

        prev_log = np.concatenate([[y_log[0]], y_log[:-1]])
        X = self._features(seir_log, prev_log)
        Y = y_log.astype(np.float32)

        # Residual = target - SEIR prediction (both on log scale)
        residual_target = Y - seir_log.astype(np.float32)

        self.residual_net = ResidualNet(input_dim=4)
        optimizer = Adam(self.residual_net.parameters(), lr=self.lr)
        loss_fn = nn.MSELoss()

        X_t = torch.from_numpy(X)
        Y_t = torch.from_numpy(residual_target)

        self.residual_net.train()
        for _ in range(self.epochs):
            optimizer.zero_grad()
            pred = self.residual_net(X_t)
            loss = loss_fn(pred, Y_t)
            loss.backward()
            optimizer.step()

        self.residual_net.eval()
        with torch.no_grad():
            pred = self.residual_net(X_t).numpy()
        resid = residual_target - pred
        self.residual_std = float(np.std(resid)) + 1e-6

    def predict_threshold(self, history: np.ndarray, z: float = 1.96) -> float:
        """Given history, return upper threshold on the ORIGINAL scale."""
        if self.residual_net is None:
            raise RuntimeError("Call fit() first")

        history = np.asarray(history, dtype=float)
        y_log = np.log1p(history)

        n_weeks = len(history) + 1
        seir = simulate_seir(self.seir_params, n_weeks=n_weeks)
        seir_log = np.log1p(seir * 1e7)

        # Predict next-week residual using the last feature row
        prev_log = float(y_log[-1])
        next_week = n_weeks - 1
        week_of_year = next_week % 52.1775
        sin_w = np.sin(2 * np.pi * week_of_year / 52.1775)
        cos_w = np.cos(2 * np.pi * week_of_year / 52.1775)
        feat = np.array(
            [[seir_log[-1], prev_log, sin_w, cos_w]], dtype=np.float32
        )

        with torch.no_grad():
            residual = float(self.residual_net(torch.from_numpy(feat)).item())

        mu_log = seir_log[-1] + residual
        # Upper quantile on log scale (adds z * std * sqrt(mu+phi*mu^2) equivalent)
        upper_log = mu_log + z * self.residual_std
        return float(np.expm1(upper_log))
