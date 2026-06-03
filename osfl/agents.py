"""The OSFL agents. Each is a thin class over engine + store + persona.

The engine math is always deterministic. The *language* agents (Planner.decompose,
Persona.make_draft, Advisor.advise) optionally use an LLM when OPENAI_API_KEY is set, each
with a deterministic offline fallback so the app never hard-depends on the network.

  Planner          decompose a goal into a funnel/habit (LLM or archetype); build the queue
  Simulator        run Monte Carlo and cache last_sim on the goal
  Persona          draft a 'you-voiced' message in the right cluster (LLM or template)
  Followup         surface threads that need a nudge
  Wellbeing        momentum / streak / load / at-risk
  DecisionAdvisor  validate a strategy and frame fixes
  Advisor          answer free-text scenario questions as a sharper version of you (LLM)
  Memory           conjugate-update a shot type's posterior from a logged outcome
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, ClassVar, Literal, cast

from . import engine as E
from .llm import LLM
from .models import (
    Cluster,
    Goal,
    PersonaDraft,
    QueueItem,
    ShotType,
    SimulationResult,
    Suggestion,
    ValidationReport,
    WellbeingReport,
)
from .models import (
    Followup as FollowupModel,  # aliased: the agent class below is also named Followup
)
from .persona.drafter import draft as draft_fn
from .persona.drafter import seed_from
from .persona.loader import PersonaLoader
from .persona.voice import split_subject, voice_system_prompt, voice_user_prompt
from .store import Store

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _to_date(s: str) -> date:
    return date.fromisoformat(s[:10])


def _days_until(deadline_iso: str, today: date) -> float:
    return float((_to_date(deadline_iso) - today).days)


def _stage_priors(store: Store, goal: Goal) -> list[tuple[float, float]]:
    priors: list[tuple[float, float]] = []
    for st in sorted(goal.stages, key=lambda s: s.order):
        raw = store.get("shot_types", st.shot_type_id)
        if raw is None:
            priors.append((1.0, 1.0))
        else:
            priors.append(ShotType(**raw).effective_prior())
    return priors


def _habit_prior(store: Store, goal: Goal) -> tuple[float, float]:
    raw = store.get("shot_types", goal.shot_type_id) if goal.shot_type_id else None
    return ShotType(**raw).effective_prior() if raw else (1.0, 1.0)


def _habit_sessions(goal: Goal) -> int:
    return goal.n0_volume or max(goal.target_sessions * 2, goal.target_sessions + 1)


_SKELETON_BY_NAME = [
    ("application", "apply"),
    ("email", "apply"),
    ("intro", "intro"),
    ("gym", "habit_nudge"),
    ("session", "habit_nudge"),
    ("screen", "followup"),
    ("interview", "followup"),
    ("meeting", "followup"),
    ("partner", "followup"),
]


def _skeleton_for(shot_type_name: str) -> str:
    low = (shot_type_name or "").lower()
    for key, skel in _SKELETON_BY_NAME:
        if key in low:
            return skel
    return "ask"


# -- LLM goal-decomposition helpers (convert model JSON into an ARCHETYPES-shaped spec) ----- #
def _clamp(x: Any, lo: float, hi: float) -> float:
    try:
        val = float(x)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, val))


def _slug(s: str) -> str:
    import re

    out = re.sub(r"[^a-z0-9]+", "_", (s or "step").lower()).strip("_")
    return out or "step"


def _persona_of(p: object) -> Cluster:
    if p == "friends":
        return "friends"
    if p == "family":
        return "family"
    return "professional"


def _spec_from_llm(data: dict[str, Any]) -> dict[str, Any]:
    """Turn the model's JSON into the same spec shape Planner.ARCHETYPES uses."""
    if data.get("kind") == "habit":
        mean = _clamp(data.get("adherence", 0.6), 0.05, 0.95)
        a, b = E.beta_from_mean(mean, 12.0)
        name = data.get("shot_name", "Session")
        return {
            "kind": "habit",
            "sessions": int(_clamp(data.get("scheduled_sessions", 60), 1, 100_000)),
            "target": int(_clamp(data.get("target_sessions", 30), 1, 100_000)),
            "shot": (_slug(name), name, mean, a, b, _persona_of(data.get("persona"))),
        }
    stages = []
    for s in (data.get("stages") or [])[:5]:
        mean = _clamp(s.get("conversion", 0.2), 0.01, 0.97)
        a, b = E.beta_from_mean(mean, 12.0)
        label = s.get("name", "Stage")
        stages.append((_slug(label), label, mean, a, b, _persona_of(s.get("persona"))))
    if not stages:
        raise ValueError("LLM returned no stages")
    return {
        "kind": "funnel",
        "stages": stages,
        "n0": int(_clamp(data.get("n0_volume", 50), 1, 1_000_000)),
        "target": int(_clamp(data.get("target_successes", 1), 1, 10_000)),
    }


