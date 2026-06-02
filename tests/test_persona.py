"""Persona layer: parsing, determinism, voice differentiation, lint, and safe fallbacks."""

import re

from osfl.persona.drafter import draft
from osfl.persona.loader import PersonaLoader

LOADER = PersonaLoader("personas")
GLYPHS = "😂🙌🔥👀🎉❤️😊🙏👍"


def test_all_clusters_parse():
    params = LOADER.all()
    assert set(params) == {"professional", "friends", "family"}
    assert params["professional"].emoji_rate == 0.0
    assert params["friends"].emoji_palette  # non-empty


def test_same_seed_identical():
    p = LOADER.get("friends")
    ctx = {"name": "Sam", "topic": "the thing", "shot_type_id": "x"}
    a = draft("followup", p, "close", ctx, 123)
    b = draft("followup", p, "close", ctx, 123)
    assert a.body == b.body and a.subject == b.subject


def test_professional_emoji_free():
    p = LOADER.get("professional")
    for seed in range(50):
        d = draft("apply", p, "normal", {"name": "Sam", "role": "SWE", "company": "Acme"}, seed)
        assert all(g not in d.body for g in GLYPHS)


def test_banned_words_stripped():
    p = LOADER.get("friends")  # bans dear/sincerely/regards/kindly/...
    d = draft("ask", p, "normal", {"name": "Sam", "topic": "regards kindly please find it"}, 7)
    for w in p.banned_words:
        assert not re.search(rf"\b{re.escape(w)}\b", d.body, re.IGNORECASE)


def test_unknown_shot_type_falls_back():
    p = LOADER.get("professional")
    d = draft("NONEXISTENT_SKELETON", p, "normal", {"name": "Sam"}, 1)
    assert d.body  # falls back to the 'ask' skeleton, no crash


def test_empty_context_no_crash():
    p = LOADER.get("family")
    d = draft("followup", p, "normal", {}, 1)
    assert d.body


def test_three_clusters_visibly_differ():
    ctx = {"name": "Sam", "topic": "the deck", "shot_type_id": "x"}
    bodies = {c: draft("followup", LOADER.get(c), "close", ctx, 5).body for c in ("professional", "friends", "family")}
    assert len(set(bodies.values())) == 3
