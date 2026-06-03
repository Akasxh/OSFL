"""Vectorized Beta-Binomial funnel Monte Carlo.

Key modelling choice: p_i is sampled PER RUN (rng.beta(a, b, size=runs)), not once, which
injects parameter uncertainty on top of binomial noise. This is why the MC P(>=1) sits BELOW
the fixed-p closed form for a near-floor target — a deliberate choice, see docs/adr/0001.
"""

from __future__ import annotations

import numpy as np

from .stats import SimResult, summarize


def simulate_funnel(
    n0: int,
    stages: list[tuple[float, float]],
    T: int,
    runs: int = 10000,
    seed: int | None = None,
) -> SimResult:
    if runs < 1:
        raise ValueError("runs must be >= 1")
    rng = np.random.default_rng(seed)
    counts = np.full(runs, n0, dtype=np.int64)
    for a, b in stages:
        p = rng.beta(a, b, size=runs)
        counts = rng.binomial(counts, p)
    return summarize(counts, T, n0, runs, seed)


def funnel_trajectory(
    n0: int,
    stages: list[tuple[float, float]],
    runs: int = 10000,
    seed: int | None = None,
) -> np.ndarray:
    """Survivor counts after each stage. Shape (len(stages)+1, runs); row 0 == n0."""
    rng = np.random.default_rng(seed)
    counts = np.full(runs, n0, dtype=np.int64)
    traj = [counts.copy()]
    for a, b in stages:
        p = rng.beta(a, b, size=runs)
        counts = rng.binomial(counts, p)
        traj.append(counts.copy())
    return np.asarray(traj)
