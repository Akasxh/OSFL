"""Pin the verified OSFL numbers so no implementation can silently drift.

Exact, version-independent facts (closed form / arithmetic) are asserted tightly.
The one MC value (seed 42) is asserted within a band; numpy is pinned via uv.lock.
"""

import math

from osfl.engine import (
    beta_from_mean,
    find_bottleneck,
    min_volume_for_threshold,
    posterior_mean,
    rank_queue,
    simulate_funnel,
    simulate_habit,
    update_posterior,
    validate_strategy,
)

JOB = [(2.0, 23.0), (4.0, 6.0), (2.5, 7.5)]  # means 0.08, 0.40, 0.25


def test_funnel_fixed_p_closed_form():
    prod = 0.08 * 0.40 * 0.25  # 0.008
    assert abs((1 - (1 - prod) ** 60) - 0.3824) < 1e-3


def test_funnel_mc_seed42_band():
    r = simulate_funnel(60, JOB, 1, runs=10000, seed=42)
    assert abs(r.p_success - 0.3201) < 0.01  # parameter-uncertainty MC < fixed-p 0.382
    assert r.target == 1
    assert len(r.hist_bins) == 61
    assert sum(r.hist_bins) == 10000


def test_funnel_ev_chain_and_bottleneck():
    bn = find_bottleneck(60, JOB, 1)
    assert abs(bn.ev_chain[-1] - 0.48) < 1e-6  # 60 * 0.008
    assert bn.stage_index == 0  # the 8% apply->screen gate


def test_min_volume_80pct_is_201():
    assert min_volume_for_threshold(JOB, 1, 0.80) == 201


def test_min_volume_70pct_is_150():
    assert min_volume_for_threshold(JOB, 1, 0.70) == 150


def test_bayes_divergence():
    post = update_posterior((2.0, 23.0), 5, 30)
    assert post == (7.0, 48.0)
    assert abs(posterior_mean(post) - 7 / 55) < 1e-9
    assert abs(posterior_mean(post) - 0.1273) < 1e-3  # 12.7% vs population 8%


def test_beta_from_mean_roundtrip():
    a, b = beta_from_mean(0.08, 25)
    assert abs(a - 2.0) < 1e-9 and abs(b - 23.0) < 1e-9


def test_validate_rejects_job_funnel():
    rep = validate_strategy(JOB, 60, 1, threshold=0.7, seed=42)
    assert rep["passed"] is False
    assert rep["min_volume_for_threshold"] == 150
    assert rep["bottleneck_stage_index"] == 0
    assert len(rep["suggestions"]) == 3


def test_priority_ranking():
    cands = [
        {"goal_id": "job", "shot_type_id": "cold_email", "impact": 0.90,
         "days_to_deadline": 45, "ltv": 0.90, "p_now": 0.0, "p_plus_one": 0.10},
        {"goal_id": "fit", "shot_type_id": "gym", "impact": 0.60,
         "days_to_deadline": 30, "ltv": 1.00, "p_now": 0.0, "p_plus_one": 0.06},
        {"goal_id": "reconnect", "shot_type_id": "msg", "impact": 0.40,
         "days_to_deadline": 13.8, "ltv": 0.50, "p_now": 0.0, "p_plus_one": 0.04},
    ]
    ranked = rank_queue(cands)
    assert [r.goal_id for r in ranked] == ["job", "fit", "reconnect"]
    assert abs(ranked[0].score - 0.2025) < 1e-4
    assert abs(ranked[1].score - 0.18) < 1e-4
    assert abs(ranked[2].score - 0.0616) < 1e-4


def test_habit_runs():
    r = simulate_habit(60, (6, 4), 36, seed=42)
    assert 0.45 < r.p_success < 0.62
    assert r.target == 36


def test_min_volume_general_T_fast_and_exact():
    import time

    from osfl.engine.strategy import _binom_sf_ge

    t = time.perf_counter()
    mv = min_volume_for_threshold(JOB, 10, 0.70)  # T>1 path
    elapsed = time.perf_counter() - t
    assert elapsed < 0.5  # exp+binary search, not the old O(n^2) scan
    prod = 0.08 * 0.40 * 0.25
    assert _binom_sf_ge(mv, prod, 10) >= 0.70  # crossing is exact
    assert _binom_sf_ge(mv - 1, prod, 10) < 0.70


def test_min_volume_degenerate_prod_p_guard():
    # stage mean 1.0 (beta=0 at engine level) -> prod_p>=1 guard, no math-domain crash
    assert min_volume_for_threshold([(1.0, 0.0)], 1, 0.70) == 1


def test_runs_zero_raises():
    import pytest

    with pytest.raises(ValueError):
        simulate_funnel(60, JOB, 1, runs=0, seed=1)
    with pytest.raises(ValueError):
        simulate_habit(60, (6, 4), 36, runs=0, seed=1)
