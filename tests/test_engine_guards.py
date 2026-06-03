"""Regression tests for engine input-guards.

Each test asserts behaviour that was RED before the guard existed — the function
used to raise a low-level error (ZeroDivisionError/IndexError), return an invalid
Beta posterior, or report an unreachable volume as if it met the threshold.
"""

from __future__ import annotations

import pytest

from osfl.engine.bayes import update_posterior
from osfl.engine.funnel import simulate_funnel
from osfl.engine.priority import shot_score, urgency_factor
from osfl.engine.strategy import min_volume_for_threshold, validate_strategy


def test_update_posterior_rejects_k_greater_than_n():
    # RED before: returned (a+k, b+(n-k)) with a negative beta → mean > 1.
    with pytest.raises(ValueError, match="0 <= k <= n"):
        update_posterior((2.0, 23.0), k=30, n=5)


def test_update_posterior_accepts_the_k_equals_n_boundary():
    assert update_posterior((2.0, 23.0), k=5, n=5) == (7.0, 23.0)


def test_urgency_factor_zero_horizon_is_max_urgency_not_zero_division():
    # RED before: 1.0 - days / 0 raised ZeroDivisionError.
    assert urgency_factor(5.0, horizon=0.0) == 1.0


def test_validate_strategy_empty_stages_raises_valueerror():
    # RED before: crashed with IndexError indexing improved[bottleneck] on an empty list.
    with pytest.raises(ValueError, match="at least one stage"):
        validate_strategy([], n0=10, T=1)


def test_min_volume_infeasible_returns_sentinel_not_a_too_small_volume():
    # A ~1e-7 conversion with T=3 cannot reach 0.99 within the 5M cap.
    # RED before: returned the last bracket bound (~6.3M), which does NOT meet the
    # threshold; now it returns the 10**9 infeasible sentinel used by the other
    # unreachable branches.
    assert min_volume_for_threshold([(1e-7, 1.0)], T=3, threshold=0.99) == 10**9


def test_simulate_funnel_zero_volume_is_certain_failure():
    res = simulate_funnel(0, [(2.0, 8.0)], T=1, runs=100, seed=1)
    assert res.p_success == 0.0  # zero attempts can never produce a success


def test_shot_score_is_the_product_of_its_four_factors():
    assert shot_score(0.5, 0.4, 0.8, 1.0) == pytest.approx(0.16)
