"""OSFL math engine — pure numpy, no I/O, deterministic given a seed."""

from .bayes import beta_from_mean, posterior_mean, update_posterior
from .funnel import funnel_trajectory, simulate_funnel
from .habit import simulate_habit
from .priority import (
    RankedShot,
    marginal_p_gain,
    rank_queue,
    shot_score,
    urgency_factor,
)
from .stats import SimResult, summarize
from .strategy import (
    BottleneckReport,
    find_bottleneck,
    min_volume_for_threshold,
    point_estimate_p,
    validate_strategy,
)

__all__ = [
    "BottleneckReport",
    "RankedShot",
    "SimResult",
    "beta_from_mean",
    "find_bottleneck",
    "funnel_trajectory",
    "marginal_p_gain",
    "min_volume_for_threshold",
    "point_estimate_p",
    "posterior_mean",
    "rank_queue",
    "shot_score",
    "simulate_funnel",
    "simulate_habit",
    "summarize",
    "update_posterior",
    "urgency_factor",
    "validate_strategy",
]