# --------------------------------------------------------------------------- #
class Simulator:
    def __init__(self, store: Store) -> None:
        self.store = store

    def run(self, goal: Goal, runs: int = 10000, seed: int | None = None) -> SimulationResult:
        if goal.kind == "funnel":
            stages = _stage_priors(self.store, goal)
            res = E.simulate_funnel(goal.n0_volume, stages, goal.target_successes, runs, seed)
            traj = E.funnel_trajectory(goal.n0_volume, stages, runs, seed)
            per_stage_drop = traj.mean(axis=1).tolist()
            target = goal.target_successes
        else:
            n = _habit_sessions(goal)
            res = E.simulate_habit(n, _habit_prior(self.store, goal), goal.target_sessions, None, runs, seed)
            per_stage_drop = None
            target = goal.target_sessions

        sim = SimulationResult(
            goal_id=goal.id,
            runs=res.runs,
            seed=res.seed,
            p_success=res.p_success,
            mean_final=res.mean,
            median_final=res.median,
            p10=res.p10,
            p50=res.p50,
            p90=res.p90,
            hist_bins=res.hist_bins,
            hist_edges=[float(i) for i in range(len(res.hist_bins) + 1)],
            per_stage_drop=per_stage_drop,
            target=target,
        )
        raw = self.store.get("goals", goal.id)
        if raw is not None:
            raw["last_sim"] = sim.model_dump()
            self.store.upsert("goals", raw)
        return sim


class Memory:
    def __init__(self, store: Store) -> None:
        self.store = store

    def log(self, shot_type: ShotType, k: int, n: int) -> ShotType:
        a, b = E.update_posterior(shot_type.effective_prior(), k, n)
        shot_type.user_alpha = a
        shot_type.user_beta = b
        self.store.upsert("shot_types", shot_type.model_dump())
        return shot_type


class DecisionAdvisor:
    def __init__(self, store: Store) -> None:
        self.store = store

    def advise(self, goal: Goal, runs: int = 10000, seed: int | None = None) -> ValidationReport:
        if goal.kind != "funnel" or not goal.stages:
            sim = Simulator(self.store).run(goal, runs, seed)
            passed = sim.p_success >= goal.threshold
            suggestions = []
            if not passed:
                suggestions = [
                    Suggestion(
                        kind="more_volume",
                        detail="Schedule more sessions or raise weekly cadence to lift adherence headroom.",
                        projected_p=min(sim.p_success + 0.15, 0.99),
                    ),
                    Suggestion(
                        kind="extend_deadline",
                        detail="Extend the horizon so the target session count is reachable at a sustainable pace.",
                        projected_p=goal.threshold,
                    ),
                ]
            return ValidationReport(
                goal_id=goal.id,
                passed=passed,
                p_success=sim.p_success,
                threshold=goal.threshold,
                bottleneck_stage_id=None,
                bottleneck_reason="Habit goal — adherence is the single lever.",
                min_volume_for_threshold=None,
                suggestions=suggestions,
            )

        stages = _stage_priors(self.store, goal)
        rep = E.validate_strategy(stages, goal.n0_volume, goal.target_successes, goal.threshold, runs, seed)
        sorted_stages = sorted(goal.stages, key=lambda s: s.order)
        bi = rep["bottleneck_stage_index"]
        stage = sorted_stages[bi] if 0 <= bi < len(sorted_stages) else None
        reason = rep["bottleneck_reason"]
        if stage is not None:
            reason = reason.replace(f"stage {bi}", f"'{stage.name}'")
        return ValidationReport(
            goal_id=goal.id,
            passed=rep["passed"],
            p_success=rep["p_success"],
            threshold=rep["threshold"],
            bottleneck_stage_id=stage.id if stage else None,
            bottleneck_reason=reason,
            min_volume_for_threshold=rep["min_volume_for_threshold"],
            suggestions=[Suggestion(**s) for s in rep["suggestions"]],
        )


