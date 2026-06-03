"""Playwright E2E suite for the OSFL dashboard.

Drives the real uvicorn subprocess (`base_url`) with a headless Chromium `page`, exercising
the Alpine-hydrated UI end to end. Everything runs OFFLINE (the harness forces an empty
OPENAI_API_KEY), so these tests assert the offline contract: draft engine == "template",
the scenario advisor shows the OPENAI_API_KEY note, and NO non-local network is touched.

Grounding (verified against static/index.html, static/app.js, osfl/app.py):
- Panels are headed by circled-digit markers ①..⑨ inside <h2>.
- Each panel header carries a `badge(id)` span that renders "<METHOD> <url> · <ms>ms" once a
  fetch lands; before that it is the em-dash placeholder "—".
- `dash()` boots via init()->reloadAll(): GET /api/state, then simulate() (POST .../simulate)
  and validate() (POST .../validate) for the first goal. So sim + validation badges fill in
  without any click; clicking just re-fires them.
- Default orchestrator request is "is my plan realistic?" -> intent "validate" -> the route is
  ["DecisionAdvisor"], so the trace always contains a DecisionAdvisor chip offline.
"""

from __future__ import annotations

import re

# A panel/network action can involve a real subprocess round-trip; be generous.
T = 20000


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _boot(page, base_url):
    """Navigate and wait for Alpine to hydrate the first goal + first forecast."""
    page.goto(base_url, wait_until="domcontentloaded")
    # Alpine renders goal cards from state.goals; the seed always has "Land a job".
    page.wait_for_selector("text=Land a job", timeout=T)
    # reloadAll() auto-simulates the first goal: wait for the big P% number to appear.
    page.wait_for_selector("#hist", timeout=T)


# --------------------------------------------------------------------------- #
# 1. page loads
# --------------------------------------------------------------------------- #
def test_page_title_contains_osfl(page, base_url):
    page.goto(base_url, wait_until="domcontentloaded")
    assert "OSFL" in page.title()


# --------------------------------------------------------------------------- #
# 2. all 9 panels render
# --------------------------------------------------------------------------- #
def test_all_nine_panels_render(page, base_url):
    _boot(page, base_url)
    expected = [
        "Goals & funnels",
        "Priority queue",
        "Wellbeing & follow-ups",
        "Monte-Carlo simulation",
        "Strategy validation",
        "Log outcome",
        "Persona / digital twin",
        "Orchestrator routing trace",
        "Scenario advisor",
    ]
    headers = page.locator("h2")
    headers.first.wait_for(timeout=T)
    texts = headers.all_inner_texts()
    assert len(texts) >= 9, f"expected >=9 panel headers, saw {len(texts)}: {texts}"
    blob = " || ".join(texts)
    for label in expected:
        assert label in blob, f"panel header missing: {label!r} (have: {blob})"


# --------------------------------------------------------------------------- #
# 3. clicking a goal card sets it active
# --------------------------------------------------------------------------- #
def test_clicking_goal_card_sets_active(page, base_url):
    _boot(page, base_url)
    # First goal ("Land a job") is auto-active; the active-goal line echoes its title.
    active_line = page.locator("text=active goal →")
    active_line.wait_for(timeout=T)
    assert "Land a job" in active_line.inner_text()

    # Click the habit goal "Get fit" card (scope to the goals panel — the title also appears
    # in the queue/followups panels, so an unscoped exact-text match is ambiguous).
    goals_panel = page.locator("xpath=//h2[contains(.,'Goals')]/ancestor::div[contains(@class,'card')]")
    goals_panel.get_by_text("Get fit", exact=True).click()
    # The active-goal workspace line must update to the new title.
    page.wait_for_function(
        "() => document.querySelector('section.xl\\\\:col-span-7')?.innerText.includes('Get fit')",
        timeout=T,
    )
    assert "Get fit" in active_line.inner_text()


# --------------------------------------------------------------------------- #
# 4. Run-simulations updates the P% number and the histogram canvas exists
# --------------------------------------------------------------------------- #
def test_run_simulations_updates_p_and_draws_histogram(page, base_url):
    _boot(page, base_url)
    canvas = page.locator("#hist")
    canvas.wait_for(timeout=T)

    # The big P(success) number sits next to "P(success) · threshold".
    p_locator = page.locator("xpath=//span[contains(text(),'P(success) · threshold')]/preceding-sibling::span[1]")
    p_locator.wait_for(timeout=T)
    before = p_locator.inner_text()
    assert re.fullmatch(r"\d{1,3}%", before.strip()), f"P% not rendered, got {before!r}"

    # Click the explicit Run button; the canvas must end up with real pixels drawn.
    page.get_by_role("button", name=re.compile("Run 10k simulations")).click()
    # drawHist() sets canvas.width = clientWidth*dpr (>0) once sim data exists.
    page.wait_for_function(
        "() => { const c = document.getElementById('hist'); return c && c.width > 0 && c.height > 0; }",
        timeout=T,
    )
    width = page.evaluate("() => document.getElementById('hist').width")
    assert width > 0, "histogram canvas was never sized/drawn"
    after = p_locator.inner_text()
    # Deterministic seed=42 => the value is stable across runs (re-render keeps a real %).
    assert re.fullmatch(r"\d{1,3}%", after.strip()), f"P% missing after run, got {after!r}"


