"""Strategy validation: bottleneck detection, analytic min-volume, framed suggestions.

min_volume_for_threshold is the *point-estimate* volume (deterministic, version-independent):
the number of stage-0 attempts so that, under the prior/posterior mean conversion rates, a
Binomial funnel clears the target with probability >= threshold. The MC simulate() reports the
uncertainty-adjusted forecast at the *current* volume; the two answer different questions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .funnel import simulate_funnel


@dataclass
class BottleneckReport:
    stage_index: int
    ev_chain: list[float]
    sensitivities: list[float]
    reason: str


def _means(stages: list[tuple[float, float]]) -> list[float]:
    return [a / (a + b) for a, b in stages]


def find_bottleneck(n0: int, stages: list[tuple[float, float]], T: int) -> BottleneckReport:
    means = _means(stages)
    ev_chain: list[float] = []
    acc = float(n0)
    for m in means:
        acc *= m
        ev_chain.append(acc)
    ev_final = ev_chain[-1] if ev_chain else float(n0)
    # relative-bump leverage: a proportional lift to the lowest-p gate moves EV_final most.
    sensitivities = [ev_final / m if m > 0 else math.inf for m in means]
    idx = int(np.argmax(sensitivities)) if sensitivities else 0
    reason = (
        f"stage {idx} (conversion {means[idx]:.0%}) is the tightest gate — "
        f"it carries the largest EV/p leverage in the chain"
        if means
        else "no stages"
    )
    return BottleneckReport(idx, ev_chain, sensitivities, reason)


def _binom_sf_ge(n: int, p: float, T: int) -> float:
    """Exact P(X >= T) for X ~ Binomial(n, p), no scipy.

    Closed form for T<=1; otherwise an O(n) vectorized cumulative log-pmf recurrence
    (no per-element lgamma), so the min-volume search stays O(n log n) overall.
    """
    n = int(n)
    if T <= 0:
        return 1.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0 if n >= T else 0.0
    if n < T:
        return 0.0
    if T == 1:
        return 1.0 - (1.0 - p) ** n
    # log_pmf(k) = log_pmf(k-1) + log((n-k+1)/k) + log(p/(1-p)); start at k=0.
    ks = np.arange(n + 1)
    step = np.log(n - ks[:-1]) - np.log(ks[:-1] + 1.0) + math.log(p) - math.log1p(-p)
    log_pmf = np.empty(n + 1)
    log_pmf[0] = n * math.log1p(-p)
    log_pmf[1:] = log_pmf[0] + np.cumsum(step)
    return float(np.exp(log_pmf[T:]).sum())


def point_estimate_p(stages: list[tuple[float, float]], n0: int, T: int) -> float:
    """Deterministic P(success) under the point-estimate (mean) conversion rates.

    Smooth and noise-free — used by the priority queue for marginal-gain comparisons,
    where MC sampling jitter would scramble tiny +1-shot deltas.
    """
    prod = math.prod(_means(stages)) if stages else 0.0
    return _binom_sf_ge(int(n0), prod, T)


def min_volume_for_threshold(
    stages: list[tuple[float, float]],
    T: int,
    threshold: float = 0.7,
    runs: int = 10000,  # accepted for signature symmetry; analytic path is deterministic
    seed: int | None = None,
) -> int:
    means = _means(stages)
    prod_p = math.prod(means) if means else 0.0
    if prod_p <= 0.0 or threshold >= 1.0:
        return 10**9
    if prod_p >= 1.0:
        # every attempt converts deterministically; a single batch of T clears the target
        return max(int(T), 1)
    if T <= 1:
        n = math.ceil(math.log(1.0 - threshold) / math.log(1.0 - prod_p))
        return max(int(n), 1)
    # General T: SF is monotone increasing in n. Exponential-bracket then binary-search.
    hi = max(T, 1)
    while _binom_sf_ge(hi, prod_p, T) < threshold:
        hi *= 2
        if hi > 5_000_000:
            return 10**9  # unreachable within a sane volume cap — same infeasible sentinel as above
    lo = T
    while lo < hi:
        mid = (lo + hi) // 2
        if _binom_sf_ge(mid, prod_p, T) >= threshold:
            hi = mid
        else:
            lo = mid + 1
    return lo


def validate_strategy(
    stages: list[tuple[float, float]],
    n0: int,
    T: int,
    threshold: float = 0.7,
    runs: int = 10000,
    seed: int | None = None,
) -> dict:
    if not stages:
        raise ValueError("validate_strategy requires at least one stage")
    sim = simulate_funnel(n0, stages, T, runs=runs, seed=seed)
    bn = find_bottleneck(n0, stages, T)
    min_vol = min_volume_for_threshold(stages, T, threshold)

    suggestions = [
        {
            "kind": "more_volume",
            "detail": f"Raise stage-0 volume from {n0} to ~{min_vol} attempts to clear {threshold:.0%}.",
            "projected_p": float(threshold),
        },
        {
            "kind": "extend_deadline",
            "detail": (
                f"Keep volume at {n0} but extend the deadline so the prescribed throughput is "
                f"realistic to execute (current odds {sim.p_success:.0%})."
            ),
            "projected_p": float(sim.p_success),
        },
    ]

    # better_shot_type: lift the bottleneck gate to a referral-grade rate, hold its strength.
    improved = list(stages)
    bi = bn.stage_index
    a, b = improved[bi]
    cur = a / (a + b)
    # clamp into a valid, sensible probability: 2x current, floored at 25%, capped at 95%
    # (without the cap, a bottleneck mean > 50% would make (1-better) negative → invalid Beta)
    better = min(max(cur * 2.0, 0.25), 0.95)
    s = a + b
    improved[bi] = (better * s, (1.0 - better) * s)
    mv2 = min_volume_for_threshold(improved, T, threshold)
    suggestions.append(
        {
            "kind": "better_shot_type",
            "detail": (
                f"Swap stage {bi} for a higher-conversion channel (~{better:.0%}); "
                f"then only ~{mv2} attempts reach {threshold:.0%}."
            ),
            "projected_p": float(threshold),
        }
    )

    return {
        "passed": bool(sim.p_success >= threshold),
        "p_success": float(sim.p_success),
        "threshold": float(threshold),
        "bottleneck_stage_index": bn.stage_index,
        "bottleneck_reason": bn.reason,
        "min_volume_for_threshold": int(min_vol),
        "suggestions": suggestions,
    }
