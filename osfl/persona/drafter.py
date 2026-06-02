"""Deterministic, offline 'you-voiced' drafter — no LLM, no network.

Given (shot_type, PersonaParams, subcluster, context, seed) it always returns the same draft.
Voice differentiation across clusters comes from the params: greeting register, a warmth opener,
formality word-substitution, hedge injection, an emoji pass, and a sign-off. The same skeleton
renders visibly differently for professional vs friends vs family.
"""

from __future__ import annotations

import hashlib
import re

from ..models import PersonaDraft, PersonaParams

# --------------------------------------------------------------------------- #
# Message skeletons per shot type. {slots} are filled from context (safe defaults
# below); the trailing CTA is chosen by directness.
# --------------------------------------------------------------------------- #
SKELETONS: dict[str, dict] = {
    "apply": {
        "email": True,
        "subject": "Application for the {role} role",
        "core": "I'd like to put my name forward for the {role} role at {company}. {pitch}",
        "cta": {"direct": "Could we find 15 minutes this week to talk?",
                "soft": "It would mean a lot to get the chance to chat whenever suits you."},
    },
    "ask": {
        "email": False,
        "subject": "Quick question",
        "core": "I wanted to ask you about {topic}. {pitch}",
        "cta": {"direct": "Let me know what you think?",
                "soft": "No rush at all — whenever you get a moment."},
    },
    "intro": {
        "email": True,
        "subject": "Intro — {me}",
        "core": "I'm {me}, {pitch} I came across {company} and thought it was worth reaching out.",
        "cta": {"direct": "Open to a quick call next week?",
                "soft": "Would love to connect if you're open to it."},
    },
    "followup": {
        "email": True,
        "subject": "Following up on {topic}",
        "core": "I'm circling back on {topic} from {when}.",
        "cta": {"direct": "Is this still on your radar?",
                "soft": "Totally understand if now's not the time — just keeping it warm."},
    },
    "thanks": {
        "email": False,
        "subject": "Thank you",
        "core": "Thank you so much for {reason}. {pitch}",
        "cta": {"direct": "I owe you one.",
                "soft": "It genuinely made a difference."},
    },
    "habit_nudge": {
        "email": False,
        "subject": "",
        "core": "Time for {goal} — you're {progress} of the way to {target}.",
        "cta": {"direct": "Lace up, future-you says thanks.",
                "soft": "Even a short one counts today."},
    },
}

_DEFAULTS = {
    "name": "there", "role": "", "company": "your team", "topic": "my note",
    "when": "last week", "pitch": "", "me": "me", "goal": "your goal",
    "progress": "part", "target": "your target", "reason": "your time and help",
}

# Word substitutions applied by formality. (casual_form, formal_form)
_FORMALITY_SUBS = [
    ("wanna", "would like to"),
    ("gonna", "going to"),
    ("yeah", "yes"),
    ("hey", "hello"),
    ("thanks", "thank you"),
    ("a bit", "somewhat"),
]
_HEDGES = ["I was wondering —", "whenever you get a chance,", "no pressure, but"]
_WARMTH_HIGH = "Hope you're doing really well."
_WARMTH_MED = "Hope you're good!"


class _Slots(dict):
    def __missing__(self, key):  # never KeyError on a missing slot
        return _DEFAULTS.get(key, "")


def _hash(seed: int, salt: int) -> int:
    h = hashlib.sha256(f"{seed}:{salt}".encode()).hexdigest()
    return int(h[:8], 16)


def _pick(options: list[str], seed: int, salt: int) -> str:
    if not options:
        return ""
    return options[_hash(seed, salt) % len(options)]


def seed_from(goal_id: str | None, stage_id: str | None, contact_id: str | None) -> int:
    raw = f"{goal_id or ''}|{stage_id or ''}|{contact_id or ''}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


def _apply_formality(text: str, formality: float) -> str:
    for casual, formal in _FORMALITY_SUBS:
        if formality > 0.6:
            text = re.sub(rf"\b{re.escape(casual)}\b", formal, text, flags=re.IGNORECASE)
        elif formality < 0.3:
            text = re.sub(rf"\b{re.escape(formal)}\b", casual, text, flags=re.IGNORECASE)
    return text


def _lint(text: str, params: PersonaParams) -> str:
    for w in params.banned_words:
        text = re.sub(rf"\b{re.escape(w)}\b", "", text, flags=re.IGNORECASE)
    if params.emoji_rate == 0.0:
        text = re.sub(r"!{2,}", "!", text)  # collapse exclamation chains for professional
    return re.sub(r"\s{2,}", " ", text).strip()


def _emoji_pass(sentences: list[str], params: PersonaParams, seed: int) -> list[str]:
    if params.emoji_rate <= 0 or not params.emoji_palette:
        return sentences
    out = []
    for i, s in enumerate(sentences):
        s = s.rstrip()
        if s and (_hash(seed, 100 + i) % 1000) / 1000.0 < params.emoji_rate:
            s = f"{s} {_pick(params.emoji_palette, seed, 200 + i)}"
        out.append(s)
    return out


def draft(
    shot_type: str,
    params: PersonaParams,
    subcluster: str,
    context: dict,
    seed: int,
) -> PersonaDraft:
    sk = SKELETONS.get(shot_type, SKELETONS["ask"])
    slots = _Slots(context or {})

    greet_opts = params.greetings.get(subcluster) or params.greetings.get("normal") or ["Hi {name},"]
    greeting = _pick(greet_opts, seed, 1).format_map(slots)

    sentences: list[str] = []
    if params.warmth >= 0.85:
        sentences.append(_WARMTH_HIGH)
    elif params.warmth >= 0.7:
        sentences.append(_WARMTH_MED)

    core = sk["core"].format_map(slots).strip()
    if params.directness < 0.5 and core:
        hedge = _pick(_HEDGES, seed, 2)
        hedge = hedge[0].upper() + hedge[1:]
        # keep a leading "I"/"I'm" capitalized; otherwise lowercase the continuation
        if core.startswith("I ") or core.startswith("I'"):
            core = f"{hedge} {core}"
        else:
            core = f"{hedge} {core[0].lower()}{core[1:]}"
    sentences.append(core)

    cta_key = "direct" if params.directness >= 0.6 else "soft"
    cta = sk["cta"][cta_key].format_map(slots).strip()
    if cta:
        sentences.append(cta)

    sentences = [_apply_formality(s, params.formality) for s in sentences if s]
    sentences = _emoji_pass(sentences, params, seed)
    body_text = _lint(" ".join(sentences), params)

    sign_opts = params.signoffs.get(subcluster) or params.signoffs.get("normal") or ["Best,"]
    signoff = _pick(sign_opts, seed, 3).format_map(slots).strip()

    pieces = [p for p in (greeting, body_text, signoff) if p]
    assembled = "\n\n".join(pieces)

    subject = None
    if sk.get("email") and sk.get("subject"):
        subject = _lint(sk["subject"].format_map(slots), params)

    return PersonaDraft(
        shot_type_id=context.get("shot_type_id", "") if context else "",
        persona=params.cluster,
        subject=subject or None,
        body=assembled,
        params_used={
            "cluster": params.cluster,
            "subcluster": subcluster,
            "formality": params.formality,
            "warmth": params.warmth,
            "directness": params.directness,
            "emoji_rate": params.emoji_rate,
            "shot_type": shot_type,
            "seed": seed,
        },
    )
