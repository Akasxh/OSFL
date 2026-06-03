"""Build LLM prompts from a persona skill file so the model drafts in the user's voice.

The persona/*.md prose IS the system prompt material — it was authored as "how I actually
talk". This module turns (PersonaParams + prose) into a system prompt and turns a shot type
into a user prompt, and splits an optional "Subject:" line back out of the model's output.
"""

from __future__ import annotations

from typing import Any

from ..models import PersonaParams

_PURPOSE = {
    "apply": "job application / cold outreach email to a target role",
    "ask": "short, direct ask",
    "intro": "introduction / first-contact message",
    "followup": "follow-up after no reply (keep the thread alive without nagging)",
    "thanks": "thank-you message",
    "habit_nudge": "short self-nudge to do today's session",
}


def voice_system_prompt(params: PersonaParams, prose: str, subcluster: str) -> str:
    palette = " ".join(params.emoji_palette) or "(no emoji)"
    banned = ", ".join(params.banned_words) or "(none)"
    reactions = "; ".join(f"{k}: {v}" for k, v in params.reactions.items()) or "(none)"
    return f"""You write messages AS the user (first person) in their **{params.display_name}** voice. The recipient is a "{subcluster}" contact in this cluster.

The user's own notes on how they talk here:
\"\"\"
{prose.strip()}
\"\"\"

Quantitative style to match: formality {params.formality:.2f}, warmth {params.warmth:.2f}, directness {params.directness:.2f}, emoji-rate {params.emoji_rate:.2f} (allowed emoji: {palette}), target length ~{params.avg_len} words.
Never use these words/phrases: {banned}.
Reaction instincts — {reactions}.

Rules:
- Sound exactly like the user, NOT like an AI assistant. No meta commentary.
- If emoji-rate is 0, use zero emoji. Otherwise use them sparingly per the rate.
- NEVER leave bracketed placeholders like [Your Name], [Company], or a fill-in signature block. Use the provided context; if a detail is unknown, write naturally around it.
- Output ONLY the message. For an email-type message, make the FIRST line "Subject: ..." then a blank line then the body. Otherwise output just the body.
- Stay close to the target length and the relationship register."""


def voice_user_prompt(skeleton: str, context: dict[str, Any]) -> str:
    purpose = _PURPOSE.get(skeleton, "message")
    ctx = {
        k: v for k, v in (context or {}).items() if k not in ("shot_type_id", "goal_id", "stage_id", "skeleton") and v
    }
    lines = "\n".join(f"- {k}: {v}" for k, v in ctx.items()) or "- (no extra context)"
    return f"Write a {purpose}.\nContext:\n{lines}"


def split_subject(text: str) -> tuple[str | None, str]:
    text = (text or "").strip()
    first, _, rest = text.partition("\n")
    if first.lower().startswith("subject:"):
        return first.split(":", 1)[1].strip() or None, rest.strip()
    return None, text
