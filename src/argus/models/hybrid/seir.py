"""Simplified SEIR compartmental model producing weekly infectious fractions.

Pure numpy, no learned components. This is the mechanistic backbone of the
hybrid model. Parameters (beta, sigma, gamma) control transmission, incubation,
and recovery rates respectively. The output is the weekly fraction of the
population in the infectious (I) compartment.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SEIRParams:
    beta: float = 0.3
    sigma: float = 0.14     # 1/incubation period (7 days)
    gamma: float = 0.14     # 1/infectious period (7 days)
    initial_exposed_frac: float = 0.001
    initial_infected_frac: float = 0.0


def simulate_seir(
    params: SEIRParams,
    n_weeks: int,
    steps_per_week: int = 7,
) -> np.ndarray:
    """Discrete-time SEIR simulation returning I (infectious) fraction per week.

    Args:
        params: SEIR parameters.
        n_weeks: number of weekly output points to produce.
        steps_per_week: sub-week integration steps (7 = daily).

    Returns:
        np.ndarray of shape (n_weeks,), each entry in [0, 1] = infectious fraction.
    """
    S = 1.0 - params.initial_exposed_frac - params.initial_infected_frac
    E = params.initial_exposed_frac
    I = params.initial_infected_frac
    R = 0.0

    dt = 1.0 / steps_per_week
    out = np.zeros(n_weeks)

    for week in range(n_weeks):
        for _ in range(steps_per_week):
            dS = -params.beta * S * I * dt
            dE = (params.beta * S * I - params.sigma * E) * dt
            dI = (params.sigma * E - params.gamma * I) * dt
            dR = params.gamma * I * dt
            S += dS
            E += dE
            I += dI
            R += dR
        out[week] = I

    return out