class Planner:
    ARCHETYPES: ClassVar[dict[str, dict[str, Any]]] = {
        "job": {
            "kind": "funnel",
            "n0": 60,
            "target": 1,
            "stages": [
                ("cold_email", "Apply", 0.08, 2.0, 23.0, "professional"),
                ("recruiter_screen", "Screen", 0.40, 4.0, 6.0, "professional"),
                ("onsite_interview", "Onsite", 0.25, 2.5, 7.5, "professional"),
            ],
        },
        "seed": {
            "kind": "funnel",
            "n0": 40,
            "target": 1,
            "stages": [
                ("warm_intro", "Intro", 0.20, 2.0, 8.0, "professional"),
                ("first_meeting", "First meeting", 0.30, 3.0, 7.0, "professional"),
                ("partner_meeting", "Partner meeting", 0.15, 1.5, 8.5, "professional"),
            ],
        },
        "fitness": {
            "kind": "habit",
            "sessions": 60,
            "target": 36,
            "shot": ("gym_session", "Gym session", 0.60, 6.0, 4.0, "friends"),
        },
        "generic": {
            "kind": "funnel",
            "n0": 40,
            "target": 1,
            "stages": [
                ("outreach", "Outreach", 0.20, 2.0, 8.0, "professional"),
                ("meeting", "Meeting", 0.40, 4.0, 6.0, "professional"),
                ("close", "Close", 0.30, 3.0, 7.0, "professional"),
            ],
        },
    }

    def __init__(self, store: Store, llm: LLM | None = None) -> None:
        self.store = store
        self.llm = llm

    @staticmethod
    def detect_archetype(title: str) -> str:
        t = title.lower()
        if any(w in t for w in ("job", "interview", "hire", "offer", "recruit")):
            return "job"
        if any(w in t for w in ("seed", "raise", "fund", "investor", "round")):
            return "seed"
        if any(w in t for w in ("fit", "gym", "workout", "weight", "run", "health")):
            return "fitness"
        return "generic"

    def _ensure_shot_type(self, name: str, desc: str, mean: float, a: float, b: float, persona: Cluster) -> str:
        existing = self.store.list("shot_types", name=name)
        if existing:
            eid: str = existing[0]["id"]
            return eid
        st = ShotType(name=name, description=desc, alpha=a, beta=b, persona=persona)
        self.store.upsert("shot_types", st.model_dump())
        return st.id

    def decompose(self, goal: Goal, archetype: str | None = None) -> Goal:
        spec = None
        if archetype is None and self.llm is not None and self.llm.available:
            try:
                spec = _spec_from_llm(self._llm_decompose(goal))
            except Exception:
                logger.warning("LLM goal decomposition failed; using deterministic archetype", exc_info=True)
                spec = None  # any failure → deterministic archetype
        if spec is None:
            arch = archetype or self.detect_archetype(goal.title)
            spec = self.ARCHETYPES.get(arch, self.ARCHETYPES["generic"])
        return self._apply_spec(goal, spec)

    def _llm_decompose(self, goal: Goal) -> dict[str, Any]:
        if self.llm is None:  # only reached from decompose() under an availability guard
            raise RuntimeError("_llm_decompose called without an available LLM")
        sys = (
            "You are a planning strategist. Break a goal into either a realistic ordered "
            "conversion FUNNEL or a recurring HABIT, with grounded conversion rates. "
            "Respond with strict JSON only."
        )
        shape = (
            '{"kind":"funnel","stages":[{"name":"Apply","conversion":0.08,"persona":"professional"}],'
            '"n0_volume":60,"target_successes":1}  OR  '
            '{"kind":"habit","shot_name":"Gym session","adherence":0.6,'
            '"scheduled_sessions":60,"target_sessions":36,"persona":"friends"}'
        )
        usr = (
            f'Goal: "{goal.title}".\n'
            "Give 2-4 ordered funnel stages (each with a 0..1 per-stage conversion and a persona "
            "of professional|friends|family), a realistic starting volume, and a target count. "
            "Use a habit instead only for recurring fitness/health/practice goals.\n"
            f"JSON shape: {shape}"
        )
        return self.llm.chat_json(sys, usr, temperature=0.5, max_tokens=500)

    def _apply_spec(self, goal: Goal, spec: dict[str, Any]) -> Goal:
        from .models import Stage

        if spec["kind"] == "funnel":
            stages = []
            for order, (name, label, mean, a, b, persona) in enumerate(spec["stages"]):
                stid = self._ensure_shot_type(name, label, mean, a, b, persona)
                stages.append(Stage(name=label, shot_type_id=stid, order=order))
            goal.kind = "funnel"
            goal.stages = stages
            goal.shot_type_id = None
            if not goal.n0_volume:
                goal.n0_volume = spec["n0"]
            goal.target_successes = goal.target_successes or spec["target"]
        else:
            name, label, mean, a, b, persona = spec["shot"]
            stid = self._ensure_shot_type(name, label, mean, a, b, persona)
            goal.kind = "habit"
            goal.shot_type_id = stid
            goal.stages = []
            if not goal.target_sessions:
                goal.target_sessions = spec["target"]
            if not goal.n0_volume:
                goal.n0_volume = spec["sessions"]
        self.store.upsert("goals", goal.model_dump())
        return goal

    def build_queue(self) -> list[QueueItem]:
        goals = [Goal(**g) for g in self.store.list("goals")]
        today = date.today()
        candidates: list[dict[str, Any]] = []
        titles = {g.id: g.title for g in goals}

        for g in goals:
            if g.status not in ("active", "at_risk"):
                continue
            days = _days_until(g.deadline, today)
            if g.kind == "funnel" and g.stages:
                stages = _stage_priors(self.store, g)
                bn = E.find_bottleneck(g.n0_volume, stages, g.target_successes)
                ordered = sorted(g.stages, key=lambda s: s.order)
                stage = ordered[bn.stage_index] if bn.stage_index < len(ordered) else ordered[0]
                p_now = E.point_estimate_p(stages, g.n0_volume, g.target_successes)
                p_plus = E.point_estimate_p(stages, g.n0_volume + 1, g.target_successes)
                raw = self.store.get("shot_types", stage.shot_type_id)
                persona = raw.get("persona") if raw else None
                candidates.append(
                    {
                        "goal_id": g.id,
                        "shot_type_id": stage.shot_type_id,
                        "stage_id": stage.id,
                        "persona": persona,
                        "impact": g.impact,
                        "ltv": g.long_term_value,
                        "days_to_deadline": days,
                        "p_now": p_now,
                        "p_plus_one": p_plus,
                        "rationale": f"Bottleneck '{stage.name}' — one more shot moves the odds most.",
                    }
                )
            elif g.kind == "habit" and g.shot_type_id:
                prior = _habit_prior(self.store, g)
                n = _habit_sessions(g)
                p_now = E.point_estimate_p([prior], n, g.target_sessions)
                p_plus = E.point_estimate_p([prior], n + 1, g.target_sessions)
                raw = self.store.get("shot_types", g.shot_type_id)
                persona = raw.get("persona") if raw else None
                candidates.append(
                    {
                        "goal_id": g.id,
                        "shot_type_id": g.shot_type_id,
                        "stage_id": None,
                        "persona": persona,
                        "impact": g.impact,
                        "ltv": g.long_term_value,
                        "days_to_deadline": days,
                        "p_now": p_now,
                        "p_plus_one": p_plus,
                        "rationale": "One more session compounds adherence toward the target.",
                    }
                )

        # horizon 120d so multi-month life goals produce meaningful urgency separation
        ranked = E.rank_queue(candidates, horizon=120.0)
        return [
            QueueItem(
                shot_type_id=r.shot_type_id,
                goal_id=r.goal_id,
                goal_title=titles.get(r.goal_id, ""),
                stage_id=r.stage_id,
                persona=cast("Cluster | None", r.persona),
                score=r.score,
                impact=r.impact,
                urgency=r.urgency,
                long_term_value=r.ltv,
                marginal_p_gain=r.marginal_p_gain,
                rationale=r.rationale,
            )
            for r in ranked
        ]


