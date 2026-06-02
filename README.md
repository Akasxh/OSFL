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

## Optional: turn on the LLM (you-voiced agents)

OSFL runs **fully offline** by default. Add an OpenAI key to activate the language agents — the
Monte-Carlo / Bayesian engine stays deterministic either way.

```bash
cp .env.example .env        # then put your key in .env (it is gitignored)
# .env:
#   OPENAI_API_KEY=sk-...
#   OPENAI_MODEL=gpt-4o-mini
```

With a key set, three things upgrade from deterministic fallbacks to real model calls:

- **You-voiced drafting** — the persona skill files (`personas/*.md`) become the system prompt, so
  drafts sound like *you* in the right cluster. Toggle per-draft, or force the template with `use_llm:false`.
- **Scenario advisor** — ask anything ("which goal should I prioritize?") and get an answer grounded
  in your actual goals + forecasts, in your voice.
- **Goal decomposition** — type any goal ("get my first novel published") and the planner builds a
  realistic funnel, which the numpy engine then forecasts.

Without a key these degrade gracefully (deterministic templates / archetypes / a "set a key" note),
and the dashboard shows an `LLM off · offline templates` badge.

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
    voice.py         build LLM prompts from the persona skill files
  llm.py             optional OpenAI wrapper (graceful fallback when no key)
  agents.py          Planner / Simulator / Persona / Followup / Wellbeing / DecisionAdvisor / Advisor / Memory
  orchestrator.py    routes a request → cluster + agent-set, emits a watchable trace
  seed.py            three demo goals with verified priors
  app.py             FastAPI routes + static dashboard
personas/            professional.md · friends.md · family.md  (the skill files)
static/              index.html · app.js  (dashboard) + vendored tailwind.js · alpine.min.js
```

The Monte-Carlo / Bayesian core runs with **zero network access** (Tailwind and Alpine are vendored
into `static/`), and the LLM layer is strictly additive on top. The 25-test suite pins every headline
number (`0.382` / `201` / `150` / posterior `(7,48)` / priority ranking), the persona guarantees, and
the offline LLM fallbacks.
