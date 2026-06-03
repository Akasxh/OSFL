"""Priority queue math: one ranked next-shot across all goals.

score = impact * urgency * long_term_value * marginal_p_gain   (all in [0,1])

marginal_p_gain is normalized ACROSS the candidate list so the most-leveraged shot anchors
at 1.0 — otherwise tiny absolute +1-shot deltas would crush every score toward zero.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RankedShot:
    goal_id: str
    stage_id: str | None
    shot_type_id: str
    persona: str | None
    score: float
    impact: float
    urgency: float
    ltv: float
    marginal_p_gain: float
    rationale: str


def marginal_p_gain(p_now: float, p_plus_one: float) -> float:
    return max(p_plus_one - p_now, 0.0)


def urgency_factor(days_to_deadline: float, horizon: float = 60.0) -> float:
    if horizon <= 0:  # no horizon to discount against → treat as maximally urgent
        return 1.0
    return float(min(max(1.0 - days_to_deadline / horizon, 0.05), 1.0))


def shot_score(impact: float, urgency: float, ltv: float, mpg_norm: float) -> float:
    return impact * urgency * ltv * mpg_norm


def rank_queue(candidates: list[dict], horizon: float = 60.0) -> list[RankedShot]:
    """Each candidate dict supplies: goal_id, shot_type_id, impact, ltv, days_to_deadline,
    p_now, p_plus_one, and optionally stage_id, persona, rationale."""
    raw = [marginal_p_gain(c["p_now"], c["p_plus_one"]) for c in candidates]
    mx = max(raw) if raw else 0.0
    out: list[RankedShot] = []
    for c, r in zip(candidates, raw, strict=True):
        mpg_norm = (r / mx) if mx > 0 else 0.0
        urg = urgency_factor(c["days_to_deadline"], horizon)
        out.append(
            RankedShot(
                goal_id=c["goal_id"],
                stage_id=c.get("stage_id"),
                shot_type_id=c["shot_type_id"],
                persona=c.get("persona"),
                score=shot_score(c["impact"], urg, c["ltv"], mpg_norm),
                impact=c["impact"],
                urgency=urg,
                ltv=c["ltv"],
                marginal_p_gain=mpg_norm,
                rationale=c.get("rationale", ""),
            )
        )
    out.sort(key=lambda x: x.score, reverse=True)
    return out
