"""Live LLM ('digital twin') behaviour — the headline feature.

Skipped by default (the committed suite is offline/deterministic). Run explicitly with:
    uv run --extra dev pytest tests/test_llm_live.py --run-llm -q
These hit the real OpenAI API using the key in .env (conftest forces the offline empty key, so
each test restores the real key via monkeypatch).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.llm

_GLYPHS = "😂🔥❤️😊🙏👍🙌👀🎉"


def _real_key() -> str | None:
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY=") and line.split("=", 1)[1].strip():
                return line.split("=", 1)[1].strip()
    return None


@pytest.fixture
def live_llm(monkeypatch):
    key = _real_key()
    if not key:
        pytest.skip("no OPENAI_API_KEY in .env")
    monkeypatch.setenv("OPENAI_API_KEY", key)
    from osfl.llm import LLM

    llm = LLM()
    assert llm.available, "LLM should be available with a real key"
    return llm


def _seeded_store():
    from osfl.seed import seed_store
    from osfl.store import Store

    store = Store(str(Path(tempfile.mkdtemp()) / "osfl_live.json"))
    seed_store(store)
    return store


def test_llm_chat_roundtrip(live_llm):
    out = live_llm.chat("Reply with exactly: OSFL", "go", temperature=0, max_tokens=8)
    assert "OSFL" in out


def test_persona_llm_draft_is_you_voiced_and_emoji_free(live_llm):
    from osfl.agents import Persona
    from osfl.persona.loader import PersonaLoader

    store = _seeded_store()
    cold = store.list("shot_types", name="cold_email")[0]
    d = Persona(store, PersonaLoader("personas"), live_llm).make_draft(
        cold["id"], "professional", {"name": "Dana", "role": "Staff Engineer", "company": "Acme"}
    )
    assert d.engine == "llm"
    assert len(d.body) > 30
    assert all(g not in d.body for g in _GLYPHS)  # professional voice = no emoji
    assert d.params_used.get("model")


def test_advisor_live_is_grounded(live_llm):
    from osfl.agents import Advisor, Simulator
    from osfl.models import Goal
    from osfl.persona.loader import PersonaLoader

    store = _seeded_store()
    job = next(Goal(**g) for g in store.list("goals") if g["title"] == "Land a job")
    Simulator(store).run(job, seed=42)  # populate last_sim so advice can cite odds
    res = Advisor(store, PersonaLoader("personas"), live_llm).advise(
        "Is my job search on track and what should I do this week?", job
    )
    assert res["available"] is True
    assert len(res["answer"]) > 40
    assert res["model"]


def test_planner_llm_decomposes_novel_goal(live_llm):
    from osfl.agents import Planner
    from osfl.models import Goal

    store = _seeded_store()
    g = Goal(title="get my first novel published", deadline="2026-12-31")
    Planner(store, live_llm).decompose(g)
    assert g.kind in ("funnel", "habit")
    if g.kind == "funnel":
        assert len(g.stages) >= 2  # LLM produced a real multi-stage funnel
        assert g.n0_volume >= 1
