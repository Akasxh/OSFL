# OSFL — OS For Life

> **outcome = probability × volume**

OSFL ("OS For Life") turns a high-level goal ("land a job", "raise a seed round", "get fit") into a
**Beta-Binomial funnel** and forecasts your odds with a vectorized numpy **Monte-Carlo engine**
before prescribing how many shots to take. Log real results and a conjugate **Bayesian update**
sharpens the model to *your* rates — not population averages. A digital-twin **persona layer**
(three skill files: professional / friends / family) drafts the actual messages in your voice.

Fully offline. No API keys. One JSON file is the whole backend, and one static dashboard shows it all.

## Run (one command)

```bash
uv sync                                              # install deps into a venv
uv run uvicorn osfl.app:app --reload --port 8000
# then open http://127.0.0.1:8000/
```

Or via the project script:

```bash
uv run osfl      # same thing, no --reload
```

Run the tests:

```bash
uv run --extra dev pytest -q
```

Inspect the entire backend at any time:

```bash
cat data/store.json
```

## The three "aha" moments

1. **Funnels punish you nonlinearly.** 60 job applications through an 8% → 40% → 25% funnel is only a
   **38%** shot at one offer. To hit 80% you need **201** applications, not the ~126 you'd naively guess.
2. **Your reply rate ≠ the population's.** Log "5 replies from 30 emails" and your cold-email posterior
   jumps from the 8% prior to **12.7%** — and every future forecast uses *your* number.
3. **One queue for a whole life.** Job, fundraise, and fitness goals compete in a single ranked list
   scored by `impact × urgency × long-term-value × marginal-P-gain`.

See [`ARCHITECTURE`](#architecture) below for the full module map.

## Architecture

```
osfl/
  models.py          pydantic domain models + DTOs
  store.py           JSON-file persistence (data/store.json)
  engine/            pure numpy math (no I/O, deterministic given a seed)
    funnel.py        Beta-Binomial funnel Monte Carlo
    habit.py         habit / adherence Monte Carlo
    bayes.py         conjugate Beta updating
    strategy.py      bottleneck + min-volume + suggestions
    priority.py      cross-goal priority scoring
    stats.py         summary statistics + histogram
  persona/           digital-twin layer
    loader.py        parse personas/*.md front-matter
    drafter.py       deterministic, offline "you-voiced" drafting
  agents.py          Planner / Simulator / Persona / Followup / Wellbeing / DecisionAdvisor / Memory
  orchestrator.py    routes a request → cluster + agent-set, emits a watchable trace
  seed.py            three demo goals with verified priors
  app.py             FastAPI routes + static dashboard
personas/            professional.md · friends.md · family.md  (the skill files)
static/              index.html · app.js  (dashboard) + vendored tailwind.js · alpine.min.js
```

Everything runs with **zero network access** — Tailwind and Alpine are vendored into `static/`,
so the dashboard works fully offline. The 20-test suite pins every headline number
(`0.382` / `201` / `150` / posterior `(7,48)` / priority ranking) plus the persona guarantees.