class Persona:
    def __init__(self, store: Store, loader: PersonaLoader, llm: LLM | None = None) -> None:
        self.store = store
        self.loader = loader
        self.llm = llm

    def make_draft(
        self,
        shot_type_id: str,
        cluster: Cluster,
        context: dict[str, Any] | None = None,
        subcluster: str = "normal",
        seed: int | None = None,
        use_llm: bool | None = None,
    ) -> PersonaDraft:
        params = self.loader.get(cluster)
        ctx = dict(context or {})
        ctx.setdefault("shot_type_id", shot_type_id)
        raw = self.store.get("shot_types", shot_type_id)
        skeleton = ctx.get("skeleton") or _skeleton_for(raw["name"] if raw else "")

        llm_on = self.llm is not None and self.llm.available
        want_llm = llm_on if use_llm is None else (use_llm and llm_on)
        if want_llm and self.llm is not None:
            try:
                system = voice_system_prompt(params, self.loader.prose(cluster), subcluster)
                user = voice_user_prompt(skeleton, ctx)
                text = self.llm.chat(system, user, temperature=0.8, max_tokens=400)
                subject, body = split_subject(text)
                d = PersonaDraft(
                    shot_type_id=shot_type_id,
                    persona=cluster,
                    subject=subject,
                    body=body,
                    engine="llm",
                    params_used={
                        "cluster": cluster,
                        "subcluster": subcluster,
                        "shot_type": skeleton,
                        "model": self.llm.model,
                    },
                )
                self.store.upsert("drafts", d.model_dump())
                return d
            except Exception:
                logger.warning("LLM draft failed; falling back to the deterministic template", exc_info=True)

        if seed is None:
            seed = seed_from(ctx.get("goal_id"), ctx.get("stage_id"), ctx.get("contact_id"))
        d = draft_fn(skeleton, params, subcluster, ctx, seed)
        self.store.upsert("drafts", d.model_dump())
        return d


