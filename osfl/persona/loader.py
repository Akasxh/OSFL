"""Parse personas/*.md skill files into PersonaParams. Front-matter is machine-usable;
the prose after it is the human-readable skill guidance (not needed by the drafter)."""

from __future__ import annotations

from pathlib import Path

import yaml

from ..models import PersonaParams

CLUSTERS: tuple[str, ...] = ("professional", "friends", "family")


class PersonaLoader:
    def __init__(self, dir: str = "personas") -> None:
        self.dir = Path(dir)
        self._cache: dict[str, PersonaParams] = {}

    def get(self, cluster: str) -> PersonaParams:
        if cluster not in CLUSTERS:
            raise ValueError(f"unknown cluster: {cluster!r}")
        if cluster not in self._cache:
            self._cache[cluster] = self._parse(self.dir / f"{cluster}.md")
        return self._cache[cluster]

    def all(self) -> dict[str, PersonaParams]:
        return {c: self.get(c) for c in CLUSTERS}

    def prose(self, cluster: str) -> str:
        text = (self.dir / f"{cluster}.md").read_text(encoding="utf-8")
        parts = text.split("---", 2)
        return parts[2].strip() if len(parts) >= 3 else ""

    def _parse(self, path: str | Path) -> PersonaParams:
        text = Path(path).read_text(encoding="utf-8")
        parts = text.split("---", 2)  # ['', <yaml>, <prose>]
        if len(parts) < 3:
            raise ValueError(f"{path}: expected YAML front-matter delimited by ---")
        front = yaml.safe_load(parts[1]) or {}
        return PersonaParams(**front)
