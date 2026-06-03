"""Regression + edge-case coverage for issues the test-rigor review surfaced.

All offline/deterministic. Each restores the shared app store so order-independence holds.
"""

from __future__ import annotations

import copy
import re

import pytest

from osfl.agents import _spec_from_llm
from osfl.engine import simulate_habit, validate_strategy


@pytest.fixture(autouse=True)
def _isolate_store():
    """Snapshot/restore the module-level app store so API tests here don't leak state."""
    from osfl import app as appmod

    snap = copy.deepcopy(appmod.store.doc)
    yield
    appmod.store.doc = copy.deepcopy(snap)
    appmod.store.save()


# --------------------------------------------------------------------------- #
# REGRESSION: better_shot_type must never propose an invalid (>100%) channel.
# --------------------------------------------------------------------------- #
def test_better_shot_type_clamped_for_high_conversion_bottleneck():
    # an all-high-conversion funnel: the bottleneck mean is > 50%, which pre-fix made
    # better = cur*2 > 1.0 → a negative-beta Beta and a nonsensical ">100%" suggestion.
    stages = [(6.0, 4.0), (7.0, 3.0)]  # means 0.60, 0.70
    rep = validate_strategy(stages, n0=5, T=1, threshold=0.95, seed=42)
    swap = next(s for s in rep["suggestions"] if s["kind"] == "better_shot_type")
    pcts = [int(m) for m in re.findall(r"~(\d+)%", swap["detail"])]
    assert pcts, "expected a percentage in the suggestion detail"
    assert all(p <= 95 for p in pcts), f"channel conversion not clamped: {pcts} in {swap['detail']!r}"
    # and the improved-channel volume is a sane positive integer (no sentinel / no crash)
    vol = int(re.search(r"~(\d+) attempts", swap["detail"]).group(1))
    assert 1 <= vol < 1_000_000


def test_validate_strategy_never_emits_over_100_percent():
    for stages in ([(8.0, 2.0)], [(9.0, 1.0), (8.0, 2.0)], [(2.0, 23.0), (4.0, 6.0)]):
        rep = validate_strategy(stages, n0=10, T=1, threshold=0.99, seed=1)
        for s in rep["suggestions"]:
            for p in re.findall(r"~(\d+)%", s["detail"]):
                assert int(p) <= 100, f"{s['kind']}: {s['detail']!r}"


# --------------------------------------------------------------------------- #
# LLM-spec clamping: adversarial model JSON is coerced to valid bounds (deterministic).
# --------------------------------------------------------------------------- #
def test_spec_from_llm_clamps_adversarial_funnel():
    spec = _spec_from_llm({
        "kind": "funnel",
        "stages": [{"name": "X!! weird", "conversion": 5.0, "persona": "martian"},
                   {"name": "Y", "conversion": -1.0}],
        "n0_volume": -3, "target_successes": 0,
    })
    assert spec["kind"] == "funnel"
    for _name, _label, mean, a, b, persona in spec["stages"]:
        assert 0.01 <= mean <= 0.97
        assert a > 0 and b > 0
        assert persona in ("professional", "friends", "family")
    assert spec["n0"] >= 1 and spec["target"] >= 1


def test_spec_from_llm_clamps_adversarial_habit():
    spec = _spec_from_llm({"kind": "habit", "adherence": 9.0, "scheduled_sessions": 0,
                           "target_sessions": -2, "shot_name": "Run!"})
    assert spec["kind"] == "habit"
    name, label, mean, a, b, persona = spec["shot"]
    assert 0.05 <= mean <= 0.95 and a > 0 and b > 0
    assert spec["sessions"] >= 1 and spec["target"] >= 1
    assert persona == "professional"


def test_spec_from_llm_empty_stages_raises():
    with pytest.raises(ValueError):
        _spec_from_llm({"kind": "funnel", "stages": []})


# --------------------------------------------------------------------------- #
# Habit burnout-decay path (the sequential loop) is valid and deterministic.
# --------------------------------------------------------------------------- #
def test_habit_burnout_path_deterministic_and_valid():
    a = simulate_habit(40, (6.0, 4.0), 20, burnout=0.8, seed=42)
    b = simulate_habit(40, (6.0, 4.0), 20, burnout=0.8, seed=42)
    assert a.p_success == b.p_success and a.hist_bins == b.hist_bins
    assert 0.0 <= a.p_success <= 1.0
    assert sum(a.hist_bins) == a.runs
    # burnout makes adherence harder than the no-decay path → not higher success
    plain = simulate_habit(40, (6.0, 4.0), 20, seed=42)
    assert a.p_success <= plain.p_success + 1e-9


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.5, 1.5])
def test_habit_burnout_domain_guard(bad):
    with pytest.raises(ValueError):
        simulate_habit(40, (6.0, 4.0), 20, burnout=bad, seed=1)


# --------------------------------------------------------------------------- #
# API graceful paths the review flagged.
# --------------------------------------------------------------------------- #
def test_draft_with_unknown_shot_type_is_graceful(client):
    r = client.post("/api/draft", json={"shot_type_id": "does-not-exist", "persona": "professional",
                                        "context": {"name": "Sam"}})
    assert r.status_code == 200
    body = r.json()
    assert body["engine"] == "template" and body["body"]


def test_wellbeing_goes_heavy_with_many_active_goals(client):
    # seed has 3 active goals; adding more pushes active>3 → load 'heavy'
    for t in ("launch a podcast", "learn spanish"):
        assert client.post("/api/goals", json={"title": t, "deadline": "2026-12-01"}).status_code == 200
    wb = client.get("/api/wellbeing").json()
    assert wb["load"] == "heavy"
    assert set(wb) >= {"momentum", "streak_days", "load", "at_risk_goals", "message"}
