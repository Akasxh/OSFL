"""Lightweight in-process orchestrator. Routes an intent (or a free-text request) to a
cluster + an ordered agent-set, fires them, and records a watchable OrchestratorTrace with
per-agent timings. The API calls agents directly for the main flows; this powers the
'see the routing' panel and the generic POST /api/orchestrate.
"""

from __future__ import annotations

from time import perf_counter

from .agents import (
    Advisor,
    DecisionAdvisor,
    Followup,
    Memory,
    Persona,
    Planner,
    Simulator,
    Wellbeing,
)
from .llm import LLM
from .models import AgentStep, Goal, OrchestratorTrace, ShotType
from .persona.loader import PersonaLoader
from .store import Store


class Orchestrator:
    ROUTES: dict[str, list[str]] = {
        "plan": ["Planner", "Simulator", "DecisionAdvisor"],
        "simulate": ["Simulator"],
        "validate": ["DecisionAdvisor"],
        "log": ["Memory", "Simulator", "DecisionAdvisor"],
        "draft": ["Persona"],
        "queue": ["Planner"],
        "wellbeing": ["Wellbeing", "Followup"],
    }

    def __init__(self, store: Store, loader: PersonaLoader, llm: LLM | None = None) -> None:
        self.store = store
        self.loader = loader
        self.llm = llm or LLM()
        self.planner = Planner(store, self.llm)
        self.simulator = Simulator(store)
        self.persona = Persona(store, loader, self.llm)
        self.followup = Followup(store)
        self.wellbeing = Wellbeing(store)
        self.advisor = DecisionAdvisor(store)          # strategy validation (deterministic)
        self.scenario = Advisor(store, loader, self.llm)  # free-text scenario advice (LLM)
        self.memory = Memory(store)

    # -- routing ------------------------------------------------------------ #
    @staticmethod
    def infer_intent(request: str) -> str:
        r = request.lower()
        if any(w in r for w in ("draft", "write", "message", "email", "reply")):
            return "draft"
        if any(w in r for w in ("validate", "reject", "strategy", "enough", "realistic")):
            return "validate"
        if any(w in r for w in ("queue", "next", "priorit", "focus")):
            return "queue"
        if any(w in r for w in ("wellbeing", "burnout", "burning", "momentum", "tired", "streak")):
            return "wellbeing"
        if any(w in r for w in ("plan", "decompose", "break down")):
            return "plan"
        return "simulate"

    def _cluster_for(self, payload: dict, goal: Goal | None) -> str:
        if payload.get("persona"):
            return payload["persona"]
        if goal and goal.kind == "funnel" and goal.stages:
            raw = self.store.get("shot_types", sorted(goal.stages, key=lambda s: s.order)[0].shot_type_id)
            if raw and raw.get("persona"):
                return raw["persona"]
        if goal and goal.shot_type_id:
            raw = self.store.get("shot_types", goal.shot_type_id)
            if raw and raw.get("persona"):
                return raw["persona"]
        return "professional"

    def route(self, intent: str, payload: dict) -> OrchestratorTrace:
        t0 = perf_counter()
        goal: Goal | None = None
        if payload.get("goal_id"):
            raw = self.store.get("goals", payload["goal_id"])
            goal = Goal(**raw) if raw else None
        cluster = self._cluster_for(payload, goal)
        steps: list[AgentStep] = []
        result: dict = {}

        for name in self.ROUTES.get(intent, ["Planner"]):
            s = perf_counter()
            action, summary = "skip", "no-op"
            if name == "Planner" and intent == "plan" and goal:
                self.planner.decompose(goal)
                action, summary = "decompose", f"{len(goal.stages)} stages"
            elif name == "Planner":
                q = self.planner.build_queue()
                result["queue"] = [x.model_dump() for x in q]
                action, summary = "build_queue", f"{len(q)} ranked"
            elif name == "Simulator" and goal:
                sim = self.simulator.run(goal, payload.get("runs", 10000), payload.get("seed"))
                result["last_sim"] = sim.model_dump()
                action, summary = "monte_carlo", f"P(success)={sim.p_success:.0%}"
            elif name == "DecisionAdvisor" and goal:
                rep = self.advisor.advise(goal, payload.get("runs", 10000), payload.get("seed"))
                result["validation"] = rep.model_dump()
                action, summary = "validate", ("PASS" if rep.passed else "REJECT")
            elif (
                name == "Memory"
                and goal
                and payload.get("shot_type_id")
                and payload.get("k") is not None
                and payload.get("n") is not None
            ):
                raw = self.store.get("shot_types", payload["shot_type_id"])
                if raw:
                    st = self.memory.log(ShotType(**raw), payload["k"], payload["n"])
                    result["updated_shot_type"] = st.model_dump()
                    action, summary = "bayes_update", f"mean→{st.effective_mean():.1%}"
            elif name == "Persona":
                stid = payload.get("shot_type_id")
                if not stid and goal:
                    if goal.kind == "funnel" and goal.stages:
                        stid = sorted(goal.stages, key=lambda s: s.order)[0].shot_type_id
                    else:
                        stid = goal.shot_type_id
                if stid:
                    ctx = dict(payload.get("context", {}))
                    if goal:
                        ctx.setdefault("goal_id", goal.id)
                    d = self.persona.make_draft(stid, cluster, ctx, payload.get("subcluster", "normal"), payload.get("seed"))
                    result["draft"] = d.model_dump()
                    action, summary = "draft", f"{cluster} voice"
            elif name == "Followup":
                f = self.followup.due()
                result["followups"] = [x.model_dump() for x in f]
                action, summary = "followups", f"{len(f)} due"
            elif name == "Wellbeing":
                w = self.wellbeing.report()
                result["wellbeing"] = w.model_dump()
                action, summary = "wellbeing", w.load
            steps.append(
                AgentStep(name=name, action=action, output_summary=summary, elapsed_ms=int((perf_counter() - s) * 1000))
            )

        return OrchestratorTrace(
            request=payload.get("request", intent),
            cluster=cluster,
            agents=steps,
            result=result,
            elapsed_ms=int((perf_counter() - t0) * 1000),
        )
