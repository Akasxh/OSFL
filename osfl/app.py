"""OSFL FastAPI app — all /api routes + the static dashboard.

A single in-process Store (data/store.json), PersonaLoader, and Orchestrator are created at
import time; the store is seeded and every goal is warm-simulated once so the dashboard paints
forecasts on first load. Paths are resolved against the project root, so it runs from anywhere.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .llm import LLM
from .models import (
    AdviseRequest,
    DraftRequest,
    Goal,
    GoalCreate,
    GoalPatch,
    Outcome,
    OutcomeCreate,
    OrchestrateRequest,
    ShotType,
    SimRequest,
)
from .orchestrator import Orchestrator
from .persona.loader import PersonaLoader
from .seed import seed_store
from .store import Store

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

store = Store(os.environ.get("OSFL_STORE_PATH", str(ROOT / "data" / "store.json")))
loader = PersonaLoader(str(ROOT / "personas"))
seed_store(store)
llm = LLM()
orch = Orchestrator(store, loader, llm)

# warm last_sim on every goal so GET /api/goals paints immediately (deterministic seed)
for _raw in store.list("goals"):
    orch.simulator.run(Goal(**_raw), seed=42)

app = FastAPI(title="OSFL", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _goal(gid: str) -> Goal:
    raw = store.get("goals", gid)
    if raw is None:
        raise HTTPException(status_code=404, detail="goal not found")
    return Goal(**raw)


def _state() -> dict:
    goals = [Goal(**g) for g in store.list("goals")]
    return {
        "goals": goals,
        "shot_types": [ShotType(**s) for s in store.list("shot_types")],
        "queue": orch.planner.build_queue(),
        "wellbeing": orch.wellbeing.report(),
        "followups": orch.followup.due(),
        "personas": loader.all(),
        "llm": {"available": llm.available, "model": llm.model if llm.available else None},
    }


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


# --------------------------------------------------------------------------- #
# State / read
# --------------------------------------------------------------------------- #
@app.get("/api/state")
def get_state() -> dict:
    return _state()


@app.get("/api/goals")
def list_goals() -> list[Goal]:
    return [Goal(**g) for g in store.list("goals")]


@app.get("/api/goals/{gid}")
def get_goal(gid: str) -> Goal:
    return _goal(gid)


@app.get("/api/shot_types")
def list_shot_types() -> list[ShotType]:
    return [ShotType(**s) for s in store.list("shot_types")]


@app.get("/api/personas")
def get_personas() -> dict:
    return loader.all()


@app.get("/api/queue")
def get_queue(limit: int | None = None):
    q = orch.planner.build_queue()
    return q[:limit] if limit else q


@app.get("/api/wellbeing")
def get_wellbeing():
    return orch.wellbeing.report()


@app.get("/api/followups")
def get_followups():
    return orch.followup.due()


# --------------------------------------------------------------------------- #
# Goal lifecycle
# --------------------------------------------------------------------------- #
@app.post("/api/goals")
def create_goal(body: GoalCreate) -> Goal:
    g = Goal(**body.model_dump())
    needs_decompose = (g.kind == "funnel" and not g.stages) or (g.kind == "habit" and not g.shot_type_id)
    if needs_decompose:
        orch.planner.decompose(g)
    else:
        store.upsert("goals", g.model_dump())
    orch.simulator.run(g, seed=42)
    return _goal(g.id)


@app.post("/api/goals/{gid}/decompose")
def decompose_goal(gid: str) -> Goal:
    g = _goal(gid)
    orch.planner.decompose(g)
    orch.simulator.run(g, seed=42)
    return _goal(gid)


@app.patch("/api/goals/{gid}")
def patch_goal(gid: str, body: GoalPatch) -> Goal:
    raw = store.get("goals", gid)
    if raw is None:
        raise HTTPException(status_code=404, detail="goal not found")
    for k, v in body.model_dump(exclude_none=True).items():
        raw[k] = v
    store.upsert("goals", raw)
    orch.simulator.run(Goal(**raw), seed=42)
    return _goal(gid)


@app.post("/api/goals/{gid}/simulate")
def simulate_goal(gid: str, body: SimRequest):
    return orch.simulator.run(_goal(gid), body.runs, body.seed)


@app.post("/api/goals/{gid}/validate")
def validate_goal(gid: str, body: SimRequest):
    return orch.advisor.advise(_goal(gid), body.runs, body.seed)


@app.post("/api/goals/{gid}/outcomes")
def log_outcome(gid: str, body: OutcomeCreate) -> dict:
    g = _goal(gid)
    raw_st = store.get("shot_types", body.shot_type_id)
    if raw_st is None:
        raise HTTPException(status_code=404, detail="shot_type not found")
    if not (0 <= body.k_successes <= body.n_attempts):
        raise HTTPException(status_code=422, detail="k_successes must satisfy 0 <= k <= n_attempts")

    before_mean = ShotType(**raw_st).effective_mean()
    outcome = Outcome(goal_id=gid, **body.model_dump())
    store.upsert("outcomes", outcome.model_dump())

    updated = orch.memory.log(ShotType(**raw_st), body.k_successes, body.n_attempts)
    sim = orch.simulator.run(g, seed=42)
    validation = orch.advisor.advise(g, seed=42)

    raw_goal = store.get("goals", gid)
    raw_goal["status"] = "at_risk" if sim.p_success < g.threshold else "active"
    store.upsert("goals", raw_goal)

    return {
        "outcome": outcome,
        "updated_shot_type": updated,
        "before_mean": before_mean,
        "after_mean": updated.effective_mean(),
        "last_sim": sim,
        "validation": validation,
        "state": _state(),
    }


# --------------------------------------------------------------------------- #
# Persona + orchestration
# --------------------------------------------------------------------------- #
@app.post("/api/draft")
def post_draft(body: DraftRequest):
    return orch.persona.make_draft(
        body.shot_type_id, body.persona, body.context, body.subcluster, body.seed, body.use_llm
    )


@app.post("/api/orchestrate")
def post_orchestrate(body: OrchestrateRequest):
    intent = Orchestrator.infer_intent(body.request)
    return orch.route(intent, {"request": body.request, "goal_id": body.goal_id})


@app.get("/api/llm/status")
def llm_status() -> dict:
    return {"available": llm.available, "model": llm.model if llm.available else None}


@app.post("/api/advise")
def post_advise(body: AdviseRequest) -> dict:
    goal = _goal(body.goal_id) if body.goal_id else None
    return orch.scenario.advise(body.question, goal, body.persona)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
