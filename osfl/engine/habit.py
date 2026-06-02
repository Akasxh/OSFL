"""Vectorized habit / adherence Monte Carlo.

No-burnout path: one Beta draw per run then a single Binomial — fast and deterministic.
Burnout path: a sequential decay loop over scheduled sessions (vectorized across runs),
where each miss shrinks adherence and each hit restores it. Off by default.
"""

from __future__ import annotations

import numpy as np

from .stats import SimResult, summarize


def simulate_habit(
    n_sessions: int,
    adherence: tuple[float, float],
    K: int,
    burnout: float | None = None,
    runs: int = 10000,
    seed: int | None = None,
) -> SimResult:
    if runs < 1:
        raise ValueError("runs must be >= 1")
    if burnout is not None and not (0.0 < burnout < 1.0):
        raise ValueError("burnout must be in (0, 1)")
    rng = np.random.default_rng(seed)
    a, b = adherence
    p = rng.beta(a, b, size=runs)
    if burnout is None:
        attended = rng.binomial(n_sessions, p)
    else:
        decay = float(burnout)  # in (0,1): a hit restores adherence, a miss shrinks it
        thr = np.ones(runs)
        done = np.zeros(runs, dtype=np.int64)
        for _ in range(int(n_sessions)):
            hit = rng.random(runs) < np.clip(p * thr, 0.0, 1.0)
            done += hit
            thr = np.where(hit, np.minimum(thr / decay, 1.0), np.maximum(thr * decay, 0.0))
        attended = done
    return summarize(attended, K, n_sessions, runs, seed)
