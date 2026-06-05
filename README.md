# OSFL — OS For Life

[![CI](https://github.com/Akasxh/OSFL/actions/workflows/ci.yml/badge.svg)](https://github.com/Akasxh/OSFL/actions/workflows/ci.yml)

> **outcome = probability × volume**

Most planning tools track what you *did*. OSFL forecasts what will *work*. It turns a
high-level goal ("land a job", "raise a seed round", "get fit") into a **Beta-Binomial
funnel**, runs a vectorized NumPy **Monte-Carlo engine** over it, and tells you the two
numbers that actually matter: *your odds at the current effort* and *how many shots it
really takes*. Log outcomes and a conjugate **Bayesian update** replaces population
averages with *your* measured rates. One **priority queue** ranks the next action across
every goal in your life, and a digital-twin **persona layer** drafts the message in your
voice.

**Live tour:** [osfl.vercel.app](https://osfl.vercel.app) · **Agent-readable summary:**
[osfl.vercel.app/llms.txt](https://osfl.vercel.app/llms.txt)

**Status:** working MVP. The deterministic engine + API + dashboard are stable and CI-gated;
the optional LLM layer is strictly additive (the app runs fully offline without a key);
future work lives in [`ROADMAP.md`](ROADMAP.md).

## Quick start

```bash
uv sync                                              # install (locked deps, creates the venv)
uv run uvicorn osfl.app:app --reload --port 8000     # then open http://127.0.0.1:8000/
# or, no --reload:  uv run osfl
```

```bash
uv run pytest -q                                     # the test suite
uv run ruff check . && uv run mypy osfl              # lint + strict type-check (what CI runs)
```

No database, no services: the entire backend is one JSON file — after the first run,
inspect it any time with `cat data/store.json`. The dashboard's JS is vendored, so the
whole thing works with zero network access.

## The three "aha" moments

1. **Funnels punish you nonlinearly.** 60 applications through an 8% → 40% → 25% funnel is
   only a **38%** shot at one offer (closed form). To reach 80% you need **201**
   applications — not the ~126 you'd naively guess by scaling.
2. **Your reply rate ≠ the population's.** Log "5 replies from 30 cold emails" and your
   posterior jumps from the 8% prior to **12.7%** (`Beta(7, 48)`) — every future forecast
   then runs on *your* number.
3. **One queue for a whole life.** Job, fundraise, and fitness goals compete in a single
   ranked list scored `impact × urgency × long-term-value × marginal-P-gain`, so the answer
   to "what should I do right now?" is one item, not three apps.

The dashboard also shows a *lower* uncertainty-adjusted Monte-Carlo number (~32% vs the
38% closed form). That gap is deliberate — parameter uncertainty, not a bug:
[ADR 0001](docs/adr/0001-monte-carlo-below-closed-form.md).

## What's inside

| Capability | Where | How |
|---|---|---|
| Funnel + habit forecasting | `osfl/engine/funnel.py`, `habit.py` | seeded Beta-Binomial Monte-Carlo, 10k runs |
| Learn *your* rates | `osfl/engine/bayes.py` | conjugate Beta update from logged outcomes |
| Strategy validation | `osfl/engine/strategy.py` | bottleneck detection, analytic min-volume, framed fixes |
| Cross-life priority queue | `osfl/engine/priority.py` | normalized marginal-gain scoring |
| You-voiced drafting | `osfl/persona/` | persona skill files → deterministic templates or LLM |
| Scenario advice + decomposition | `osfl/agents.py` + optional OpenAI | graceful offline fallbacks, bounded requests |
| Dashboard | `static/` | Alpine + Tailwind, vendored, served by the app |

## API at a glance

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | liveness/readiness (store readable, goal count, LLM availability) |
| `GET /api/state` | the full dashboard payload in one call |
| `POST /api/goals` | create a goal (auto-decomposes into a funnel/habit) |
| `POST /api/goals/{id}/simulate` | run the Monte-Carlo forecast |
| `POST /api/goals/{id}/validate` | pass/reject the strategy + bottleneck + min-volume |
| `POST /api/goals/{id}/outcomes` | log real results → Bayesian update → fresh forecast |
| `GET /api/queue` | the ranked next-shot list across all goals |
| `POST /api/draft` | draft a message in your voice (template or LLM) |
| `POST /api/advise` | free-text scenario advice grounded in your forecasts (LLM) |

Interactive docs at `http://127.0.0.1:8000/docs` once running.

## Verify every claim

Nothing above asks for trust. From a fresh clone:

```bash
uv sync --locked          # fails loudly if the lockfile has drifted
uv run pytest -q          # the suite pins the engine math, API contracts, and fallbacks
uv run mypy osfl          # strict mode, zero issues
uv run python -c "
from osfl.engine.funnel import simulate_funnel
from osfl.engine.strategy import min_volume_for_threshold
from osfl.engine.bayes import update_posterior
stages = [(2.0, 23.0), (4.0, 6.0), (2.5, 7.5)]            # 8% -> 40% -> 25%
print('MC P(>=1) @60, seed 42:', simulate_funnel(60, stages, 1, seed=42).p_success)           # 0.3201
print('applications for 80%:', min_volume_for_threshold(stages, 1, 0.80))                     # 201
print('posterior after 5/30:', update_posterior((2.0, 23.0), 5, 30))                          # (7.0, 48.0)
"
```

CI runs the same gates on every push and PR — the badge above is the live state.

## Optional: turn on the LLM

Add an OpenAI key to upgrade three language agents — you-voiced drafting, the scenario
advisor, and free-text goal decomposition — from deterministic fallbacks to real model
calls. The Monte-Carlo / Bayesian engine never touches an LLM; the numbers stay
deterministic either way, and every call is time-bounded with a logged fallback.

```bash
cp .env.example .env        # then set OPENAI_API_KEY in .env (it is gitignored)
```

## Docs map

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — component diagram (Mermaid), layers, request flow
- [`AGENTS.md`](AGENTS.md) — exact build/test commands + the gotchas that look like bugs
- [`docs/adr/`](docs/adr/) — design decisions with rationale (start with ADR 0001)
- [`CHANGELOG.md`](CHANGELOG.md) — Keep-a-Changelog history
- [`ROADMAP.md`](ROADMAP.md) — forward-looking plans (aspirational, not current claims)
- [`web/`](web/) — the source of the [osfl.vercel.app](https://osfl.vercel.app) landing page

## License

MIT — see [`LICENSE`](LICENSE).
