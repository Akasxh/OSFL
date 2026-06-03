# OSFL Robustness Roadmap

How to make OSFL robust enough to **self-author a `simulate_alex_job.md`-style life simulation**
(deep profile → 90-day arc → reject/pivot/crisis/moonshot/viral/win → branching mermaid graph),
end-to-end, **offline, deterministic, and honest**.

This plan is the synthesis of three parallel design passes:
1. **Foundations** — cold-start priors + mirror-vs-guide (the two cross-cutting decisions).
2. **Five features** — F1 scenario simulator, F2 mermaid graph, F3 asset ingestion, F4 serendipity, F5 burnout — with an architect's build order and a skeptic's red-team.
3. **Borrow research** — the best real-world systems on GitHub for each, vetted for credibility/license/hype.

---

## 0. The unifying principle (what the research proved)

**Zero new mandatory dependencies.** Every one of the 7 capabilities is achievable by *copying an idea*
or *vendoring a tiny MIT/Apache/BSD snippet* over the existing `numpy + fastapi + pydantic + pyyaml (+ openai)`
stack — **~700–900 lines of plain Python + one vendored browser bundle (mermaid)**. The adversary
confirmed all ~20 borrows are real repos, correctly licensed, with no invented sources. We import **none**
of the big frameworks (LangGraph, CrewAI, AutoGen, Swarm, mem0, cognee, PyMC, …) — they pull heavy
transitive deps and/or LLM-tool-call plumbing that breaks offline-first. We copy their *load-bearing pattern*
in 20–80 lines each.

License discipline (verified): MIT/Apache/BSD = safe to copy code · GPL/AGPL (uhabits, anki-sm-2,
SillyTavern) = **idea-only**, reimplement the (uncopyrightable) math fresh · AutoGen is **CC-BY-4.0**
(content license) = idea-only · BabyAGI prompts only from the **MIT v0.1.0 tag** (HEAD is unlicensed).

---

## 1. Two reframes that shape everything (from the skeptic)

These are not features — they are corrections that every phase must honor.

### 1a. Determinism ≠ meaningfulness  *(the single biggest conceptual hole)*
OSFL's engine deliberately samples `p ~ Beta(a,b)` **per run** to capture parameter uncertainty (that's
why the pinned MC value is `0.3201`, below the `0.3824` closed form). A scenario is the *opposite shape* —
one path through time. Drawing one `Beta`→`Binomial` per tick is byte-reproducible at `seed=42` but makes
Alex's whole win/lose arc a property of the *seed*, not the *strategy*.

> **Rule:** the narrative **beats** (when to pivot, when crisis fires, whether a win is reachable) are
> **deterministic functions of the forecast distribution** — use the engine's existing noise-free
> `point_estimate_p` / `find_bottleneck`. Sampling is reserved **only** for the discrete event outcome at
> each beat (did *this* batch convert; did serendipity fire), drawn from a child RNG stream. Then pin the
> event sequence at `seed=42` **and** add a **5-seed-sweep test** asserting the qualitative arc
> (pivot fires, crisis fires, a win is reachable) is stable. Reproducible *and* representative.

### 1b. Emit BEATS, not ticks
A 90-day per-tick loop yields 100–300 mermaid nodes — unreadable. The target artifact is readable
*because* it has ~6 curated milestone beats. **The runner emits a `ScenarioEvent` only on days where
state changes** (channel launch, pivot, crisis, serendipity, win/fail); quiescent days advance the clock
silently. ~5–10 nodes, readable graph **without** collapse logic, smaller store footprint. MVP, not deferred.

### 1c. Three more guardrails
- **Serendipity is counterfactual, not a pass-button.** The WIN comes from the *strategy* (the warm-intro
  pivot lifting the bottleneck — `strategy.py` already computes this `better_shot_type` lift); luck changes
  *timing*, not *outcome*, and its contribution to win-probability is **capped**. Always report
  `p_base` vs `p_with_strategy` vs `luck_share`. A goal impossible-without-luck still reads as impossible.
