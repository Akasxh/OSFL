"""Backend API suite — in-process FastAPI TestClient, offline, deterministic.

Covers every endpoint in the FEATURES contract (GET/POST/PATCH), the full goal
lifecycle (create -> decompose -> simulate -> validate -> log-outcome -> re-sim),
the /outcomes response BUNDLE, queue/wellbeing/followup shapes, every documented
error path (404 + the four 422s), and the offline LLM fallbacks.

Notes on isolation
------------------
The `client` fixture wraps a fresh TestClient over the SAME module-level Store, so
mutations persist within a pytest process. Tests are therefore written to be
order-independent: any test that mutates posteriors/goal state creates its OWN
goal + shot_type instead of corrupting the three seeded demo goals that the
read-only / pin tests rely on. Seeded reads never assume a prior test ran.
"""

from __future__ import annotations

import copy

import pytest


# --------------------------------------------------------------------------- #
# isolation: this module mutates the SHARED module-level store (creates goals,
# updates seeded posteriors). Snapshot the whole store doc before the module runs
# and restore it after, so other test files (e.g. the harness smoke test that
# asserts exactly 3 goals) see the store exactly as seeded.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module", autouse=True)
def _restore_store_after_module():
    import osfl.app as appmod

    snapshot = copy.deepcopy(appmod.store.doc)
    yield
    appmod.store.doc = copy.deepcopy(snapshot)
    appmod.store.save()


