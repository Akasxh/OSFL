"""Optional OpenAI layer.

OSFL runs fully offline without a key. When OPENAI_API_KEY is set, the *language* agents
(drafting, scenario advice, goal decomposition) use the model. The Monte-Carlo / Bayesian
engine never calls this — numbers stay deterministic. Every caller falls back gracefully if
the key is missing or a request errors, so the app never hard-depends on the network.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return  # python-dotenv is a declared dep, but stay importable without it
    load_dotenv(_ROOT / ".env")


_load_env()


class LLM:
    def __init__(self, model: str | None = None) -> None:
        self.api_key: str | None = os.environ.get("OPENAI_API_KEY") or None
        self.model: str = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def chat(self, system: str, user: str, *, temperature: float = 0.7, max_tokens: int = 700) -> str:
        resp = self._get_client().chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

    def chat_json(self, system: str, user: str, *, temperature: float = 0.4, max_tokens: int = 700) -> dict:
        resp = self._get_client().chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return json.loads((resp.choices[0].message.content or "{}").strip())
