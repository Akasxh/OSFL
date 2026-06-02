"""Store: the whole backend as one inspectable JSON file (data/store.json).

Documents are id-keyed collection maps. Writes are atomic (temp file + os.replace) and
guarded by a lock so rapid UI clicks don't corrupt the file. Everything is plain dicts;
the API layer (re)validates through pydantic models on the way in and out.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from .models import utcnow_iso

COLLECTIONS: tuple[str, ...] = ("shot_types", "goals", "shots", "outcomes", "drafts")


def _default_doc() -> dict:
    return {
        "version": 1,
        "shot_types": {},
        "goals": {},
        "shots": {},
        "outcomes": {},
        "drafts": {},
        "meta": {"created_at": utcnow_iso(), "seed_loaded": False},
    }


class Store:
    def __init__(self, path: str = "data/store.json") -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self.doc: dict = _default_doc()
        self.load()

    def load(self) -> None:
        if self.path.exists():
            self.doc = json.loads(self.path.read_text(encoding="utf-8"))
            for c in COLLECTIONS:
                self.doc.setdefault(c, {})
            self.doc.setdefault("meta", {"created_at": utcnow_iso(), "seed_loaded": False})
        else:
            self.doc = _default_doc()
            self.save()

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(self.path.name + ".tmp")
            tmp.write_text(
                json.dumps(self.doc, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            os.replace(tmp, self.path)

    # -- collection ops ----------------------------------------------------- #
    def get(self, coll: str, id: str) -> dict | None:
        return self.doc[coll].get(id)

    def list(self, coll: str, **filters) -> list[dict]:
        items = list(self.doc[coll].values())
        for k, v in filters.items():
            items = [it for it in items if it.get(k) == v]
        return items

    def upsert(self, coll: str, obj: dict) -> dict:
        self.doc[coll][obj["id"]] = obj
        self.save()
        return obj

    def delete(self, coll: str, id: str) -> None:
        self.doc[coll].pop(id, None)
        self.save()

    # -- meta --------------------------------------------------------------- #
    @property
    def meta(self) -> dict:
        return self.doc["meta"]

    def set_meta(self, key: str, value) -> None:
        self.doc["meta"][key] = value
        self.save()
