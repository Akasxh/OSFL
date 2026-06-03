# OSFL — OS For Life

[![CI](https://github.com/Akasxh/OSFL/actions/workflows/ci.yml/badge.svg)](https://github.com/Akasxh/OSFL/actions/workflows/ci.yml)

> **outcome = probability × volume**

OSFL turns a high-level goal ("land a job", "raise a seed round", "get fit") into a
**Beta-Binomial funnel** and forecasts your real odds with a vectorized NumPy
**Monte-Carlo engine** — then tells you how many shots it actually takes. Log real
results and a conjugate **Bayesian update** sharpens the model to *your* rates, not
population averages. A digital-twin **persona layer** drafts the messages in your voice.

**Status:** working MVP. The deterministic engine + API + dashboard are stable and
covered by the suite; the optional LLM layer is strictly additive (the app runs fully
offline without a key); broader features are tracked in [`ROADMAP.md`](ROADMAP.md).

## Quick start

```bash
uv sync                                              # install into a venv (uses the locked deps)
uv run uvicorn osfl.app:app --reload --port 8000     # then open http://127.0.0.1:8000/
# or, no --reload:  uv run osfl
```

```bash
uv run pytest -q          # run the test suite
uv run ruff check . && uv run mypy osfl   # lint + type-check (what CI runs)
```

The entire backend is one JSON file — after the first run, inspect it any time with
`cat data/store.json`.

## The three "aha" moments

1. **Funnels punish you nonlinearly.** 60 applications through an 8% → 40% → 25% funnel
   is only a **38%** shot at one offer (closed form). To hit 80% you need **201**
   applications, not the ~126 you'd naively guess. *(The dashboard shows a lower
   uncertainty-adjusted ~32% — that gap is deliberate; see
   [ADR 0001](docs/adr/0001-monte-carlo-below-closed-form.md).)*
2. **Your reply rate ≠ the population's.** Log "5 replies from 30 emails" and your
   cold-email posterior jumps from the 8% prior to **12.7%** — every future forecast
   then uses *your* number.
3. **One queue for a whole life.** Job, fundraise, and fitness goals compete in a single
   ranked list scored by `impact × urgency × long-term-value × marginal-P-gain`.

## Optional: turn on the LLM

OSFL runs **fully offline** by default. Add an OpenAI key to upgrade three language
agents — you-voiced drafting, the scenario advisor, and free-text goal decomposition —
from deterministic fallbacks to real model calls. The Monte-Carlo / Bayesian engine
never calls an LLM; numbers stay deterministic either way.

```bash
cp .env.example .env        # then set OPENAI_API_KEY in .env (it is gitignored)
```

## How it fits together

Entry point `osfl/app.py` (FastAPI + the static dashboard). The pure, deterministic math
lives in `osfl/engine/` (NumPy, no I/O); the digital-twin layer in `osfl/persona/`; one
JSON file is the whole store (`osfl/store.py`). Full component diagram and request flow:
[`ARCHITECTURE.md`](ARCHITECTURE.md). Agent-facing build/test commands: [`AGENTS.md`](AGENTS.md).

## License

MIT — see [`LICENSE`](LICENSE).
