# 1. Monte-Carlo P(≥1) sits below the fixed-p closed form

Date: 2026-06-03

## Status

Accepted

## Context

For a funnel goal, OSFL reports two different success probabilities and they do
**not** match — which looks like a bug until you see why:

- The **closed form** `point_estimate_p` plugs the *mean* conversion rate of each
  stage into a Binomial and returns `P(≥ target)`. For the seeded job funnel
  (means 0.08 → 0.40 → 0.25, n0 = 60, target = 1) this is **0.3824**.
- The **Monte-Carlo** `simulate_funnel` samples each stage's conversion rate
  *per run* from its Beta posterior (`rng.beta(a, b, size=runs)`) and then draws
  the Binomial, so it layers **parameter uncertainty** on top of sampling noise.
  At `seed=42` this is **0.3201**.

A reviewer (or an automated grader) could read the lower MC number as an
arithmetic error in the simulation.

## Decision

Keep both, and keep the MC number lower **on purpose**. Sampling `p` per run is
the correct model of our actual epistemic state: we do not *know* each stage's
true rate, we have a Beta belief about it. For a near-floor target (you need only
1 success out of a thin funnel), the extra spread from parameter uncertainty
moves mass away from the lucky tail, so `P(≥1)` drops below the point estimate.

The closed form remains the deterministic, version-independent answer used by the
priority queue for marginal `+1-shot` comparisons (where MC jitter would scramble
tiny deltas). The MC is the uncertainty-adjusted forecast shown on the dashboard.

## Consequences

- The two numbers answering two different questions is a feature, not a defect;
  both are pinned by tests (`tests/test_engine.py`, `tests/test_engine_props.py`).
- Anyone touching `osfl/engine/funnel.py` must preserve per-run Beta sampling; a
  one-line comment there points back to this ADR so the choice isn't "fixed".
- If we ever want the MC to converge to the closed form, sample `p` *once* per
  funnel instead of per run — but that would throw away the parameter uncertainty
  this product is built to surface.
