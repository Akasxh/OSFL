# AGENTS.md

Working notes for coding agents. Commands first; only facts you can't infer at a glance.

## Commands (uv-managed — never use pip)

```bash
uv sync --locked                                   # install
uv run uvicorn osfl.app:app --reload --port 8000   # run the app
uv run pytest -q                                   # test
uv run pytest tests/test_engine.py::test_name -q   # one test
uv run ruff check . && uv run ruff format --check . # lint + format
uv run mypy osfl                                   # type-check
uv run mutmut run                                  # mutation test (scoped to osfl/engine/)
```

Before marking work done, run the full gate (this is exactly what CI runs):
`uv run ruff check . && uv run ruff format --check . && uv run mypy osfl && uv run pytest -q`

## Layout

- `osfl/engine/` — pure NumPy, deterministic given a seed, **no I/O**. Keep it that way.
- `osfl/agents.py`, `osfl/orchestrator.py` — domain logic over engine + store + persona.
- `osfl/app.py` — FastAPI routes + the static dashboard; `osfl/models.py` — all types.
- `osfl/store.py` — the whole backend is one JSON file (`data/store.json`, gitignored).
- `tests/` — pytest; `test_llm_live.py` needs a real key (`--run-llm`), skipped by default.

## Gotchas (look like bugs, aren't)

- A funnel reports a Monte-Carlo `P(≥1)` (~0.3201 at seed 42) **below** the closed form
  (0.3824). Deliberate parameter-uncertainty (per-run Beta sampling) — see
  `docs/adr/0001-monte-carlo-below-closed-form.md`. Do not "fix" it.
- The app runs **fully offline** without `OPENAI_API_KEY`; the LLM layer is additive with
  graceful fallbacks. Tests force the offline path.

## Boundaries

- Don't edit `data/store.json` or `.env` by hand. Don't add dependencies you don't need.
- `web/` is a separate landing page — out of scope for the Python package.
