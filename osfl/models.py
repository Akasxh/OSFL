"""All OSFL domain models + request/response DTOs (pydantic v2).

This is the single source of types — store, engine adapters, agents, and the API all
import from here. Engine modules themselves stay model-free (pure numpy) and the agent
layer converts engine dataclasses into these models.
"""

from __future__ import annotations

import secrets
import time
from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

Cluster = Literal["professional", "friends", "family"]
Subcluster = Literal["close", "normal", "acquaintance"]


def new_id() -> str:
    """Short, time-sortable id: hex(ms) + 6 random hex chars."""
    ms = int(time.time() * 1000)
    return f"{ms:011x}{secrets.token_hex(3)}"


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _as_iso_date(v: str) -> str:
    """Reject a non-ISO deadline at the boundary (422) instead of failing deep in an agent (500)."""
    try:
        date.fromisoformat(v[:10])
    except ValueError as err:
        raise ValueError("deadline must be an ISO date (YYYY-MM-DD)") from err
    return v


class _StrictModel(BaseModel):
    """Base for request DTOs: reject unknown/typo'd fields instead of silently dropping them."""

    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- #
# Core domain
# --------------------------------------------------------------------------- #
class ShotType(BaseModel):
    """A reusable conversion primitive (cold_email, gym_session).

    Carries the population Beta prior AND the per-user posterior. The pair
    (alpha,beta) vs (user_alpha,user_beta) IS the 'your rate vs population rate' demo.
    """

    id: str = Field(default_factory=new_id)
    name: str
    description: str = ""
    alpha: float = Field(default=1.0, gt=0.0)
    beta: float = Field(default=1.0, gt=0.0)
    user_alpha: float | None = Field(default=None, gt=0.0)
    user_beta: float | None = Field(default=None, gt=0.0)
    persona: Cluster | None = None

    def effective_prior(self) -> tuple[float, float]:
        """User posterior if it exists, else the population prior."""
        if self.user_alpha is not None and self.user_beta is not None:
            return (self.user_alpha, self.user_beta)
        return (self.alpha, self.beta)

    def prior_mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def effective_mean(self) -> float:
        a, b = self.effective_prior()
        return a / (a + b)


class Stage(BaseModel):
    """One funnel step embedded in a funnel Goal (cascade-deletes with the goal)."""

    id: str = Field(default_factory=new_id)
    name: str
    shot_type_id: str
    order: int = 0


class SimulationResult(BaseModel):
    """Cached output of one Monte-Carlo run; embedded on goal.last_sim."""

    goal_id: str
    runs: int = 10000
    seed: int | None = None
    p_success: float = 0.0
    mean_final: float = 0.0
    median_final: float = 0.0
    p10: float = 0.0
    p50: float = 0.0
    p90: float = 0.0
    hist_bins: list[int] = Field(default_factory=list)
    hist_edges: list[float] = Field(default_factory=list)
    per_stage_drop: list[float] | None = None
    target: int = 1
    computed_at: str = Field(default_factory=utcnow_iso)


class Goal(BaseModel):
    """Discriminated on kind (funnel|habit). Holds an embedded last_sim cache."""

    id: str = Field(default_factory=new_id)
    title: str
    kind: Literal["funnel", "habit"] = "funnel"
    threshold: float = 0.7
    deadline: str  # ISO date
    created_at: str = Field(default_factory=utcnow_iso)
    status: Literal["active", "met", "at_risk", "archived"] = "active"
    impact: float = 0.5  # 0..1 — how much this goal matters
    long_term_value: float = 0.5  # 0..1 — durable value weight

    # funnel
    stages: list[Stage] = Field(default_factory=list)
    n0_volume: int = 0
    target_successes: int = 1

    # habit
    shot_type_id: str | None = None
    target_sessions: int = 0
    horizon_days: int = 0

    last_sim: SimulationResult | None = None


class Shot(BaseModel):
    """A planned/suggested action surfaced by the queue."""

    id: str = Field(default_factory=new_id)
    goal_id: str
    stage_id: str | None = None
    shot_type_id: str
    persona: Cluster | None = None
    status: Literal["suggested", "drafted", "sent"] = "suggested"
    created_at: str = Field(default_factory=utcnow_iso)
    draft_id: str | None = None


class Outcome(BaseModel):
    """Immutable logged evidence; drives the conjugate Bayesian update."""

    id: str = Field(default_factory=new_id)
    goal_id: str
    shot_type_id: str
    stage_id: str | None = None
    n_attempts: int
    k_successes: int
    logged_at: str = Field(default_factory=utcnow_iso)
    note: str | None = None

    @field_validator("k_successes")
    @classmethod
    def _k_le_n(cls, v: int, info: ValidationInfo) -> int:
        n = info.data.get("n_attempts")
        if n is not None and not (0 <= v <= n):
            raise ValueError("k_successes must satisfy 0 <= k <= n_attempts")
        return v


class PersonaDraft(BaseModel):
    """Output of the drafter (deterministic template or LLM); persisted so the UI can re-show."""

    id: str = Field(default_factory=new_id)
    shot_type_id: str
    persona: Cluster
    subject: str | None = None
    body: str
    engine: Literal["template", "llm"] = "template"
    params_used: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=utcnow_iso)