- **Mutation safety.** The runner operates on **deep copies**, reuses `Planner.ARCHETYPES` as **data only**
  (never calls `Planner`/`Simulator.run`/`Memory.log`, which persist `last_sim`/`user_alpha`), and a guard
  test snapshots the **entire** store doc before/after asserting byte-equality.
- **One loop, not two.** No separate `Simulator.run_timeline`. Live burnout detection is a *pure fold* of
  the outcome log; the runner reuses that same fold. The ScenarioRunner is the only loop.

---

## 2. Phase 0 — Foundations (prerequisites, not add-ons)

The Alex scenario's defining move ("Override Denied → let him fail → FORCE the switch") **is**
`classify()` reading a tier-gapped prior's forecast — so neither half of the demo exists until both
foundation modules do. They integrate at one symbol: **`ShotType.effective_prior()`** — cold-start governs
the *number* it returns; mirror-vs-guide governs the *authority* to act on it. Both read the **same scalar
`strength = α+β`** with opposite intent.

### 2a. Cold-start priors — where probability comes from before any data
**Decision:** a 3-layer provenance-tracked Beta prior. `benchmark` (cited real-world rate) → `segment_tilt`
(features from the profile multiply the mean and **shrink strength**, because a tilt is itself a guess) →
`user_posterior` (the existing conjugate update). **`strength` = confidence = pseudocount.**

**Why it's robust + honest:** `funnel.py` already draws `p ~ Beta(a,b)` per run, so a **weak prior (small
α+β) is automatically a wider Beta → fatter forecast tails**, with *zero new code*. The design's only job is
to **not inflate strength**: benchmark-backed → 20–40; segment-tilted → ×0.6; **LLM-guessed → forced to 4–6**
(so 1–2 real outcomes dominate — verified: a strength-4 prior moves `0.04→0.090` after 2 wins of 20, vs a
strength-40 prior reaching only `0.060`). This is the **numeric twin of Persona's anti-hallucination guard**:
the voice layer won't let the LLM invent your register; the prior layer won't let it invent precision.

**The borrow:** *Empirical-Bayes Beta-Binomial* (David Robinson, public-domain math) — wrap the **existing**
`engine/bayes.beta_from_mean(mean, strength)` (confirmed present; it's exactly method-of-moments
`α=mean·strength, β=(1−mean)·strength`) with a layered `BetaPrior{mean, strength, provenance, source_layer}`.
~30 lines, nothing vendored.

**New:** `osfl/engine/priors.py` (`resolve_prior(shot_key, segment)`), `osfl/data/benchmarks.json` (~6 cited
keys: ATS callback ~8%, recruiter-screen ~40%, onsite→offer ~25%, VC warm-intro ~20%, gym adherence ~60%, …),
`PriorSource` model + `prior_source_id` on `ShotType`, one `prior_sources` store collection. UI: a
`benchmark / estimated / your_data` confidence badge on each forecast.

**Worked example (Alex):** cold-app benchmark `0.08` (strength 25) × `tier_gap` (Tier-3→Tier-1, ×0.5 mean,
×0.6 strength) → `0.04` strength 15 → `Beta(0.6, 14.4)`. 60 apps → **P(≥1) = 0.175** (vs 0.32 generic),
min-volume for 70% jumps **150 → 301**. *This is the engine ground for "Override Denied."*

**Test migration (non-negotiable):** the demo priors `0.08/0.40/0.25` are currently pinned as "verified."
Re-derive them from `benchmarks.json` (`beta_from_mean(0.08,25) == (2.0,23.0)` exactly, already proven by
`test_beta_from_mean_roundtrip`) so **the numbers stay green**; only the *framing* changes — split
`test_engine.py` into ENGINE-INVARIANTS (keep pinned) and ILLUSTRATIVE-PRIORS (a fixture, not a fact).