class Followup:
    def __init__(self, store: Store) -> None:
        self.store = store

    def due(self) -> list[FollowupModel]:
        today = date.today()
        goals = [Goal(**g) for g in self.store.list("goals")]
        outcomes = self.store.list("outcomes")
        out: list[FollowupModel] = []
        for g in goals:
            if g.status not in ("active", "at_risk"):
                continue
            g_outs = [o for o in outcomes if o["goal_id"] == g.id]
            default_shot = (
                sorted(g.stages, key=lambda s: s.order)[0].shot_type_id
                if g.kind == "funnel" and g.stages
                else g.shot_type_id
            )
            if not g_outs:
                out.append(
                    FollowupModel(
                        goal_id=g.id,
                        goal_title=g.title,
                        shot_type_id=default_shot or "",
                        stage_id=None,
                        due_in_days=0,
                        reason="No shots logged yet — take the first one.",
                        last_outcome_at=None,
                    )
                )
                continue
            last = max(g_outs, key=lambda o: o["logged_at"])
            days_since = (today - _to_date(last["logged_at"])).days
            if days_since >= 3:
                out.append(
                    FollowupModel(
                        goal_id=g.id,
                        goal_title=g.title,
                        shot_type_id=last["shot_type_id"],
                        stage_id=last.get("stage_id"),
                        due_in_days=max(0, 5 - days_since),
                        reason=f"No new results in {days_since} days — keep the thread alive.",
                        last_outcome_at=last["logged_at"],
                    )
                )
        return out


