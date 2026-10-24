"""Residual neural network using pure NumPy (no PyTorch dependency)."""
import numpy as np

class NumpyResidualNet:
    def __init__(self, input_dim: int = 4, hidden: int = 32):
        # Initialize weights matching a standard PyTorch initialization
        np.random.seed(42)
        self.w1 = np.random.randn(input_dim, hidden) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden)
        self.w2 = np.random.randn(hidden, hidden) * np.sqrt(2.0 / hidden)
        self.b2 = np.zeros(hidden)
        self.w3 = np.random.randn(hidden, 1) * np.sqrt(2.0 / hidden)
        self.b3 = np.zeros(1)
        self.lr = 0.01

    def forward(self, x: np.ndarray) -> np.ndarray:
        self.z1 = x @ self.w1 + self.b1
        self.a1 = np.maximum(0, self.z1) # ReLU
        self.z2 = self.a1 @ self.w2 + self.b2
        self.a2 = np.maximum(0, self.z2) # ReLU
        self.z3 = self.a2 @ self.w3 + self.b3
        return self.z3.flatten()

    def train_step(self, x: np.ndarray, y: np.ndarray) -> float:
        # Forward
        out = self.forward(x)
        
        # Loss (MSE)
        loss = np.mean((out - y) ** 2)
        d_out = 2 * (out - y) / len(y)
        
        # Backward
        d_w3 = self.a2.T @ d_out[:, None]
        d_b3 = np.sum(d_out)
        d_a2 = d_out[:, None] @ self.w3.T
        d_z2 = d_a2 * (self.z2 > 0)
        d_w2 = self.a1.T @ d_z2
        d_b2 = np.sum(d_z2, axis=0)
        d_a1 = d_z2 @ self.w2.T
        d_z1 = d_a1 * (self.z1 > 0)
        d_w1 = x.T @ d_z1
        d_b1 = np.sum(d_z1, axis=0)
        
        # Update
        self.w3 -= self.lr * d_w3
        self.b3 -= self.lr * d_b3
        self.w2 -= self.lr * d_w2
        self.b2 -= self.lr * d_b2
        self.w1 -= self.lr * d_w1
        self.b1 -= self.lr * d_b1
        return loss
