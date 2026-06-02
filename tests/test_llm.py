"""The LLM layer is optional: with no key, every language agent falls back deterministically.

These tests never hit the network — they remove the key (so LLM.available is False) or force
the template path, exercising only the offline branches.
"""

from osfl.agents import Advisor, Persona, Planner
from osfl.llm import LLM
from osfl.models import Goal
from osfl.persona.loader import PersonaLoader
from osfl.seed import seed_store
from osfl.store import Store

LOADER = PersonaLoader("personas")


def _offline(monkeypatch) -> LLM:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return LLM()


def test_llm_unavailable_without_key(monkeypatch):
    assert _offline(monkeypatch).available is False


def test_persona_falls_back_to_template(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "s.json"))
    seed_store(store)
    cold = store.list("shot_types", name="cold_email")[0]
    d = Persona(store, LOADER, _offline(monkeypatch)).make_draft(
        cold["id"], "professional", {"name": "Sam", "role": "SWE"}
    )
    assert d.engine == "template" and d.body


def test_use_llm_false_forces_template(tmp_path):
    # even if a key is present, use_llm=False must use the deterministic template (no network)
    store = Store(str(tmp_path / "s.json"))
    seed_store(store)
    cold = store.list("shot_types", name="cold_email")[0]
    d = Persona(store, LOADER, LLM()).make_draft(cold["id"], "friends", {"name": "Sam"}, use_llm=False)
    assert d.engine == "template"


def test_advisor_offline_message(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "s.json"))
    seed_store(store)
    r = Advisor(store, LOADER, _offline(monkeypatch)).advise("what next?")
    assert r["available"] is False and "OPENAI_API_KEY" in r["answer"]


def test_planner_uses_archetype_without_llm(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "s.json"))
    g = Goal(title="land a job at a startup", deadline="2026-12-01")
    Planner(store, _offline(monkeypatch)).decompose(g)
    assert g.kind == "funnel" and len(g.stages) == 3  # job archetype, deterministic