### 2b. Mirror-vs-guide — when OSFL imitates you vs overrides you
**Decision:** an explicit per-domain `GuidancePolicy(mode = mirror | guide | hard_limit)`, assigned by one
principle:
- **MIRROR** any surface whose correctness is *fidelity-to-you*: voice/tone/drafting (`Persona.make_draft`,
  `persona/voice.py`). **Never overridden** — this is the anti-hallucination twin.
- **GUIDE** any surface whose correctness is *expected-value-over-time*: strategy/volume/priority
  (`Planner`/`Simulator`/`DecisionAdvisor`). May contradict you.
- **HARD_LIMIT** the narrow set where one override causes durable harm: **burnout/overwork**, and registering
  a plan whose forecast is below a self-deception floor.

**The 4-rung override ladder** (you can force any choice; the cost is logged): `advise` → `warn-with-forecast`
("this path 11% vs the referral path 58%" + a logged *"Override Denied. User insists."*) → `require-ack`
(you must acknowledge the specific forecast number, which persists as consent evidence) → `hard-throttle`
(only hard_limit domains; caps the batch, never a flat "no").

**Bounded failure = the ProofWindow** (this is the scenario's exact shape): on an override, instead of
registering 60 cold apps, open a `ProofWindow(granted_volume = ~10, failure_trigger = "k==0 or posterior
below lower credible bound")`. You send 10 — **drafted in your exact voice (mirror untouched)** — outcomes
flow through the existing `update_posterior`; when the trigger fires, the strategist force-switches and the
Advisor delivers the hard truth **in your own voice** ("the network was never the bottleneck — a Tier-3
portfolio cold-applying to Tier-1 converts ~5%; we proved it in 10 shots; switch to warm intros").

**The borrows (a 3-way copy-the-idea stack, import nothing):**
- `guardrails-ai/guardrails` (Apache-2.0): the `OnFailAction` enum shape → `Rung(str, Enum)`, plus the rule
  *even the lowest rung still logs the event*, plus a bounded retry budget.
- `NeMo-Guardrails` (Apache-2.0): the *YAML-category → typed-pydantic* pattern → `guidance.yaml` keyed by
  domain, loaded into a `GuidancePolicy` (pyyaml already shipped). No Colang.
- `Cerbos` (Apache-2.0): **deny-overrides precedence** → `hard_limit > guide > mirror` as a 20-line
  declarative resolver ("burnout always beats push-volume").
- `LangGraph` (MIT): the `HumanInterrupt/HumanResponse` schema → a typed consent record for `require-ack`,
  serialized to the JSON store for deterministic offline resume.
- `Constitutional AI` (method-name only): the critique→revise loop as the ProofWindow — **MVP = "retry N
  times then escalate a rung" with a threshold check**; the LLM critique branch is additive polish.

**New:** `osfl/guidance.py` (~120 lines), `engine/guidance.py` pure `classify(forecast_p, alt_p, deadline,
policy, domain, prior_layer) -> (rung, reason)`, `guidance.yaml`, models `GuidanceMode/DomainPolicy/
GuidancePolicy/ProofWindow/GuidanceEvent`, two store collections (`guidance_log`, `proof_windows`), a seeded
tier-mismatch `ShotType` (built *through* `resolve_prior`, not hand-typed). **Mirror layer needs zero edits**
— proof the seam holds. Enforce it with a test asserting `persona/voice.py` never receives strategist content.

### 2c. The interlock (why they ship together)
Both read `strength`. **Critical wiring:** a weak, un-grounded prior can `warn` but must **cap the ladder at
rung 2** — the system must never nag hardest where it's *least* sure. Pass `PriorSource.layer` into
`classify()`; when `layer != user_posterior`, no ack-gate or hard-throttle. The **ProofWindow is the cure**:
it's cheap precisely so ~10 real outcomes correct a wrong prior before any big commitment.

---

## 3. Phase 1 — Three standalone deterministic cores (parallel, valuable on their own)

### F5 — Burnout / crisis (replaces the flagged shallow Wellbeing)
**The borrow:** *uhabits exponential-smoothing* (GPL repo → idea-only, the formula is a math identity):
`mult = 0.5 ** (sqrt(freq)/halflife); score = prev*mult + value*(1-mult)` — a 2-line, deterministic,
bounded-[0,1], seed-free state update (hits raise, misses decay, recent dominates). Plus the
*Maslach Burnout Inventory* **3-factor vector** (public construct): morale = `(exhaustion, cynicism, efficacy)`
not one scalar, so F5 distinguishes "tired but engaged" from "detached" — and **each axis routes to a
different ladder rung**. `exhaustion ← volume-vs-capacity`, `cynicism ← tone EMA` (LLM/VADER optional, deferred),
`efficacy ← posterior-mean / p_success trend`.
**New:** `osfl/engine/wellbeing.py` (~40 lines, pure arithmetic), rewrite `Wellbeing.report()` as a fold over
the outcome log (keep legacy `momentum/streak/load/message`), persist nothing extra in MVP. This is the
`hard_limit` actuator and **fires CRISIS on a rejection streak** — the gap the Alex demo exposed.

### F4 — Serendipity / luck (counterfactual tail events)
**The borrow:** a *seeded two-component Bernoulli mixture* (standard rare-event technique; `bayesian-testing`
MIT as the numpy reference): outcome = base Beta draw, but with tiny `p_tail` draw a bounded high-impact
"jackpot" from a heavy-tailed component — on an **independent child RNG stream** (`default_rng(seed ^ const)`),
so base draws stay byte-identical (verified: base `p_success` stays `0.3201`). Base rates are fixed grounded
priors (~1e-3/day), effects additive-only and capped, every win carries a fired-flag.
**New:** `engine/serendipity.py`, 3 seeded `event_types` (viral_post/surprise_referral/lucky_timing),
`SimulationResult` gains `p_success_base / p_success_with_events / serendipity_share`. UI panel ② overlays
base-vs-events + a "X% of wins via a rare event" label.

### Tilt helper (the only piece of F3 we keep for MVP)
**Cut full F3 ingestion** (mem0/cognee/unstructured/Graphiti/Letta = ~250 LLM-dependent lines, the biggest
chunk, for two things the seed file can hardcode). **Keep only** `engine/tilt.py` — a single-stage
Beta-strength-preserving shrink (`tier_gap` ×0.64 at gap 2) applied at sim time over a **copy** of the priors
(ShotType untouched, reversible). Hardcode Alex's profile + one warm-intro contact in `seed.py`, exactly as
the 3 demo goals are already hardcoded. *(Full ingestion → Phase 5, below.)*

---

## 4. Phase 2 — F1 ScenarioRunner (the keystone)

`osfl/scenario.py` — the BEAT-emitting loop that composes Phase 1.

**The borrows (control flow, copied not imported):**
- **OpenAI Swarm / Agents SDK** (MIT) — *handoff-as-return-value*: each step returns
  `StepResult{state_delta, next, summary}`; a bounded `while turns < max and active_step:` applies the delta
  and swaps to `next`. `DecisionAdvisor` becomes a router returning `next = 'pivot' | 'crisis' | 'moonshot'`.
  ~40 lines, zero deps. (Swarm is unmaintained-by-design; we copy the pattern, deprecation is irrelevant.)
- **DeepMind Concordia** (Apache-2.0) — *propose-vs-resolve*: the agent **proposes** an action; a separate
  `resolve()` = **OSFL's existing seeded Beta-Binomial engine** decides what happened, then conjugate-updates.
  Agents never decide their own success → every outcome auditable, swappable, offline-deterministic.
- **AutoGen** (CC-BY-4.0 → idea-only) — *composable termination predicates*:
  `[GoalReached(thr), DayBudget(n), BurnoutHardLimit(), StallDetector()]` OR'd together; F5's burnout
  hard_limit is one predicate, the day budget another. Hard tick-ceiling prevents a crisis-pause infinite loop.
- **Tree-of-Thoughts** (MIT) + **Thompson sampling** (textbook) for *pivot quality*: propose 2–4 candidate
  strategy edits, **simulate each with the existing engine at a fixed seed**, argmax the projected `p_success`
  delta, emit `(chosen, rejected[])`. The rejected branches are a *free* byproduct that feeds F2's red edges.
  The pivot becomes an auditable simulate-then-select, not a hardcoded if/else.

**Honoring §1:** beats decided by deterministic `point_estimate_p`/`find_bottleneck`; sampling only for the
discrete batch outcome; deep-copy mutation safety; ~5–10 beats. The runner **delegates** luck to
`engine/serendipity.py` and crisis to `engine/wellbeing.classify` — owns no luck/morale math.

**Bridge to F2:** the *AgentOps* `RunEvent{id, parent_id, day, kind, status, seed}` schema (MIT, idea-only) +
*LangGraph* checkpoint shape → a unified `ScenarioEvent` (one model, F1 writes / F2 reads). `parent_id` turns
the linear log into a branching graph; `status=rejected` drives dotted edges. Because the engine is seeded,
**replay is free and deterministic**, and **fork** (clone a checkpoint, change one belief, re-run) is exactly
F2's branch material. One `scenarios` store collection — that's the *only* durable new collection MVP needs.

---

## 5. Phase 3 — F2 mermaid branching graph + self-authored markdown

`osfl/engine/mermaid.py` — a pure `ScenarioRun → "graph TD …"` function.

**The borrow:** *LangGraph `draw_mermaid`* edge rule (MIT, port ~40 lines, don't install): solid `-- label -->`
for the taken path, dotted `-. label .->` for rejected branches; `_to_safe_id()` sanitizer; `classDef`
per node kind (taken=green, rejected=red-dashed, rag=blue, state=gray); `linkStyle` paints the chosen path.
Deterministic `(day,id)` ordering, no clock/random. Plus a `scenario_to_markdown` wrapper so **OSFL literally
writes the `simulate_alex_job.md` artifact** (narrative + fenced mermaid + timeline table), offline.

**Vendor:** `static/mermaid.esm.min.mjs` (MIT) rendered client-side with `securityLevel:'strict'`,
`startOnLoad:false` — the one new browser asset, following the existing `tailwind.js`/`alpine.min.js`
convention. The deterministic engine runs and is unit-testable with mermaid **absent** (golden-string test).

---

## 6. Phase 4 — Dashboard panels + the additive LLM layer (lowest risk, last)

New Alpine/Tailwind panels: scenario timeline (beat cards with `rejected_alternatives` expanders, morale/
runway bars), scenario journey (mermaid render + download `.md`), wellbeing morale/energy bars + burnout chip,
serendipity base-vs-events overlay. All gated on `llm.available` with template fallbacks (the proven
`Persona`/`Advisor` pattern).

**Persona voice quick win (do anytime, ~15 lines, highest-leverage mirror upgrade):** *Character-Card-spec-v3*
`mes_example`/`<START>` few-shot block + `post_history_instructions` trailer (MIT V3 spec; never SillyTavern's
AGPL JS) — inject 2–4 real you-written snippets into `voice.py` and re-assert hard constraints
(banned_words, emoji_rate) as the **last** prompt segment so they survive long context.

**Additive LLM (each with deterministic fallback, never produces a number that flows into the math):**
Strategist `_llm_rerank` (bounded tie-break within a 0.05 score band, can't pick a dominated move),
`_narrate`/`_finish` prose, `BabyAGI`-style replan prompts (MIT v0.1.0 tag). **Hard rule:** the LLM never
produces a number entering the Monte-Carlo, tilt, morale, serendipity, or move choice — only prose and
tie-break ordering within a proven-safe band.

---

## 7. The borrow ledger (confirmed best bets)

| # | Idea | Source (license) | Mode | OSFL target | ~Lines |
|---|------|------------------|------|-------------|--------|
| 1 | Handoff-as-return-value bounded loop | OpenAI Swarm/Agents SDK (MIT) | copy-idea | F1 `osfl/scenario.py` | 40 |
| 2 | Propose-vs-resolve (engine = resolver) | DeepMind Concordia (Apache-2.0) | copy-idea | F1 tick body | 30 |
| 3 | Composable termination predicates | AutoGen (CC-BY → idea-only) | copy-idea | F1 loop guard | 15 |
| 4 | RunEvent `{id,parent_id,kind,status,seed}` | AgentOps + LangGraph (MIT, idea-only) | copy-idea | F1→F2 bridge, `models.py` | 25 |
| 5 | `draw_mermaid` solid/dotted edge rule | LangGraph (MIT) | copy-idea | F2 `engine/mermaid.py` | 80 |
| 6 | Mermaid browser bundle | mermaid-js (MIT) | **vendor** | `static/` | 1 file |
| 7 | Empirical-Bayes layered prior | D. Robinson (public math) | copy-idea | cold-start `engine/priors.py` | 30 |
| 8 | EMA state + MBI 3-factor | uhabits (GPL→idea) + MBI (public) | copy-idea | F5 `engine/wellbeing.py` | 40 |
| 9 | Rung enum + NOOP-logs + retry budget | guardrails-ai (Apache-2.0) | copy-idea | `osfl/guidance.py` | 30 |
| 10 | YAML-category → typed pydantic policy | NeMo-Guardrails (Apache-2.0) | copy-idea | `guidance.yaml` | 20 |
| 11 | Deny-overrides precedence | Cerbos (Apache-2.0) | copy-idea | guidance resolver | 20 |
| 12 | HumanInterrupt/consent record | LangGraph (MIT) | copy-idea | require-ack rung | 40 |
| 13 | Two-component seeded luck mixture | rare-event std / bayesian-testing (MIT) | copy-idea | F4 resolve step | 10 |
| 14 | Thompson sampling + ToT simulate-then-select | MABWiser (Apache) + ToT (MIT) | copy-idea | F1 pivot | 40 |
| 15 | Character-Card few-shot + post-history | Card spec v3 (MIT) | copy-idea | `persona/voice.py` | 15 |
| 16 | P(best)/expected-loss decision metrics | bayesian-testing (MIT) | **vendor** | `engine/decision.py` (queue) | 30 |

**No new pip dependency is added anywhere.** Only two *vendored files* (mermaid bundle; optional
bayesian-testing snippet), both following the established local-vendor convention.

---

## 8. What we deliberately do NOT adopt (and why)

- **Framework imports** (LangGraph, CrewAI, AutoGen, Swarm, pydantic-graph, langchain): heavy transitive deps
  + LLM-tool-call plumbing → break offline-first. Copy the 20–80-line pattern instead.
- **F3 memory stack** (mem0 → qdrant+sqlalchemy+posthog telemetry; cognee/unstructured/Graphiti/Zep → mandatory
  vector/graph DBs): violate one-JSON-store + minimal-deps. **Deferred to Phase 5**; MVP hardcodes Alex's profile.
- **PyMC / Vowpal Wabbit**: MCMC/C++ builds, massively over-scoped vs the closed-form Empirical-Bayes we use.
- **graphviz** (needs system `dot`, emits static images, can't render in-browser) · **AgentOps SDK** (phones
  home to a cloud dashboard) — both break offline; we copy only their *schema idea*.
- **VADER** (~1 MB lexicon): premature — the EMA cynicism axis works without it. Cut until notes carry signal.
- **Polish tier** (SM-2 adaptive cadence, FSRS decay, LLMCompiler `$N` grammar, GTPyhop method-registry,
  Letta Block, Graphiti bi-temporal): each individually cheap but gated **behind "core 7 shipped."**

---

## 9. Risk register (top items)

| Sev | Risk | Mitigation |
|-----|------|-----------|
| HIGH | Magic-seed arc (reproducible but not representative) | Beats from deterministic forecast fns; sample only discrete outcomes; **5-seed-sweep test** on the qualitative arc |
| HIGH | Runner mutates live goals via `Simulator.run`/`Memory.log`/`Planner` upserts | Deep copies; `ARCHETYPES` as data only; **whole-store byte-equality** guard test |
| HIGH | Schema fork F1↔F2 | One unified `ScenarioEvent` (F1 writes, F2 reads); validate the graph against a real run |
| MED | Serendipity reads as cheating | Counterfactual framing (`p_base`/`p_strategy`/`luck_share`), capped contribution, fired-flag |
| MED | Mermaid unreadable at 90 days | **Beats not ticks** (~5–10 nodes); MVP, not deferred |
| MED | Weak prior + eager ladder nags where least sure | `classify()` caps rung at `warn` when `prior_layer != user_posterior` |
| MED | ProofWindow on an irreversible action | Default-deny: only open on known-reversible shot types (messages/sessions); else cap at require-ack |
| LOW | Backward-compat on boot re-persist | All new model fields defaulted; "byte-green" = engine **test numbers**, not `store.json` bytes |

---

## 10. Start here — the smallest first slice (≈1.5–2 days)

Prove the **entire claim** ("OSFL self-authors a branching, narrative, offline, deterministic-AND-meaningful
scenario") before committing to morale/serendipity/ingestion/UI/LLM:

1. `ScenarioRun` + `ScenarioEvent` in `models.py`; `scenarios` in `store.COLLECTIONS`/`_default_doc()` (one edit).
2. Hardcode an Alex `ScenarioProfile` + 3 plays (cold-channel, warm-intro pivot, moonshot) as literal data in `seed.py`.
3. `osfl/scenario.py`: a **beat-emitting** loop on **deep copies** (never `Simulator.run`/`Memory.log`), using
   deterministic `point_estimate_p`/`find_bottleneck` to decide when the cold channel collapses (→ a `pivot`
   beat with the rejected cold-channel in `rejected_alternatives`), one child RNG stream for the discrete
   outcome, the existing outcome-fold for a `crisis` beat, a terminal `win/fail` beat. Persist one `ScenarioRun`.
4. `engine/mermaid.py`: `scenario_to_mermaid(run)` with green/red-dashed/gray `classDef`s over those ~6 beats.
5. `POST /api/scenario/simulate` + `GET /api/scenario/{id}/graph`.

**Tests:** (a) does-NOT-mutate-store (whole-doc byte-equal); (b) two runs at `seed=42` byte-identical;
(c) 5-seed sweep — pivot + crisis + terminal beats all present; (d) golden mermaid string.

Everything else (Phase 1 cores, the full guidance ladder, mermaid-in-browser, LLM polish) is an **additive
layer on a proven spine.**

---

## 11. Sequencing & effort

```
Phase 0a  Cold-start priors            ~0.5–1 day   (prereq; isolated, high-value)
Phase 0b  Mirror-vs-guide policy       ~1–1.5 day   (prereq; depends on 0a's forecast)
Phase 1   F5 morale + F4 luck + tilt   ~2 days      (parallel; standalone-valuable)
Phase 2   F1 ScenarioRunner            ~2 days      (keystone; the smallest-slice lands here first)
Phase 3   F2 mermaid + export.md       ~1 day       (pure consumer)
Phase 4   UI panels + additive LLM     ~2 days      (lowest risk, last)
Phase 5   Full F3 ingestion (future)   —            (deferred: retires the hardcoded profile)
```

The cut line is principled: **MVP = everything the deterministic engine can do offline; FULL = everything
the optional LLM and richer-but-deferrable mechanics add on top.** ~60 new tests on the 25 that stay green.