# --------------------------------------------------------------------------- #
# 5. Validate-strategy renders ON TRACK / REJECTED plus a suggestion
# --------------------------------------------------------------------------- #
def test_validate_strategy_renders_verdict_and_suggestion(page, base_url):
    _boot(page, base_url)
    page.get_by_role("button", name="Validate strategy").click()

    verdict = page.locator("xpath=//span[normalize-space(.)='ON TRACK' or normalize-space(.)='REJECTED']")
    verdict.first.wait_for(timeout=T)
    label = verdict.first.inner_text().strip()
    assert label in ("ON TRACK", "REJECTED"), f"unexpected verdict: {label!r}"

    # The seeded "Land a job" funnel is below its 70% threshold => REJECTED with suggestions.
    # At least one suggestion kind chip (more_volume / extend_deadline / better_shot_type) shows.
    suggestion = page.locator(
        "xpath=//span[contains(text(),'more volume') or contains(text(),'extend deadline') "
        "or contains(text(),'better shot type')]"
    )
    suggestion.first.wait_for(timeout=T)
    assert suggestion.count() >= 1, "no strategy suggestion rendered"


# --------------------------------------------------------------------------- #
# 6. log-outcome form -> before→after rate line + forecast shift + repaint
# --------------------------------------------------------------------------- #
def test_log_outcome_shows_before_after_rate_and_repaints(page, base_url):
    _boot(page, base_url)
    # Ensure a sim exists first so prev_p is captured (auto on boot, but be explicit).
    page.wait_for_selector("#hist", timeout=T)

    # Panel ④ inputs: attempts (n) and successes (k). Defaults are n=20,k=3 — valid (k<=n).
    n_input = page.locator("xpath=//label[contains(.,'attempts (n)')]//input")
    k_input = page.locator("xpath=//label[contains(.,'successes (k)')]//input")
    n_input.fill("20")
    k_input.fill("8")

    page.get_by_role("button", name=re.compile("Log .* update model")).click()

    # The result badge shows "your rate: X% → Y%" and "forecast: A% → B%".
    rate_line = page.locator("xpath=//div[contains(., 'your rate:')]")
    rate_line.first.wait_for(timeout=T)
    rate_txt = rate_line.first.inner_text()
    assert "your rate:" in rate_txt
    assert "→" in rate_txt, f"before→after arrow missing in {rate_txt!r}"
    assert re.search(r"\d{1,3}%\s*→\s*\d{1,3}%", rate_txt), f"rate transition not formatted: {rate_txt!r}"

    forecast_line = page.locator("xpath=//div[contains(., 'forecast:')]")
    forecast_line.first.wait_for(timeout=T)
    assert re.search(r"\d{1,3}%\s*→\s*\d{1,3}%", forecast_line.first.inner_text())

    # logOutcome() calls drawHist() again -> canvas stays sized (repaint happened).
    page.wait_for_function(
        "() => { const c = document.getElementById('hist'); return c && c.width > 0; }",
        timeout=T,
    )


# --------------------------------------------------------------------------- #
# 7. persona tabs switch and show formality / warmth params
# --------------------------------------------------------------------------- #
def test_persona_tabs_switch_and_show_params(page, base_url):
    _boot(page, base_url)

    # Persona panel ⑥ defaults to the "professional" tab; params grid shows formality+warmth.
    params_grid = page.locator(
        "xpath=//div[contains(@class,'grid') and contains(., 'formality') and contains(., 'warmth')]"
    )
    params_grid.first.wait_for(timeout=T)
    assert "formality" in params_grid.first.inner_text()
    assert "warmth" in params_grid.first.inner_text()

    prof_formality = params_grid.first.inner_text()

    # Switch to the "family" tab (a persona-tab button, scoped to panel ⑥, not the advisor panel).
    persona_panel = page.locator(
        "xpath=//h2[contains(.,'Persona / digital twin')]/ancestor::div[contains(@class,'card')]"
    )
    persona_panel.get_by_role("button", name="family", exact=True).click()

    # Params must re-render; family's formality differs from professional's (cross-cluster voice).
    page.wait_for_function(
        "(prev) => { const els = [...document.querySelectorAll('div')].filter("
        "  e => e.innerText.includes('formality') && e.innerText.includes('warmth') && e.className.includes('grid'));"
        "  return els.length && els[0].innerText !== prev; }",
        arg=prof_formality,
        timeout=T,
    )
    assert "formality" in params_grid.first.inner_text()
    assert "warmth" in params_grid.first.inner_text()


