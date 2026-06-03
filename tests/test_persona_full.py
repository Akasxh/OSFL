"""Pure persona/twin suite — PersonaLoader, the deterministic drafter, and the voice
prompt builders. No FastAPI app, no store, no network, no LLM. Everything here exercises
the real osfl.persona.* code against the committed personas/*.md files.

Grounded in:
  - osfl/persona/loader.py   (PersonaLoader: parse YAML front-matter -> PersonaParams)
  - osfl/persona/drafter.py  (draft(): deterministic offline 'you-voiced' templating)
  - osfl/persona/voice.py    (voice_system_prompt / voice_user_prompt / split_subject)
  - osfl/models.py           (PersonaParams field set)
  - personas/{professional,friends,family}.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from osfl.models import PersonaParams
from osfl.persona.drafter import SKELETONS, draft
from osfl.persona.loader import CLUSTERS, PersonaLoader
from osfl.persona.voice import split_subject, voice_system_prompt, voice_user_prompt

# Resolve personas/ relative to the repo root (tests/ -> repo root) so the suite does not
# depend on the process working directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_PERSONAS_DIR = _REPO_ROOT / "personas"

# Every emoji glyph used by any persona palette — for the professional emoji-free sweep.
_ALL_GLYPHS = "😂🙌🔥👀🎉❤️😊🙏👍"

# All shot-type skeletons the drafter knows about.
_ALL_SKELETONS = sorted(SKELETONS.keys())


@pytest.fixture(scope="module")
def loader() -> PersonaLoader:
    return PersonaLoader(str(_PERSONAS_DIR))


# --------------------------------------------------------------------------- #
# Loader: all 3 clusters parse with every PersonaParams field present.
# --------------------------------------------------------------------------- #
def test_loader_exposes_exactly_the_three_clusters(loader: PersonaLoader):
    parsed = loader.all()
    assert set(parsed.keys()) == set(CLUSTERS) == {"professional", "friends", "family"}


@pytest.mark.parametrize("cluster", ["professional", "friends", "family"])
def test_every_cluster_parses_all_personaparams_fields(loader: PersonaLoader, cluster: str):
    """Each persona file must populate every field declared on PersonaParams, not just
    accept defaults. This proves the YAML front-matter is fully wired, not half-parsed."""
    p = loader.get(cluster)
    assert isinstance(p, PersonaParams)

    # cluster identity round-trips from the file
    assert p.cluster == cluster
    assert isinstance(p.display_name, str) and p.display_name.strip()

    # scalar style knobs are real floats in [0, 1]
    for knob in (p.formality, p.warmth, p.directness, p.emoji_rate):
        assert isinstance(knob, float)
        assert 0.0 <= knob <= 1.0

    assert isinstance(p.avg_len, int) and p.avg_len > 0
    assert isinstance(p.length_tolerance, float) and p.length_tolerance >= 0.0

    # every persona file ships all three relationship registers for greetings + signoffs
    assert set(p.greetings.keys()) == {"close", "normal", "acquaintance"}
    assert set(p.signoffs.keys()) == {"close", "normal", "acquaintance"}
    for register in ("close", "normal", "acquaintance"):
        assert p.greetings[register] and all(isinstance(g, str) for g in p.greetings[register])
        assert p.signoffs[register] and all(isinstance(s, str) for s in p.signoffs[register])

    # list / dict guidance fields are non-empty and well-typed in every file
    assert p.dos and all(isinstance(x, str) for x in p.dos)
    assert p.donts and all(isinstance(x, str) for x in p.donts)
    assert p.banned_words and all(isinstance(x, str) for x in p.banned_words)
    assert p.reactions and all(isinstance(k, str) and isinstance(v, str) for k, v in p.reactions.items())

    # the emoji palette must be consistent with the rate: zero rate => empty palette and vice-versa
    assert isinstance(p.emoji_palette, list)
    if p.emoji_rate == 0.0:
        assert p.emoji_palette == []
    else:
        assert p.emoji_palette


def test_known_pinned_param_values(loader: PersonaLoader):
    """Lock the headline numbers from the committed files so a silent edit is caught."""
    pro, fr, fam = loader.get("professional"), loader.get("friends"), loader.get("family")
    assert (pro.formality, pro.warmth, pro.directness, pro.emoji_rate) == (0.85, 0.40, 0.80, 0.0)
    assert (fr.formality, fr.warmth, fr.directness, fr.emoji_rate) == (0.25, 0.80, 0.55, 0.6)
    assert (fam.formality, fam.warmth, fam.directness, fam.emoji_rate) == (0.45, 0.95, 0.45, 0.35)


def test_unknown_cluster_raises(loader: PersonaLoader):
    with pytest.raises(ValueError):
        loader.get("strangers")


# --------------------------------------------------------------------------- #
# Drafter: byte-identical determinism for the same inputs, across ALL skeletons.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("skeleton", _ALL_SKELETONS)
@pytest.mark.parametrize("cluster", ["professional", "friends", "family"])
def test_drafter_is_byte_identical_for_same_inputs(loader: PersonaLoader, cluster: str, skeleton: str):
    """draft() must be a pure function of (skeleton, params, subcluster, context, seed).
    Same inputs -> byte-identical subject AND body, for every cluster x every skeleton."""
    p = loader.get(cluster)
    ctx = {
        "name": "Sam", "role": "Engineer", "company": "Acme", "topic": "the proposal",
        "when": "Tuesday", "pitch": "I shipped two launches last quarter.", "me": "Alex",
        "goal": "your run", "progress": "halfway", "target": "10k", "reason": "the intro",
        "shot_type_id": "st_x",
    }
    a = draft(skeleton, p, "close", ctx, 4242)
    b = draft(skeleton, p, "close", dict(ctx), 4242)
    assert a.body == b.body
    assert a.subject == b.subject
    assert a.params_used == b.params_used


@pytest.mark.parametrize("skeleton", _ALL_SKELETONS)
def test_changing_seed_can_change_output_but_stays_pure(loader: PersonaLoader, skeleton: str):
    """A different seed re-rolls greeting/sign-off/emoji picks; re-running the SAME new seed
    is still byte-identical (purity), so determinism is per-seed, not global state."""
    p = loader.get("friends")
    ctx = {"name": "Sam", "topic": "the trip", "role": "X", "company": "Y",
           "pitch": "yo", "me": "Alex", "shot_type_id": "x"}
    s1a = draft(skeleton, p, "close", ctx, 1)
    s1b = draft(skeleton, p, "close", ctx, 1)
    s2 = draft(skeleton, p, "close", ctx, 999)
    assert s1a.body == s1b.body  # same seed => identical
    # We don't require every seed to differ (small option sets can collide), but purity holds.
    assert isinstance(s2.body, str) and s2.body


def test_email_skeletons_emit_subject_and_non_email_do_not(loader: PersonaLoader):
    """The skeleton table marks apply/intro/followup as email (subject present); ask/thanks/
    habit_nudge are not. The draft.subject field must reflect that flag."""
    p = loader.get("professional")
    ctx = {"name": "Sam", "role": "SWE", "company": "Acme", "topic": "the deck",
           "me": "Alex", "shot_type_id": "x"}
    for sk in ("apply", "intro", "followup"):
        d = draft(sk, p, "normal", ctx, 3)
        assert d.subject, f"{sk} should carry a subject"
    for sk in ("ask", "thanks", "habit_nudge"):
        d = draft(sk, p, "normal", ctx, 3)
        assert d.subject is None, f"{sk} should not carry a subject"


# --------------------------------------------------------------------------- #
# Drafter: cluster voices are visibly distinct from one skeleton.
# --------------------------------------------------------------------------- #
def test_three_clusters_produce_distinct_bodies_from_one_skeleton(loader: PersonaLoader):
    ctx = {"name": "Sam", "topic": "the deck", "when": "last week", "shot_type_id": "x"}
    bodies = {c: draft("followup", loader.get(c), "close", ctx, 5).body for c in CLUSTERS}
    # all three are non-empty and pairwise different
    assert all(b.strip() for b in bodies.values())
    assert len(set(bodies.values())) == 3


def test_friends_voice_is_casual_professional_is_formal(loader: PersonaLoader):
    """Prove the differentiation runs in the intended direction ROBUSTLY (across seeds, not a
    lucky one): professional always opens with a formal greeting (Hi/Hello/Dear), friends never
    does, and the params encode the casual<->formal axis."""
    fr_p, pro_p = loader.get("friends"), loader.get("professional")
    assert fr_p.formality < pro_p.formality
    assert fr_p.emoji_rate > pro_p.emoji_rate
    ctx = {"name": "Sam", "topic": "the deck", "shot_type_id": "x"}
    FORMAL = ("Hi ", "Hi,", "Hello", "Dear")
    for seed in range(20):
        fr = draft("ask", fr_p, "close", ctx, seed).body
        pro = draft("ask", pro_p, "close", ctx, seed).body
        assert fr != pro
        assert pro.startswith(FORMAL), f"professional greeting not formal at seed={seed}: {pro[:20]!r}"
        assert not fr.startswith(FORMAL), f"friends greeting looks formal at seed={seed}: {fr[:20]!r}"


# --------------------------------------------------------------------------- #
# Drafter: professional is emoji-free across a seed sweep.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("skeleton", _ALL_SKELETONS)
def test_professional_is_emoji_free_over_seed_sweep(loader: PersonaLoader, skeleton: str):
    p = loader.get("professional")
    ctx = {"name": "Sam", "role": "SWE", "company": "Acme", "topic": "the deck",
           "me": "Alex", "goal": "run", "shot_type_id": "x"}
    for seed in range(40):
        d = draft(skeleton, p, "normal", ctx, seed)
        assert all(g not in d.body for g in _ALL_GLYPHS), f"emoji leaked at seed={seed}"
        if d.subject:
            assert all(g not in d.subject for g in _ALL_GLYPHS)


# --------------------------------------------------------------------------- #
# Drafter: banned words injected via a context slot are linted out.
# --------------------------------------------------------------------------- #
def test_banned_words_injected_via_context_slot_are_stripped(loader: PersonaLoader):
    """A user-supplied context value can smuggle a banned word into the body; the lint pass
    must remove every banned word (whole-word, case-insensitive) while keeping other text."""
    p = loader.get("friends")  # bans: dear, sincerely, regards, kindly, "please find", "per my"
    payload = "Dear team, sincerely Regards kindly KINDLY the keepme token"
    d = draft("ask", p, "normal", {"name": "Sam", "topic": payload}, 7)
    for w in p.banned_words:
        assert not re.search(rf"\b{re.escape(w)}\b", d.body, re.IGNORECASE), f"{w!r} survived"
    # non-banned content is preserved
    assert "keepme" in d.body


def test_banned_word_strip_respects_word_boundaries(loader: PersonaLoader):
    """'regards' is banned but the substring inside 'regardless' must NOT be clipped."""
    p = loader.get("friends")
    d = draft("ask", p, "normal", {"name": "Sam", "topic": "regardless of regards we ship"}, 11)
    assert "regardless" in d.body
    assert not re.search(r"\bregards\b", d.body, re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Drafter: safe fallbacks — unknown skeleton -> 'ask', empty context never raises.
# --------------------------------------------------------------------------- #
def test_unknown_skeleton_falls_back_to_ask(loader: PersonaLoader):
    p = loader.get("professional")
    ctx = {"name": "Sam", "topic": "the deck", "shot_type_id": "x"}
    fallback = draft("NOT_A_REAL_SKELETON", p, "normal", ctx, 13)
    reference = draft("ask", p, "normal", ctx, 13)
    # 'ask' is a non-email skeleton: no subject, and the rendered body matches the 'ask' default
    assert fallback.subject is None
    assert fallback.body == reference.body


@pytest.mark.parametrize("skeleton", _ALL_SKELETONS + ["unknown_xyz"])
def test_empty_context_never_raises_and_produces_body(loader: PersonaLoader, skeleton: str):
    for cluster in CLUSTERS:
        d = draft(skeleton, loader.get(cluster), "normal", {}, 1)
        assert d.body.strip()  # default slots fill in; no KeyError, no empty body


def test_none_context_does_not_crash(loader: PersonaLoader):
    """draft() guards `context or {}`; passing None must still render cleanly."""
    d = draft("ask", loader.get("family"), "normal", None, 2)  # type: ignore[arg-type]
    assert d.body.strip()
    assert d.params_used["shot_type"] == "ask"


# --------------------------------------------------------------------------- #
# Drafter: subcluster register changes greeting and sign-off.
# --------------------------------------------------------------------------- #
def test_subcluster_close_vs_acquaintance_changes_greeting_and_signoff(loader: PersonaLoader):
    """professional's close vs acquaintance greeting/sign-off pools are disjoint, so the
    rendered greeting line and sign-off line must differ between the two registers — for any
    seed. We assert membership in the right pool rather than a single hard-coded string."""
    p = loader.get("professional")
    ctx = {"name": "Sam", "role": "SWE", "company": "Acme", "shot_type_id": "x"}

    close_signoffs = set(p.signoffs["close"])        # {'Best,', 'Thanks,'}
    acq_signoffs = set(p.signoffs["acquaintance"])   # {'Kind regards,', 'Sincerely,'}
    assert close_signoffs.isdisjoint(acq_signoffs)   # precondition that makes this test meaningful

    for seed in range(20):
        close = draft("apply", p, "close", ctx, seed).body
        acq = draft("apply", p, "acquaintance", ctx, seed).body
        close_sign = close.splitlines()[-1]
        acq_sign = acq.splitlines()[-1]
        assert close_sign in close_signoffs
        assert acq_sign in acq_signoffs
        # disjoint pools guarantee the sign-off line actually changes with the register
        assert close_sign != acq_sign


def test_acquaintance_greeting_drops_first_name_when_pool_dictates(loader: PersonaLoader):
    """A behavioural consequence of register: professional 'acquaintance' includes the
    name-less 'Hello,' greeting, which 'close' never uses. Over a seed sweep the acquaintance
    register reaches that greeting, proving the subcluster actually selects a different pool."""
    p = loader.get("professional")
    ctx = {"name": "Sam", "role": "SWE", "company": "Acme", "shot_type_id": "x"}
    acq_greetings = {draft("apply", p, "acquaintance", ctx, s).body.splitlines()[0] for s in range(20)}
    close_greetings = {draft("apply", p, "close", ctx, s).body.splitlines()[0] for s in range(20)}
    assert "Hello," in acq_greetings           # name-less greeting only exists in acquaintance pool
    assert "Hello," not in close_greetings


# --------------------------------------------------------------------------- #
# voice.py: system prompt carries persona identity + banned words.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("cluster", ["professional", "friends", "family"])
def test_voice_system_prompt_contains_display_name_and_banned_words(loader: PersonaLoader, cluster: str):
    p = loader.get(cluster)
    prose = loader.prose(cluster)
    sysp = voice_system_prompt(p, prose, "normal")
    assert p.display_name in sysp
    for w in p.banned_words:
        assert w in sysp, f"banned word {w!r} not surfaced in system prompt"
    # the subcluster register is named, and the prose (the user's own notes) is embedded
    assert "normal" in sysp
    assert prose.strip()[:40] in sysp


def test_voice_system_prompt_reflects_quantitative_style(loader: PersonaLoader):
    p = loader.get("professional")
    sysp = voice_system_prompt(p, loader.prose("professional"), "close")
    assert f"formality {p.formality:.2f}" in sysp
    assert f"warmth {p.warmth:.2f}" in sysp
    assert f"directness {p.directness:.2f}" in sysp
    assert f"emoji-rate {p.emoji_rate:.2f}" in sysp
    assert "(no emoji)" in sysp  # empty palette renders the no-emoji marker


# --------------------------------------------------------------------------- #
# voice.py: user prompt reflects the shot type's purpose.
# --------------------------------------------------------------------------- #
def test_voice_user_prompt_reflects_shot_type_purpose():
    apply_prompt = voice_user_prompt("apply", {"role": "SWE", "company": "Acme"})
    assert "job application" in apply_prompt
    followup_prompt = voice_user_prompt("followup", {"topic": "the deck"})
    assert "follow-up" in followup_prompt
    # context values are surfaced, but plumbing keys are filtered out
    ctx_prompt = voice_user_prompt("apply", {"role": "SWE", "goal_id": "g1", "shot_type_id": "s1", "skeleton": "apply"})
    assert "role: SWE" in ctx_prompt
    assert "goal_id" not in ctx_prompt and "shot_type_id" not in ctx_prompt and "skeleton" not in ctx_prompt


def test_voice_user_prompt_unknown_shot_type_falls_back_to_generic():
    prompt = voice_user_prompt("NOT_A_SHOT", {})
    assert "Write a message." in prompt
    assert "(no extra context)" in prompt


# --------------------------------------------------------------------------- #
# voice.py: split_subject parses a leading 'Subject:' line, else (None, body).
# --------------------------------------------------------------------------- #
def test_split_subject_parses_leading_subject_line():
    subject, body = split_subject("Subject: Quick hello\n\nHi there,\nthis is the body.")
    assert subject == "Quick hello"
    assert body == "Hi there,\nthis is the body."


def test_split_subject_returns_none_when_absent():
    text = "Hi there,\nno subject line here."
    subject, body = split_subject(text)
    assert subject is None
    assert body == text  # body is the whole (stripped) text unchanged


def test_split_subject_is_case_insensitive_and_strips():
    subject, body = split_subject("  subject:   Spaced Out   \nbody line")
    assert subject == "Spaced Out"
    assert body == "body line"


def test_split_subject_empty_subject_value_yields_none():
    """A bare 'Subject:' with no value should not produce an empty-string subject."""
    subject, body = split_subject("Subject:\nthe body")
    assert subject is None
    assert body == "the body"


def test_split_subject_handles_empty_and_none_input():
    assert split_subject("") == (None, "")
    assert split_subject(None) == (None, "")  # type: ignore[arg-type]
