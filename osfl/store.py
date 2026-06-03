"""Store: the whole backend as one inspectable JSON file (data/store.json).

Documents are id-keyed collection maps. Writes are atomic (temp file + os.replace)
and serialized by a reentrant lock so a mutate-then-save can't interleave with another
writer. Everything is plain dicts; the API layer (re)validates through pydantic models
on the way in and out.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from .models import utcnow_iso

COLLECTIONS: tuple[str, ...] = ("shot_types", "goals", "shots", "outcomes", "drafts")


class StoreError(RuntimeError):
    """Raised when the backing file is unreadable/wrong-shape or addressed with an
    unknown collection — so callers get a clear domain error, not a raw
    JSONDecodeError/KeyError from deep inside."""


def _default_doc() -> dict[str, Any]:
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
        self._lock = threading.RLock()
        self.doc: dict[str, Any] = _default_doc()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.doc = _default_doc()
            self.save()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            raise StoreError(f"corrupt store file: {self.path}") from err
        if not isinstance(raw, dict):
            raise StoreError(f"store file is not a JSON object: {self.path}")
        for c in COLLECTIONS:
            raw.setdefault(c, {})
        raw.setdefault("meta", {"created_at": utcnow_iso(), "seed_loaded": False})
        self.doc = raw

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(self.path.name + ".tmp")
            tmp.write_text(json.dumps(self.doc, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.path)

    def _collection(self, coll: str) -> dict[str, Any]:
        if coll not in COLLECTIONS:
            raise StoreError(f"unknown collection: {coll!r} (expected one of {COLLECTIONS})")
        collection: dict[str, Any] = self.doc[coll]
        return collection

    # -- collection ops ----------------------------------------------------- #
    def get(self, coll: str, id: str) -> dict[str, Any] | None:
        with self._lock:
            doc: dict[str, Any] | None = self._collection(coll).get(id)
            return doc

    def list(self, coll: str, **filters: Any) -> list[dict[str, Any]]:
        with self._lock:
            items: list[dict[str, Any]] = list(self._collection(coll).values())
        for k, v in filters.items():
            items = [it for it in items if it.get(k) == v]
        return items

    def upsert(self, coll: str, obj: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._collection(coll)[obj["id"]] = obj
            self.save()
        return obj

    def delete(self, coll: str, id: str) -> None:
        with self._lock:
            self._collection(coll).pop(id, None)
            self.save()

    # -- meta --------------------------------------------------------------- #
    @property
    def meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = self.doc["meta"]
        return meta

    def set_meta(self, key: str, value: Any) -> None:
        with self._lock:
            self.doc["meta"][key] = value
            self.save()