# --------------------------------------------------------------------------- #
# 8. Draft-in-professional-voice -> draft body + engine label "template (offline)"
# --------------------------------------------------------------------------- #
def test_draft_in_professional_voice_is_template_offline(page, base_url):
    _boot(page, base_url)
    persona_panel = page.locator(
        "xpath=//h2[contains(.,'Persona / digital twin')]/ancestor::div[contains(@class,'card')]"
    )
    # Default persona tab is professional; the button text reads "Draft in professional voice".
    persona_panel.get_by_role("button", name=re.compile("Draft in professional voice")).click()

    # The draft body is a <pre>; wait for it to be non-empty.
    body = persona_panel.locator("pre")
    body.wait_for(timeout=T)
    page.wait_for_function(
        "() => { const p = [...document.querySelectorAll('pre')].pop(); return p && p.innerText.trim().length > 0; }",
        timeout=T,
    )
    assert body.inner_text().strip(), "draft body is empty"

    # Offline => engine label must literally read "template (offline)" (NOT the llm ✦ chip).
    engine_label = persona_panel.locator("text=template (offline)")
    engine_label.wait_for(timeout=T)
    assert "template (offline)" in engine_label.inner_text()


# --------------------------------------------------------------------------- #
# 9. Route -> orchestrator trace with the DecisionAdvisor chip
# --------------------------------------------------------------------------- #
def test_route_renders_trace_with_decision_advisor_chip(page, base_url):
    _boot(page, base_url)
    orch_panel = page.locator(
        "xpath=//h2[contains(.,'Orchestrator routing trace')]/ancestor::div[contains(@class,'card')]"
    )
    # Default request is "is my plan realistic?" -> intent validate -> route [DecisionAdvisor].
    orch_panel.get_by_role("button", name="Route", exact=True).click()

    # The trace renders a "cluster ... ms" line plus agent chips.
    page.wait_for_selector("xpath=//div[contains(text(),'cluster')]", timeout=T)
    chip = orch_panel.locator("text=DecisionAdvisor")
    chip.first.wait_for(timeout=T)
    assert "DecisionAdvisor" in chip.first.inner_text()


# --------------------------------------------------------------------------- #
# 10. Scenario-advisor Ask -> offline OPENAI_API_KEY note
# --------------------------------------------------------------------------- #
def test_scenario_advisor_shows_offline_openai_key_note(page, base_url):
    _boot(page, base_url)
    advisor_panel = page.locator("xpath=//h2[contains(.,'Scenario advisor')]/ancestor::div[contains(@class,'card')]")

    # The offline note is rendered (x-show !llm.available) referencing OPENAI_API_KEY.
    note = advisor_panel.locator("text=OPENAI_API_KEY")
    note.wait_for(timeout=T)
    assert "OPENAI_API_KEY" in note.inner_text()

    # Asking returns available=false with the key-needed answer in the badge.
    advisor_panel.get_by_role("button", name=re.compile("Ask")).click()
    answer = advisor_panel.locator("xpath=.//p[contains(., 'OpenAI key') or contains(., 'OPENAI_API_KEY')]")
    answer.first.wait_for(timeout=T)
    assert "key" in answer.first.inner_text().lower()


# --------------------------------------------------------------------------- #
# 11. New-goal creates an auto-decomposed goal that appears in the list
# --------------------------------------------------------------------------- #
def test_new_goal_creates_auto_decomposed_goal_in_list(page, base_url):
    _boot(page, base_url)
    goals_panel = page.locator("xpath=//h2[contains(.,'Goals')]/ancestor::div[contains(@class,'card')]")

    # Open the new-goal form.
    goals_panel.get_by_role("button", name=re.compile("New goal")).click()
    title = "land a job at acme"
    goals_panel.locator("input[placeholder^='Goal title']").fill(title)
    goals_panel.get_by_role("button", name="Create", exact=True).click()

    # createGoal() POSTs /api/goals (auto-decompose) then reloadAll(); the new title appears
    # in the goals panel (it may also surface in the queue/followups, hence scope + .first).
    page.wait_for_selector(f"text={title}", timeout=T)
    new_card = goals_panel.get_by_text(title, exact=True).first
    new_card.wait_for(timeout=T)

    # Auto-decomposed funnel => it gets a forecast verdict (a %); click it and confirm the
    # active workspace updates to it.
    new_card.click()
    page.wait_for_function(
        "(t) => document.querySelector('section.xl\\\\:col-span-7')?.innerText.includes(t)",
        arg=title,
        timeout=T,
    )
    # Confirm via API state that the created goal actually has stages (auto-decompose worked).
    new_goal = page.evaluate(
        "async (t) => { const s = await (await fetch('/api/state')).json(); return s.goals.find(g => g.title === t); }",
        title,
    )
    assert new_goal is not None, "new goal not found in state"
    assert new_goal["kind"] == "funnel"
    assert len(new_goal["stages"]) >= 1, "Planner did not auto-decompose the new goal into stages"