class Wellbeing:
    def __init__(self, store: Store) -> None:
        self.store = store

    def report(self) -> WellbeingReport:
        today = date.today()
        goals = [Goal(**g) for g in self.store.list("goals")]
        outcomes = self.store.list("outcomes")

        recent = [o for o in outcomes if (today - _to_date(o["logged_at"])).days <= 7]
        momentum = min(len(recent) / 5.0, 1.0)

        days_with = {_to_date(o["logged_at"]) for o in outcomes}
        streak = 0
        cursor = today
        from datetime import timedelta

        while cursor in days_with:
            streak += 1
            cursor = cursor - timedelta(days=1)

        active = [g for g in goals if g.status in ("active", "at_risk")]
        at_risk = [
            g.id
            for g in active
            if g.last_sim and g.last_sim.p_success < g.threshold and _days_until(g.deadline, today) <= 30
        ]

        load: Literal["light", "steady", "heavy"]
        if len(at_risk) >= 2 or len(active) > 3:
            load = "heavy"
        elif len(active) >= 2:
            load = "steady"
        else:
            load = "light"

        if momentum < 0.2 and load == "heavy":
            message = "Heavy load and low recent activity — throttle volume and protect recovery before pushing."
        elif at_risk:
            message = f"{len(at_risk)} goal(s) trending below target near the deadline — point the queue there."
        elif streak >= 3:
            message = f"{streak}-day logging streak — momentum is building. Keep the cadence."
        else:
            message = "Steady. Log a shot today to keep the model sharp."

        return WellbeingReport(
            momentum=momentum,
            streak_days=streak,
            load=load,
            at_risk_goals=at_risk,
            message=message,
        )


class Advisor:
    """Scenario advice — answers a free-text question as a sharper version of the user,
    grounded in their goals + forecasts + persona voice. LLM-backed; offline returns a note."""

    def __init__(self, store: Store, loader: PersonaLoader, llm: LLM | None = None) -> None:
        self.store = store
        self.loader = loader
        self.llm = llm

    def _grounding(self, focus: Goal | None) -> str:
        goals = [Goal(**g) for g in self.store.list("goals")]
        lines = []
        for g in goals:
            p = g.last_sim.p_success if g.last_sim else None
            ptxt = f"{p:.0%}" if p is not None else "n/a"
            tag = "  <-- FOCUS" if focus and g.id == focus.id else ""
            lines.append(
                f"- {g.title} [{g.kind}] odds {ptxt} vs target {g.threshold:.0%}, "
                f"deadline {g.deadline}, status {g.status}{tag}"
            )
        return "\n".join(lines) or "(no goals yet)"

    def advise(self, question: str, goal: Goal | None = None, cluster: str = "professional") -> dict[str, Any]:
        if self.llm is None or not self.llm.available:
            return {
                "available": False,
                "answer": "Scenario advice needs an OpenAI key (set OPENAI_API_KEY in .env). "
                "Forecasting, the priority queue, and template drafting all work offline.",
                "model": None,
            }
        system = (
            "You are a sharper, calmer version of the USER — their decision co-pilot. "
            "Answer in the first person, grounded ONLY in the data provided. Be concrete, cite the "
            "odds/numbers, and be honest when a plan is weak. 4-8 sentences. Voice notes:\n"
            + self.loader.prose(cluster).strip()
        )
        user = f"My goals and current forecasts:\n{self._grounding(goal)}\n\nQuestion: {question}"
        try:
            answer = self.llm.chat(system, user, temperature=0.6, max_tokens=500)
        except Exception as e:
            logger.warning("LLM scenario advice failed", exc_info=True)
            return {
                "available": True,
                "answer": f"(LLM error: {type(e).__name__}) — try again.",
                "model": self.llm.model,
            }
        return {"available": True, "answer": answer, "model": self.llm.model}
