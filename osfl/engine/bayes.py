"""Conjugate Beta seeding + updating. Pure arithmetic, no rng."""

from __future__ import annotations


def beta_from_mean(mean: float, strength: float) -> tuple[float, float]:
    """Beta(alpha,beta) with the given mean and 'strength' = alpha+beta (pseudo-count)."""
    return (mean * strength, (1.0 - mean) * strength)


def update_posterior(prior: tuple[float, float], k: int, n: int) -> tuple[float, float]:
    """Conjugate update: k successes of n trials -> (alpha+k, beta+(n-k))."""
    if not (0 <= k <= n):
        raise ValueError(f"need 0 <= k <= n, got k={k}, n={n}")
    a, b = prior
    return (a + k, b + (n - k))


def posterior_mean(ab: tuple[float, float]) -> float:
    a, b = ab
    return a / (a + b)