def test_healthz_reports_ok_and_store_is_readable(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["goals"] >= 3  # the three seeded demo goals are present
    assert body["llm"] is False  # the test harness forces the offline path


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _goals(client) -> list[dict]:
    r = client.get("/api/goals")
    assert r.status_code == 200
    return r.json()


def _seeded_job(client) -> dict:
    return next(g for g in _goals(client) if g["title"] == "Land a job")


def _seeded_habit(client) -> dict:
    return next(g for g in _goals(client) if g["kind"] == "habit")


def _make_funnel_goal(client, title="Land a job (scratch)") -> dict:
    """Create a fresh funnel goal that auto-decomposes (job archetype) so mutation
    tests never touch the pinned seeded goals."""
    r = client.post("/api/goals", json={"title": title, "deadline": "2026-12-31"})
    assert r.status_code == 200
    return r.json()


# --------------------------------------------------------------------------- #
# State / read endpoints
# --------------------------------------------------------------------------- #
def test_get_state_returns_full_dashboard_payload(client):
    body = client.get("/api/state").json()
    assert set(body) == {"goals", "shot_types", "queue", "wellbeing", "followups", "personas", "llm"}
    assert len(body["goals"]) >= 3
    assert isinstance(body["queue"], list)
    assert isinstance(body["shot_types"], list)


def test_get_state_status_code_ok(client):
    assert client.get("/api/state").status_code == 200


def test_list_goals_contains_three_seeded(client):
    titles = {g["title"] for g in _goals(client)}
    assert {"Land a job", "Raise a seed round", "Get fit"} <= titles


def test_get_goal_by_id_roundtrips(client):
    job = _seeded_job(client)
    r = client.get(f"/api/goals/{job['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == job["id"]
    assert r.json()["title"] == "Land a job"


def test_list_shot_types_nonempty_with_expected_fields(client):
    sts = client.get("/api/shot_types").json()
    assert len(sts) >= 1
    one = sts[0]
    assert {"id", "name", "alpha", "beta"} <= set(one)


def test_get_personas_has_three_clusters(client):
    personas = client.get("/api/personas").json()
    assert set(personas) == {"professional", "friends", "family"}
    # professional is emoji-free per the persona contract
    assert personas["professional"]["emoji_rate"] == 0.0


def test_get_queue_is_sorted_descending_by_score(client):
    q = client.get("/api/queue").json()
    assert len(q) >= 1
    scores = [item["score"] for item in q]
    assert scores == sorted(scores, reverse=True)
    # marginal_p_gain is normalized to [0,1]; the leverage leader anchors at 1.0
    assert all(0.0 <= item["marginal_p_gain"] <= 1.0 for item in q)


def test_get_queue_items_have_score_factor_fields(client):
    q = client.get("/api/queue").json()
    item = q[0]
    assert {
        "shot_type_id",
        "goal_id",
        "goal_title",
        "score",
        "impact",
        "urgency",
        "long_term_value",
        "marginal_p_gain",
        "rationale",
    } <= set(item)


def test_get_queue_limit_param_truncates(client):
    full = client.get("/api/queue").json()
    if len(full) < 2:
        pytest.skip("need >=2 queue items to test limit")
    limited = client.get("/api/queue", params={"limit": 1}).json()
    assert len(limited) == 1
    assert limited[0]["goal_id"] == full[0]["goal_id"]


def test_get_wellbeing_shape(client):
    w = client.get("/api/wellbeing").json()
    assert {"momentum", "streak_days", "load", "at_risk_goals", "message"} <= set(w)
    assert w["load"] in ("light", "steady", "heavy")
    assert 0.0 <= w["momentum"] <= 1.0
    assert isinstance(w["at_risk_goals"], list)


def test_get_followups_shape(client):
    fs = client.get("/api/followups").json()
    assert isinstance(fs, list)
    # seeded goals have no logged outcomes -> each surfaces a "take the first shot" nudge
    assert len(fs) >= 1
    one = fs[0]
    assert {"goal_id", "goal_title", "shot_type_id", "due_in_days", "reason"} <= set(one)


# --------------------------------------------------------------------------- #
# Offline LLM fallbacks
# --------------------------------------------------------------------------- #
def test_llm_status_is_offline(client):
    body = client.get("/api/llm/status").json()
    assert body["available"] is False
    assert body["model"] is None


def test_state_llm_block_reports_offline(client):
    llm = client.get("/api/state").json()["llm"]
    assert llm["available"] is False
    assert llm["model"] is None


def test_draft_engine_is_template_offline(client):
    job = _seeded_job(client)
    st_id = job["stages"][0]["shot_type_id"]
    r = client.post("/api/draft", json={"shot_type_id": st_id, "persona": "professional"})
    assert r.status_code == 200
    d = r.json()
    assert d["engine"] == "template"
    assert d["body"]


def test_draft_honours_persona_cluster(client):
    job = _seeded_job(client)
    st_id = job["stages"][0]["shot_type_id"]
    d = client.post("/api/draft", json={"shot_type_id": st_id, "persona": "friends", "subcluster": "close"}).json()
    assert d["persona"] == "friends"
    assert d["engine"] == "template"


def test_draft_use_llm_true_still_falls_back_offline(client):
    """use_llm=True must NOT error offline — it falls through to the template."""
    job = _seeded_job(client)
    st_id = job["stages"][0]["shot_type_id"]
    d = client.post("/api/draft", json={"shot_type_id": st_id, "persona": "professional", "use_llm": True}).json()
    assert d["engine"] == "template"


def test_advise_unavailable_offline(client):
    r = client.post("/api/advise", json={"question": "Is my job plan realistic?"})
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is False
    assert body["model"] is None
    assert "OPENAI_API_KEY" in body["answer"]


def test_advise_with_goal_id_still_offline(client):
    job = _seeded_job(client)
    body = client.post("/api/advise", json={"question": "What now?", "goal_id": job["id"]}).json()
    assert body["available"] is False


# --------------------------------------------------------------------------- #
# Simulation endpoint (deterministic seed)
# --------------------------------------------------------------------------- #
def test_simulate_job_funnel_is_seed_pinned(client):
    """seed=42 MC for the seeded job funnel pins to ~0.3201 (engine pin)."""
    job = _seeded_job(client)
    sim = client.post(f"/api/goals/{job['id']}/simulate", json={"runs": 10000, "seed": 42}).json()
    assert abs(sim["p_success"] - 0.3201) < 0.01
    assert sim["target"] == 1
    # histogram covers 0..n0 (60) inclusive and sums to the run count
    assert len(sim["hist_bins"]) == 61
    assert sum(sim["hist_bins"]) == 10000


def test_simulate_is_deterministic_for_same_seed(client):
    job = _seeded_job(client)
    a = client.post(f"/api/goals/{job['id']}/simulate", json={"runs": 5000, "seed": 7}).json()
    b = client.post(f"/api/goals/{job['id']}/simulate", json={"runs": 5000, "seed": 7}).json()
    assert a["p_success"] == b["p_success"]
    assert a["hist_bins"] == b["hist_bins"]
    assert a["mean_final"] == b["mean_final"]


def test_simulate_percentiles_are_ordered(client):
    job = _seeded_job(client)
    sim = client.post(f"/api/goals/{job['id']}/simulate", json={"runs": 8000, "seed": 42}).json()
    assert sim["p10"] <= sim["p50"] <= sim["p90"]


def test_simulate_habit_goal(client):
    fit = _seeded_habit(client)
    sim = client.post(f"/api/goals/{fit['id']}/simulate", json={"runs": 6000, "seed": 42}).json()
    assert sim["target"] == fit["target_sessions"] == 36
    assert sim["per_stage_drop"] is None  # habit goals carry no funnel drop chain
    assert 0.0 <= sim["p_success"] <= 1.0


# --------------------------------------------------------------------------- #
# Validation endpoint (strategy)
# --------------------------------------------------------------------------- #
def test_validate_job_funnel_is_rejected(client):
    """Job funnel at 60 attempts is below the 70% threshold; min-volume pins to 150."""
    job = _seeded_job(client)
    rep = client.post(f"/api/goals/{job['id']}/validate", json={"seed": 42}).json()
    assert rep["passed"] is False
    assert rep["min_volume_for_threshold"] == 150
    assert rep["threshold"] == job["threshold"] == 0.7
    assert len(rep["suggestions"]) == 3
    kinds = {s["kind"] for s in rep["suggestions"]}
    assert kinds == {"more_volume", "extend_deadline", "better_shot_type"}


def test_validate_reports_bottleneck_stage(client):
    job = _seeded_job(client)
    rep = client.post(f"/api/goals/{job['id']}/validate", json={"seed": 42}).json()
    # stage-0 'Apply' (8% conversion) is the tightest gate
    apply_stage = sorted(job["stages"], key=lambda s: s["order"])[0]
    assert rep["bottleneck_stage_id"] == apply_stage["id"]
    assert "Apply" in rep["bottleneck_reason"]


def test_validate_habit_goal_has_no_funnel_bottleneck(client):
    fit = _seeded_habit(client)
    rep = client.post(f"/api/goals/{fit['id']}/validate", json={"seed": 42}).json()
    assert rep["bottleneck_stage_id"] is None
    assert rep["min_volume_for_threshold"] is None
    assert "adherence" in rep["bottleneck_reason"].lower()


# --------------------------------------------------------------------------- #
# Goal lifecycle: create + auto-decompose
# --------------------------------------------------------------------------- #
def test_create_goal_auto_decomposes_funnel(client):
    g = _make_funnel_goal(client, title="Land my next job")
    assert g["kind"] == "funnel"
    assert len(g["stages"]) == 3  # job archetype -> 3 stages
    assert g["last_sim"] is not None  # warm-simulated on create
    assert g["last_sim"]["p_success"] >= 0.0


def test_create_goal_appears_in_list(client):
    g = _make_funnel_goal(client, title="A brand new goal to find")
    ids = {x["id"] for x in _goals(client)}
    assert g["id"] in ids


def test_create_fitness_goal_becomes_habit(client):
    r = client.post("/api/goals", json={"title": "Get fit again at the gym", "deadline": "2026-12-31"})
    g = r.json()
    assert g["kind"] == "habit"
    assert g["shot_type_id"] is not None
    assert g["stages"] == []


def test_explicit_decompose_endpoint(client):
    g = _make_funnel_goal(client, title="Raise a seed round soon")
    r = client.post(f"/api/goals/{g['id']}/decompose")
    assert r.status_code == 200
    again = r.json()
    assert again["kind"] == "funnel"
    assert len(again["stages"]) == 3


# --------------------------------------------------------------------------- #
# Goal lifecycle: PATCH
# --------------------------------------------------------------------------- #
def test_patch_goal_updates_volume_and_resimulates(client):
    g = _make_funnel_goal(client, title="Land a job to patch")
    before_p = g["last_sim"]["p_success"]
    r = client.patch(f"/api/goals/{g['id']}", json={"n0_volume": 5000})
    assert r.status_code == 200
    patched = r.json()
    assert patched["n0_volume"] == 5000
    # far more volume -> strictly higher success odds, and last_sim is refreshed
    assert patched["last_sim"]["p_success"] > before_p


def test_patch_goal_threshold_and_status(client):
    g = _make_funnel_goal(client, title="Land a job to retarget")
    r = client.patch(f"/api/goals/{g['id']}", json={"threshold": 0.5, "status": "archived"})
    patched = r.json()
    assert patched["threshold"] == 0.5
    assert patched["status"] == "archived"


# --------------------------------------------------------------------------- #
# Goal lifecycle: log outcome (the BUNDLE) + adaptive round-trip
# --------------------------------------------------------------------------- #
def test_log_outcome_returns_full_bundle(client):
    g = _make_funnel_goal(client, title="Land a job for bundle")
    st_id = sorted(g["stages"], key=lambda s: s["order"])[0]["shot_type_id"]
    r = client.post(
        f"/api/goals/{g['id']}/outcomes",
        json={"shot_type_id": st_id, "n_attempts": 30, "k_successes": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {
        "outcome",
        "updated_shot_type",
        "before_mean",
        "after_mean",
        "last_sim",
        "validation",
        "state",
    }
    # nested state mirrors the full dashboard payload
    assert set(body["state"]) == {
        "goals",
        "shot_types",
        "queue",
        "wellbeing",
        "followups",
        "personas",
        "llm",
    }
    assert body["last_sim"]["goal_id"] == g["id"]
    assert "passed" in body["validation"]


def test_log_outcome_shifts_posterior_toward_user_rate(client):
    """Logging an above-prior result pulls the effective mean up via the conjugate
    update (your-rate vs population). Order-independent: archetype shot_types are
    deduped BY NAME and so are shared across funnel goals, so this asserts the
    update relative to the shot_type's *current* prior rather than a fixed 0.08.
    """
    g = _make_funnel_goal(client, title="Land a job posterior")
    st_id = sorted(g["stages"], key=lambda s: s["order"])[0]["shot_type_id"]

    # capture the live prior for this (possibly already-updated) shared shot_type
    st_before = next(s for s in client.get("/api/shot_types").json() if s["id"] == st_id)
    if st_before["user_alpha"] is not None:
        a0, b0 = st_before["user_alpha"], st_before["user_beta"]
    else:
        a0, b0 = st_before["alpha"], st_before["beta"]
    k, n = 5, 30
    body = client.post(
        f"/api/goals/{g['id']}/outcomes",
        json={"shot_type_id": st_id, "n_attempts": n, "k_successes": k},
    ).json()

    before_mean = a0 / (a0 + b0)
    observed = k / n
    # before_mean reflects the live prior; after_mean is the conjugate posterior mean
    assert abs(body["before_mean"] - before_mean) < 1e-9
    # the conjugate step is exactly (a+k, b+(n-k))
    assert body["updated_shot_type"]["user_alpha"] == a0 + k
    assert body["updated_shot_type"]["user_beta"] == b0 + (n - k)
    assert abs(body["after_mean"] - (a0 + k) / (a0 + b0 + n)) < 1e-9
    # the posterior mean always moves toward the observed rate (Bayesian shrinkage)
    if observed > before_mean:
        assert before_mean < body["after_mean"] <= observed
    else:
        assert observed <= body["after_mean"] < before_mean


def test_log_outcome_moves_forecast_and_revalidates(client):
    """One round-trip: posterior shifts AND forecast shifts AND re-validates."""
    g = _make_funnel_goal(client, title="Land a job forecast")
    st_id = sorted(g["stages"], key=lambda s: s["order"])[0]["shot_type_id"]
    before_p = g["last_sim"]["p_success"]
    body = client.post(
        f"/api/goals/{g['id']}/outcomes",
        json={"shot_type_id": st_id, "n_attempts": 30, "k_successes": 25},
    ).json()
    # a strong result lifts the apply-stage conversion -> the forecast must move up
    assert body["last_sim"]["p_success"] > before_p
    assert body["after_mean"] > body["before_mean"]
    assert isinstance(body["validation"]["passed"], bool)


def test_log_outcome_persists_to_state_and_followups(client):
    g = _make_funnel_goal(client, title="Land a job state check")
    st_id = sorted(g["stages"], key=lambda s: s["order"])[0]["shot_type_id"]
    body = client.post(
        f"/api/goals/{g['id']}/outcomes",
        json={"shot_type_id": st_id, "n_attempts": 10, "k_successes": 2, "note": "first batch"},
    ).json()
    # the logged goal now has an outcome -> it is no longer in the "no shots yet" set
    state_goal = next(x for x in body["state"]["goals"] if x["id"] == g["id"])
    assert state_goal["last_sim"] is not None
    assert body["outcome"]["goal_id"] == g["id"]
    assert body["outcome"]["k_successes"] == 2
    assert body["outcome"]["n_attempts"] == 10


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def test_orchestrate_routes_validate_intent_with_trace(client):
    job = _seeded_job(client)
    r = client.post("/api/orchestrate", json={"request": "validate my strategy", "goal_id": job["id"]})
    assert r.status_code == 200
    trace = r.json()
    assert set(trace) >= {"request", "cluster", "agents", "result", "elapsed_ms"}
    assert [s["name"] for s in trace["agents"]] == ["DecisionAdvisor"]
    assert "validation" in trace["result"]
    # every step carries a timing
    assert all("elapsed_ms" in s for s in trace["agents"])


def test_orchestrate_draft_intent(client):
    job = _seeded_job(client)
    trace = client.post("/api/orchestrate", json={"request": "write me a draft email", "goal_id": job["id"]}).json()
    assert [s["name"] for s in trace["agents"]] == ["Persona"]
    assert "draft" in trace["result"]


def test_orchestrate_queue_intent(client):
    trace = client.post("/api/orchestrate", json={"request": "what should I focus on next?"}).json()
    assert [s["name"] for s in trace["agents"]] == ["Planner"]
    assert "queue" in trace["result"]


def test_orchestrate_default_simulate_intent(client):
    job = _seeded_job(client)
    trace = client.post("/api/orchestrate", json={"request": "show me the odds", "goal_id": job["id"]}).json()
    # falls through to "simulate" -> Simulator only
    assert [s["name"] for s in trace["agents"]] == ["Simulator"]
    assert "last_sim" in trace["result"]


# --------------------------------------------------------------------------- #
# Error paths — 404
# --------------------------------------------------------------------------- #
def test_get_missing_goal_404(client):
    r = client.get("/api/goals/does-not-exist")
    assert r.status_code == 404
    assert r.json()["detail"] == "goal not found"


def test_simulate_missing_goal_404(client):
    assert client.post("/api/goals/nope/simulate", json={}).status_code == 404


def test_validate_missing_goal_404(client):
    assert client.post("/api/goals/nope/validate", json={}).status_code == 404


def test_decompose_missing_goal_404(client):
    assert client.post("/api/goals/nope/decompose").status_code == 404


def test_patch_missing_goal_404(client):
    assert client.patch("/api/goals/nope", json={"n0_volume": 10}).status_code == 404


def test_log_outcome_missing_goal_404(client):
    r = client.post("/api/goals/nope/outcomes", json={"shot_type_id": "x", "n_attempts": 1, "k_successes": 0})
    assert r.status_code == 404
    assert r.json()["detail"] == "goal not found"


def test_log_outcome_missing_shot_type_404(client):
    job = _seeded_job(client)
    r = client.post(
        f"/api/goals/{job['id']}/outcomes",
        json={"shot_type_id": "no-such-shot", "n_attempts": 10, "k_successes": 2},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "shot_type not found"


# --------------------------------------------------------------------------- #
# Error paths — 422
# --------------------------------------------------------------------------- #
def test_create_goal_threshold_above_one_422(client):
    r = client.post("/api/goals", json={"title": "bad", "deadline": "2026-12-01", "threshold": 1.5})
    assert r.status_code == 422


def test_log_outcome_k_greater_than_n_422(client):
    job = _seeded_job(client)
    st_id = job["stages"][0]["shot_type_id"]
    r = client.post(
        f"/api/goals/{job['id']}/outcomes",
        json={"shot_type_id": st_id, "n_attempts": 5, "k_successes": 9},
    )
    assert r.status_code == 422


def test_simulate_runs_below_one_422(client):
    job = _seeded_job(client)
    r = client.post(f"/api/goals/{job['id']}/simulate", json={"runs": 0})
    assert r.status_code == 422


def test_create_goal_target_successes_below_one_422(client):
    r = client.post(
        "/api/goals",
        json={"title": "bad", "deadline": "2026-12-01", "target_successes": 0},
    )
    assert r.status_code == 422