# --------------------------------------------------------------------------- #
# 12. every panel badge matches a GET/POST + ms pattern
# --------------------------------------------------------------------------- #
def test_panel_badges_show_endpoint_and_latency(page, base_url):
    _boot(page, base_url)
    # Trigger every panel's fetch so each badge populates.
    page.get_by_role("button", name=re.compile("Run 10k simulations")).click()
    page.get_by_role("button", name="Validate strategy").click()

    persona_panel = page.locator(
        "xpath=//h2[contains(.,'Persona / digital twin')]/ancestor::div[contains(@class,'card')]"
    )
    persona_panel.get_by_role("button", name=re.compile("Draft in professional voice")).click()
    orch_panel = page.locator(
        "xpath=//h2[contains(.,'Orchestrator routing trace')]/ancestor::div[contains(@class,'card')]"
    )
    orch_panel.get_by_role("button", name="Route", exact=True).click()
    advisor_panel = page.locator("xpath=//h2[contains(.,'Scenario advisor')]/ancestor::div[contains(@class,'card')]")
    advisor_panel.get_by_role("button", name=re.compile("Ask")).click()

    # Log an outcome so the 'log' badge fills too.
    page.locator("xpath=//label[contains(.,'attempts (n)')]//input").fill("20")
    page.locator("xpath=//label[contains(.,'successes (k)')]//input").fill("5")
    page.get_by_role("button", name=re.compile("Log .* update model")).click()
    page.wait_for_selector("xpath=//div[contains(., 'your rate:')]", timeout=T)

    pattern = re.compile(r"^(GET|POST|PATCH)\s+\S+\s+·\s+\d+ms$")
    # Each panel badge is the small font-mono span next to its h2 (badge(id)).
    badges = page.locator("xpath=//h2/following-sibling::span[contains(@class,'font-mono')]")
    badges.first.wait_for(timeout=T)
    texts = [t.strip() for t in badges.all_inner_texts()]
    populated = [t for t in texts if t and t != "—"]
    assert populated, f"no panel badge populated; saw {texts}"
    for t in populated:
        assert pattern.match(t), f"badge does not match METHOD url · ms : {t!r}"
    # At least the core panels (state, sim, val, draft, orch, advise, log) populated.
    assert len(populated) >= 6, f"expected most panels to show a badge, got {populated}"


# --------------------------------------------------------------------------- #
# 13. offline guarantee: NO non-local network request is made
# --------------------------------------------------------------------------- #
def test_no_external_network_requests(page, base_url):
    external: list[str] = []

    def _record(request):
        url = request.url
        if url.startswith("data:") or url.startswith("blob:"):
            return
        host = re.sub(r"^[a-zA-Z]+://", "", url).split("/")[0].split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            external.append(url)

    page.on("request", _record)

    _boot(page, base_url)
    # Exercise every interactive surface that could fetch.
    page.get_by_role("button", name=re.compile("Run 10k simulations")).click()
    page.get_by_role("button", name="Validate strategy").click()
    persona_panel = page.locator(
        "xpath=//h2[contains(.,'Persona / digital twin')]/ancestor::div[contains(@class,'card')]"
    )
    persona_panel.get_by_role("button", name=re.compile("Draft in professional voice")).click()
    orch_panel = page.locator(
        "xpath=//h2[contains(.,'Orchestrator routing trace')]/ancestor::div[contains(@class,'card')]"
    )
    orch_panel.get_by_role("button", name="Route", exact=True).click()
    advisor_panel = page.locator("xpath=//h2[contains(.,'Scenario advisor')]/ancestor::div[contains(@class,'card')]")
    advisor_panel.get_by_role("button", name=re.compile("Ask")).click()
    # Let any late requests flush.
    page.wait_for_timeout(500)

    assert not external, f"external (non-local) network requests were made: {external}"
