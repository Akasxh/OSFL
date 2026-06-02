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
    "beta_from_mean",
    "posterior_mean",
    "update_posterior",
    "funnel_trajectory",
    "simulate_funnel",
    "simulate_habit",
    "RankedShot",
    "marginal_p_gain",
    "rank_queue",
    "shot_score",
    "urgency_factor",
    "SimResult",
    "summarize",
    "BottleneckReport",
    "find_bottleneck",
    "min_volume_for_threshold",
    "point_estimate_p",
    "validate_strategy",
]
