"""Idempotent seeding: three demo goals with illustrative priors, created once.

Guarded by meta.seed_loaded so a restart never duplicates. The job funnel uses the same
0.08 → 0.40 → 0.25 conversion rates the engine tests exercise, so the dashboard's headline
numbers reproduce — but these priors are hand-picked illustrative defaults, not fitted to data.
"""

from __future__ import annotations

from datetime import date, timedelta

from .models import Cluster, Goal, ShotType, Stage
from .store import Store


def _shot_type(store: Store, name: str, desc: str, a: float, b: float, persona: Cluster) -> str:
    st = ShotType(name=name, description=desc, alpha=a, beta=b, persona=persona)
    store.upsert("shot_types", st.model_dump())
    return st.id


def seed_store(store: Store) -> None:
    if store.meta.get("seed_loaded"):
        return
    today = date.today()

    # --- Land a job (funnel): 0.08 -> 0.40 -> 0.25, the headline demo ---------
    apply_id = _shot_type(store, "cold_email", "Cold application email to a target role", 2.0, 23.0, "professional")
    screen_id = _shot_type(store, "recruiter_screen", "Recruiter screen → onsite conversion", 4.0, 6.0, "professional")
    onsite_id = _shot_type(store, "onsite_interview", "Onsite → offer conversion", 2.5, 7.5, "professional")
    job = Goal(
        title="Land a job",
        kind="funnel",
        threshold=0.7,
        impact=0.9,
        long_term_value=0.9,
        deadline=(today + timedelta(days=60)).isoformat(),
        n0_volume=60,
        target_successes=1,
        stages=[
            Stage(name="Apply", shot_type_id=apply_id, order=0),
            Stage(name="Screen", shot_type_id=screen_id, order=1),
            Stage(name="Onsite", shot_type_id=onsite_id, order=2),
        ],
    )
    store.upsert("goals", job.model_dump())

    # --- Raise a seed round (funnel): smaller starting volume (n0=40) ---------
    intro_id = _shot_type(store, "warm_intro", "Warm intro request to an investor", 2.0, 8.0, "professional")
    fm_id = _shot_type(store, "first_meeting", "Intro → first meeting", 3.0, 7.0, "professional")
    pm_id = _shot_type(
        store, "partner_meeting", "First meeting → partner meeting / term sheet", 1.5, 8.5, "professional"
    )
    seed = Goal(
        title="Raise a seed round",
        kind="funnel",
        threshold=0.7,
        impact=0.8,
        long_term_value=0.7,
        deadline=(today + timedelta(days=56)).isoformat(),
        n0_volume=40,
        target_successes=1,
        stages=[
            Stage(name="Intro", shot_type_id=intro_id, order=0),
            Stage(name="First meeting", shot_type_id=fm_id, order=1),
            Stage(name="Partner", shot_type_id=pm_id, order=2),
        ],
    )
    store.upsert("goals", seed.model_dump())

    # --- Get fit (habit): adherence Beta(6,4) ~0.60, 36 of ~60 sessions ------
    gym_id = _shot_type(store, "gym_session", "Scheduled gym session adherence", 6.0, 4.0, "friends")
    fit = Goal(
        title="Get fit",
        kind="habit",
        threshold=0.7,
        impact=0.6,
        long_term_value=1.0,
        deadline=(today + timedelta(days=91)).isoformat(),
        shot_type_id=gym_id,
        target_sessions=36,
        n0_volume=60,  # scheduled sessions
        horizon_days=91,
    )
    store.upsert("goals", fit.model_dump())

    store.set_meta("seed_loaded", True)
