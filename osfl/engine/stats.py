"""Summarize a final-counts array into a SimResult. Pure numpy. Shared by funnel + habit."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SimResult:
    p_success: float
    mean: float
    median: float
    p10: float
    p50: float
    p90: float
    hist_bins: list[int]  # index == success count, 0..n0
    n0: int
    runs: int
    seed: int | None
    target: int


def summarize(final: np.ndarray, T: int, n0: int, runs: int, seed: int | None) -> SimResult:
    final = np.asarray(final, dtype=np.int64)
    bins = np.bincount(final, minlength=n0 + 1)[: n0 + 1]
    return SimResult(
        p_success=float((final >= T).mean()),
        mean=float(final.mean()),
        median=float(np.median(final)),
        p10=float(np.percentile(final, 10)),
        p50=float(np.percentile(final, 50)),
        p90=float(np.percentile(final, 90)),
        hist_bins=bins.astype(int).tolist(),
        n0=int(n0),
        runs=int(runs),
        seed=seed,
        target=int(T),
    )