class PersonaParams(BaseModel):
    """Parsed YAML front-matter of a persona/*.md file."""

    cluster: Cluster
    display_name: str
    formality: float = 0.5
    warmth: float = 0.5
    directness: float = 0.5
    emoji_rate: float = 0.0
    emoji_palette: list[str] = Field(default_factory=list)
    avg_len: int = 40
    length_tolerance: float = 0.2
    greetings: dict[str, list[str]] = Field(default_factory=dict)
    signoffs: dict[str, list[str]] = Field(default_factory=dict)
    dos: list[str] = Field(default_factory=list)
    donts: list[str] = Field(default_factory=list)
    reactions: dict[str, str] = Field(default_factory=dict)
    banned_words: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Derived / report models (never persisted)
# --------------------------------------------------------------------------- #
class QueueItem(BaseModel):
    shot_type_id: str
    goal_id: str
    goal_title: str = ""
    stage_id: str | None = None
    persona: Cluster | None = None
    score: float = 0.0
    impact: float = 0.0
    urgency: float = 0.0
    long_term_value: float = 0.0
    marginal_p_gain: float = 0.0
    rationale: str = ""


class Suggestion(BaseModel):
    kind: Literal["more_volume", "extend_deadline", "better_shot_type"]
    detail: str
    projected_p: float


class ValidationReport(BaseModel):
    goal_id: str
    passed: bool
    p_success: float
    threshold: float
    bottleneck_stage_id: str | None = None
    bottleneck_reason: str = ""
    min_volume_for_threshold: int | None = None
    suggestions: list[Suggestion] = Field(default_factory=list)


class AgentStep(BaseModel):
    name: str
    action: str
    output_summary: str
    elapsed_ms: int


class OrchestratorTrace(BaseModel):
    request: str
    cluster: str
    agents: list[AgentStep] = Field(default_factory=list)
    result: dict = Field(default_factory=dict)
    elapsed_ms: int = 0


class WellbeingReport(BaseModel):
    momentum: float
    streak_days: int
    load: Literal["light", "steady", "heavy"]
    at_risk_goals: list[str] = Field(default_factory=list)
    message: str


class Followup(BaseModel):
    goal_id: str
    goal_title: str = ""
    shot_type_id: str
    stage_id: str | None = None
    due_in_days: int
    reason: str
    last_outcome_at: str | None = None


# --------------------------------------------------------------------------- #
# Request DTOs
# --------------------------------------------------------------------------- #
class GoalCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=200)
    kind: Literal["funnel", "habit"] = "funnel"
    deadline: str
    threshold: float = Field(default=0.7, ge=0.0, le=0.999)
    impact: float = Field(default=0.5, ge=0.0, le=1.0)
    long_term_value: float = Field(default=0.5, ge=0.0, le=1.0)
    n0_volume: int = Field(default=0, ge=0, le=1_000_000)
    target_successes: int = Field(default=1, ge=1, le=10_000)
    shot_type_id: str | None = None
    target_sessions: int = Field(default=0, ge=0, le=100_000)
    horizon_days: int = Field(default=0, ge=0, le=100_000)

    @field_validator("deadline")
    @classmethod
    def _iso_deadline(cls, v: str) -> str:
        return _as_iso_date(v)


class GoalPatch(_StrictModel):
    n0_volume: int | None = Field(default=None, ge=0, le=1_000_000)
    deadline: str | None = None
    target_successes: int | None = Field(default=None, ge=1, le=10_000)
    threshold: float | None = Field(default=None, ge=0.0, le=0.999)
    target_sessions: int | None = Field(default=None, ge=0, le=100_000)
    status: Literal["active", "met", "at_risk", "archived"] | None = None

    @field_validator("deadline")
    @classmethod
    def _iso_deadline(cls, v: str | None) -> str | None:
        return _as_iso_date(v) if v is not None else v


class OutcomeCreate(_StrictModel):
    shot_type_id: str
    stage_id: str | None = None
    n_attempts: int = Field(ge=0, le=1_000_000)
    k_successes: int = Field(ge=0, le=1_000_000)
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("k_successes")
    @classmethod
    def _k_le_n(cls, v: int, info: ValidationInfo) -> int:
        n = info.data.get("n_attempts")
        if n is not None and not (0 <= v <= n):
            raise ValueError("k_successes must satisfy 0 <= k <= n_attempts")
        return v


class SimRequest(_StrictModel):
    runs: int = Field(default=10000, ge=1, le=1_000_000)
    seed: int | None = None


class DraftRequest(_StrictModel):
    shot_type_id: str
    persona: Cluster
    subcluster: Subcluster = "normal"
    context: dict = Field(default_factory=dict)
    seed: int | None = None
    use_llm: bool | None = None  # None = auto (LLM if a key is configured)


class OrchestrateRequest(_StrictModel):
    request: str = Field(min_length=1, max_length=2000)
    goal_id: str | None = None


class AdviseRequest(_StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    goal_id: str | None = None
    persona: Cluster = "professional"
