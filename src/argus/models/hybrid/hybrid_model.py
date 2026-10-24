"""Hybrid SEIR + ResidualNet detector, drop-in replacement for Farrington."""
from __future__ import annotations

import numpy as np

from argus.models.hybrid.residual_net import NumpyResidualNet
from argus.models.hybrid.seir import SEIRParams, simulate_seir


class HybridDetector:
    def __init__(
        self,
        seir_params: SEIRParams | None = None,
        epochs: int = 200,
        seed: int = 42,
    ):
        self.seir_params = seir_params or SEIRParams()
        self.epochs = epochs
        self.seed = seed
        self.residual_net: NumpyResidualNet | None = None
        self.residual_std: float = 1.0

    def _features(self, seir_log: np.ndarray, prev_log: np.ndarray) -> np.ndarray:
        n = len(seir_log)
        weeks = np.arange(n) % 52.1775
        sin_w = np.sin(2 * np.pi * weeks / 52.1775)
        cos_w = np.cos(2 * np.pi * weeks / 52.1775)
        return np.stack([seir_log, prev_log, sin_w, cos_w], axis=-1).astype(np.float32)

    def fit(self, history: np.ndarray) -> None:
        np.random.seed(self.seed)
        history = np.asarray(history, dtype=float)
        y_log = np.log1p(history)

        seir = simulate_seir(self.seir_params, n_weeks=len(history))
        seir_log = np.log1p(seir * 1e7)

        prev_log = np.concatenate([[y_log[0]], y_log[:-1]])
        X = self._features(seir_log, prev_log)
        Y = y_log.astype(np.float32)

        residual_target = Y - seir_log.astype(np.float32)

        self.residual_net = NumpyResidualNet(input_dim=4)

        for _ in range(self.epochs):
            self.residual_net.train_step(X, residual_target)

        pred = self.residual_net.forward(X)
        resid = residual_target - pred
        self.residual_std = float(np.std(resid)) + 1e-6

    def predict_threshold(self, history: np.ndarray, z: float = 1.96) -> float:
        if self.residual_net is None:
            raise RuntimeError("Call fit() first")

        history = np.asarray(history, dtype=float)
        y_log = np.log1p(history)

        n_weeks = len(history) + 1
        seir = simulate_seir(self.seir_params, n_weeks=n_weeks)
        seir_log = np.log1p(seir * 1e7)

        prev_log = float(y_log[-1])
        next_week = n_weeks - 1
        week_of_year = next_week % 52.1775
        sin_w = np.sin(2 * np.pi * week_of_year / 52.1775)
        cos_w = np.cos(2 * np.pi * week_of_year / 52.1775)
        
        feat = np.array([[seir_log[-1], prev_log, sin_w, cos_w]], dtype=np.float32)

        residual = float(self.residual_net.forward(feat)[0])

        mu_log = seir_log[-1] + residual
        upper_log = mu_log + z * self.residual_std
        return float(np.expm1(upper_log))
