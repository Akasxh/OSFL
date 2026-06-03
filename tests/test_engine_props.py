"""Property-based + edge suite for the pure OSFL math engine.

Pure imports from ``osfl.engine`` only — no FastAPI app, no Store, no LLM. Hypothesis drives
the invariants (bounded ``max_examples`` so the file runs in well under a second); the verified
pinned numbers are kept alongside as regression anchors so no implementation can silently drift.

Design notes that keep these honest:
- The funnel MC is seeded numpy. With a *fixed* seed, monotonicity of P(success) in n0 is not
  mathematically guaranteed (different survivor counts consume different randomness downstream),
  so the monotonicity properties use a healthy run count + a tiny tolerance, which is reliable
  in practice (empirically 0 failures over hundreds of random configs).
- min_volume_for_threshold and point_estimate_p are deterministic/analytic, so those properties
  are asserted exactly.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from osfl.engine import (
    beta_from_mean,
    min_volume_for_threshold,
    point_estimate_p,
    posterior_mean,
    rank_queue,
    simulate_funnel,
    simulate_habit,
    update_posterior,
    validate_strategy,
)
from osfl.engine.strategy import _binom_sf_ge

# The verified job funnel: means 0.08, 0.40, 0.25 (prod 0.008).
JOB = [(2.0, 23.0), (4.0, 6.0), (2.5, 7.5)]

# A fast, file-wide profile: few examples, generous deadline so seeded-MC examples never flake.
FAST = settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

# Hypothesis strategy for a single Beta gate with strictly positive, finite a,b.
_gate = st.tuples(
    st.floats(min_value=0.5, max_value=12.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.5, max_value=12.0, allow_nan=False, allow_infinity=False),
)
_stages = st.lists(_gate, min_size=1, max_size=3)


# --------------------------------------------------------------------------------------------
# Funnel Monte-Carlo properties
# --------------------------------------------------------------------------------------------
@FAST
@given(
    stages=_stages,
    n0=st.integers(min_value=1, max_value=120),
    seed=st.integers(min_value=0, max_value=10_000),
)
def test_funnel_p_success_is_a_probability(stages, n0, seed):
    r = simulate_funnel(n0, stages, 1, runs=1500, seed=seed)
    assert 0.0 <= r.p_success <= 1.0


@FAST
@given(
    stages=_stages,
    seed=st.integers(min_value=0, max_value=10_000),
)
def test_funnel_p_success_weakly_increases_in_n0(stages, seed):
    # More stage-0 volume cannot lower the odds of clearing a fixed target (T=1 here).
    # Fixed seed + ample runs keeps the seeded MC reliably monotone within a small tolerance.
    ps = [simulate_funnel(n0, stages, 1, runs=4000, seed=seed).p_success for n0 in (5, 40, 150)]
    assert ps[0] <= ps[1] + 1e-9
    assert ps[1] <= ps[2] + 1e-9


@FAST
@given(
    stages=_stages,
    n0=st.integers(min_value=1, max_value=80),
    seed=st.integers(min_value=0, max_value=10_000),
)
def test_funnel_histogram_sums_to_runs_and_spans_n0(stages, n0, seed):
    runs = 1200
    r = simulate_funnel(n0, stages, 1, runs=runs, seed=seed)
    assert sum(r.hist_bins) == runs  # every run lands in exactly one success-count bin
    assert len(r.hist_bins) == n0 + 1  # bins index success counts 0..n0 inclusive
    assert all(b >= 0 for b in r.hist_bins)


@FAST
@given(
    stages=_stages,
    n0=st.integers(min_value=1, max_value=80),
    seed=st.integers(min_value=0, max_value=10_000),
)
def test_funnel_same_seed_is_bit_identical(stages, n0, seed):
    a = simulate_funnel(n0, stages, 1, runs=1500, seed=seed)
    b = simulate_funnel(n0, stages, 1, runs=1500, seed=seed)
    assert a.p_success == b.p_success
    assert a.hist_bins == b.hist_bins
    assert (a.mean, a.median, a.p10, a.p50, a.p90) == (b.mean, b.median, b.p10, b.p50, b.p90)


@FAST
@given(
    stages=_stages,
    n0=st.integers(min_value=2, max_value=60),
    seed=st.integers(min_value=0, max_value=10_000),
)
def test_funnel_summary_percentiles_are_ordered_and_bounded(stages, n0, seed):
    r = simulate_funnel(n0, stages, 1, runs=2000, seed=seed)
    assert 0.0 <= r.p10 <= r.p50 <= r.p90 <= n0
    assert r.p50 == r.median  # both are the 50th percentile of the same array
    assert 0.0 <= r.mean <= n0


# --------------------------------------------------------------------------------------------
# Analytic point-estimate properties
# --------------------------------------------------------------------------------------------
@FAST
@given(
    stages=_stages,
    n0=st.integers(min_value=0, max_value=400),
)
def test_point_estimate_p_is_a_probability(stages, n0):
    p = point_estimate_p(stages, n0, 1)
    assert 0.0 <= p <= 1.0


@FAST
@given(stages=_stages)
def test_point_estimate_p_weakly_increases_in_n0(stages):
    # Deterministic closed form, so this is exact (no tolerance needed beyond fp epsilon).
    prev = -1.0
    for n0 in (0, 5, 20, 60, 150, 400):
        cur = point_estimate_p(stages, n0, 1)
        assert cur >= prev - 1e-12
        prev = cur


def test_point_estimate_p_empty_stages_is_zero():
    assert point_estimate_p([], 60, 1) == 0.0


def test_point_estimate_p_target_zero_is_certain():
    assert point_estimate_p(JOB, 60, 0) == 1.0


def test_point_estimate_p_target_above_volume_is_impossible():
    # Cannot have more successes than attempts: P(X >= T) == 0 when T > n0.
    assert point_estimate_p(JOB, 5, 10) == 0.0


# --------------------------------------------------------------------------------------------
# min_volume_for_threshold properties
# --------------------------------------------------------------------------------------------
@FAST
@given(stages=_stages)
def test_min_volume_monotonic_in_threshold(stages):
    # A stricter success threshold can never require *fewer* attempts.
    prev = -1
    for t in (0.2, 0.4, 0.6, 0.75, 0.9, 0.95):
        mv = min_volume_for_threshold(stages, 1, t)
        assert mv >= prev
        prev = mv


@FAST
@given(
    stages=_stages,
    threshold=st.floats(min_value=0.05, max_value=0.95),
)
def test_min_volume_is_the_exact_crossing_for_T1(stages, threshold):
    # For T==1 the crossing is the smallest n with the closed-form SF >= threshold.
    mv = min_volume_for_threshold(stages, 1, threshold)
    prod = math.prod(a / (a + b) for a, b in stages)
    assert prod > 0.0  # _gate keeps a,b finite & positive => mean in (0,1)
    assert _binom_sf_ge(mv, prod, 1) >= threshold - 1e-12
    if mv > 1:
        assert _binom_sf_ge(mv - 1, prod, 1) < threshold


def test_min_volume_general_T_crossing_is_exact():
    mv = min_volume_for_threshold(JOB, 10, 0.70)  # exercises the T>1 binary-search path
    prod = 0.08 * 0.40 * 0.25
    assert _binom_sf_ge(mv, prod, 10) >= 0.70
    assert _binom_sf_ge(mv - 1, prod, 10) < 0.70


def test_min_volume_threshold_one_is_unreachable_sentinel():
    # threshold >= 1.0 can never be met by a Binomial with p<1 -> sentinel, not a crash.
    assert min_volume_for_threshold(JOB, 1, 1.0) == 10**9


def test_min_volume_prod_p_near_one_guard():
    # A degenerate certain gate (mean 1.0) must hit the prod_p>=1 guard, not a math-domain error.
    assert min_volume_for_threshold([(1.0, 0.0)], 1, 0.70) == 1


def test_min_volume_empty_stages_is_unreachable_sentinel():
    # No funnel => prod_p == 0 => target can never be cleared.
    assert min_volume_for_threshold([], 1, 0.70) == 10**9


# --------------------------------------------------------------------------------------------
# Conjugate Bayesian update properties
# --------------------------------------------------------------------------------------------
@FAST
@given(
    pa=st.floats(min_value=0.5, max_value=40.0),
    pb=st.floats(min_value=0.5, max_value=40.0),
    n=st.integers(min_value=1, max_value=200),
    frac=st.floats(min_value=0.0, max_value=1.0),
)
def test_posterior_mean_lies_between_prior_and_sample(pa, pb, n, frac):
    prior = (pa, pb)
    k = int(round(frac * n))
    post = update_posterior(prior, k, n)
    prior_m = posterior_mean(prior)
    sample_m = k / n
    post_m = posterior_mean(post)
    lo, hi = min(prior_m, sample_m), max(prior_m, sample_m)
    assert lo - 1e-9 <= post_m <= hi + 1e-9


@FAST
@given(
    pa=st.floats(min_value=0.5, max_value=40.0),
    pb=st.floats(min_value=0.5, max_value=40.0),
    k=st.integers(min_value=0, max_value=100),
    extra=st.integers(min_value=0, max_value=100),
)
def test_update_posterior_adds_pseudocounts(pa, pb, k, extra):
    n = k + extra  # guarantees 0 <= k <= n so failures (n-k) are non-negative
    a2, b2 = update_posterior((pa, pb), k, n)
    assert a2 == pa + k
    assert b2 == pb + (n - k)
    assert posterior_mean((a2, b2)) == pytest.approx((pa + k) / (pa + pb + n))


def test_beta_from_mean_update_roundtrip_pins():
    # beta_from_mean reproduces the population prior; the verified divergence pins to (7, 48).
    a, b = beta_from_mean(0.08, 25)
    assert (a, b) == pytest.approx((2.0, 23.0))
    post = update_posterior((2.0, 23.0), 5, 30)
    assert post == (7.0, 48.0)
    assert posterior_mean(post) == pytest.approx(0.1273, abs=1e-3)


# --------------------------------------------------------------------------------------------
# Priority-queue properties
# --------------------------------------------------------------------------------------------
def _candidate(gid, impact, ltv, days, p_now, p_plus_one, **kw):
    base = {
        "goal_id": gid,
        "shot_type_id": kw.get("shot_type_id", "x"),
        "impact": impact,
        "ltv": ltv,
        "days_to_deadline": days,
        "p_now": p_now,
        "p_plus_one": p_plus_one,
    }
    base.update(kw)
    return base


@FAST
@given(
    gains=st.lists(
        st.tuples(
            st.floats(min_value=0.0, max_value=1.0),  # p_now
            st.floats(min_value=0.0, max_value=1.0),  # p_plus_one
        ),
        min_size=1,
        max_size=6,
    ),
)
def test_rank_queue_normalizes_marginal_gain_into_unit_interval(gains):
    cands = [
        _candidate(f"g{i}", impact=0.5, ltv=0.5, days=30, p_now=pn, p_plus_one=pp)
        for i, (pn, pp) in enumerate(gains)
    ]
    ranked = rank_queue(cands)
    norms = [r.marginal_p_gain for r in ranked]
    assert all(0.0 <= v <= 1.0 for v in norms)
    raw = [max(pp - pn, 0.0) for pn, pp in gains]
    if max(raw) > 0:
        # the most-leveraged candidate is anchored at exactly 1.0
        assert max(norms) == pytest.approx(1.0)
    else:
        # no positive gain anywhere -> every normalized gain collapses to 0.0
        assert all(v == 0.0 for v in norms)


@FAST
@given(
    rows=st.lists(
        st.tuples(
            st.floats(min_value=0.0, max_value=1.0),  # impact
            st.floats(min_value=0.0, max_value=1.0),  # ltv
            st.floats(min_value=0.0, max_value=60.0),  # days_to_deadline
            st.floats(min_value=0.0, max_value=0.5),  # p_now
            st.floats(min_value=0.0, max_value=0.5),  # delta to p_plus_one
        ),
        min_size=1,
        max_size=8,
    ),
)
def test_rank_queue_sorted_descending_by_score(rows):
    cands = [
        _candidate(f"g{i}", impact=imp, ltv=ltv, days=d, p_now=pn, p_plus_one=pn + dlt)
        for i, (imp, ltv, d, pn, dlt) in enumerate(rows)
    ]
    ranked = rank_queue(cands)
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 1.0 for s in scores)  # all four factors live in [0,1]


def test_rank_queue_empty_returns_empty():
    assert rank_queue([]) == []


def test_rank_queue_orders_the_pinned_example():
    cands = [
        _candidate("job", 0.90, 0.90, 45, 0.0, 0.10, shot_type_id="cold_email"),
        _candidate("fit", 0.60, 1.00, 30, 0.0, 0.06, shot_type_id="gym"),
        _candidate("reconnect", 0.40, 0.50, 13.8, 0.0, 0.04, shot_type_id="msg"),
    ]
    ranked = rank_queue(cands)
    assert [r.goal_id for r in ranked] == ["job", "fit", "reconnect"]
    assert ranked[0].score == pytest.approx(0.2025, abs=1e-4)
    assert ranked[1].score == pytest.approx(0.18, abs=1e-4)
    assert ranked[2].score == pytest.approx(0.0616, abs=1e-4)


# --------------------------------------------------------------------------------------------
# Pinned regression anchors (exact, version-independent)
# --------------------------------------------------------------------------------------------
def test_pin_fixed_p_closed_form_0p3824():
    prod = 0.08 * 0.40 * 0.25  # 0.008
    assert (1 - (1 - prod) ** 60) == pytest.approx(0.3824, abs=1e-3)


def test_pin_mc_seed42_p_success_band():
    r = simulate_funnel(60, JOB, 1, runs=10000, seed=42)
    # parameter-uncertainty MC sits below the fixed-p 0.382 for this near-floor target.
    assert r.p_success == pytest.approx(0.3201, abs=0.01)
    assert r.target == 1
    assert len(r.hist_bins) == 61
    assert sum(r.hist_bins) == 10000


def test_pin_min_volume_201_at_80pct():
    assert min_volume_for_threshold(JOB, 1, 0.80) == 201


def test_pin_min_volume_150_at_70pct():
    assert min_volume_for_threshold(JOB, 1, 0.70) == 150


def test_pin_posterior_divergence_7_48():
    post = update_posterior((2.0, 23.0), 5, 30)
    assert post == (7.0, 48.0)
    assert posterior_mean(post) == pytest.approx(7 / 55, abs=1e-9)


def test_pin_validate_rejects_job_funnel():
    rep = validate_strategy(JOB, 60, 1, threshold=0.7, seed=42)
    assert rep["passed"] is False
    assert rep["min_volume_for_threshold"] == 150
    assert rep["bottleneck_stage_index"] == 0
    assert len(rep["suggestions"]) == 3


# --------------------------------------------------------------------------------------------
# Engine edge / guard cases
# --------------------------------------------------------------------------------------------
def test_funnel_runs_below_one_raises():
    with pytest.raises(ValueError):
        simulate_funnel(60, JOB, 1, runs=0, seed=1)


def test_habit_runs_below_one_raises():
    with pytest.raises(ValueError):
        simulate_habit(60, (6, 4), 36, runs=0, seed=1)


def test_habit_burnout_out_of_range_raises():
    with pytest.raises(ValueError):
        simulate_habit(60, (6, 4), 36, burnout=1.0, runs=10, seed=1)
    with pytest.raises(ValueError):
        simulate_habit(60, (6, 4), 36, burnout=0.0, runs=10, seed=1)


def test_funnel_target_above_volume_gives_zero_p():
    # No run can clear a target larger than the starting volume.
    r = simulate_funnel(5, JOB, 10, runs=1000, seed=1)
    assert r.p_success == 0.0
    assert r.target == 10
    assert len(r.hist_bins) == 6  # bins still span 0..n0


def test_funnel_empty_stages_is_pass_through():
    # With no attrition every run keeps all n0, so any T<=n0 is certain.
    r = simulate_funnel(30, [], 30, runs=500, seed=3)
    assert r.p_success == 1.0
    assert r.mean == 30.0
    assert r.hist_bins[30] == 500
