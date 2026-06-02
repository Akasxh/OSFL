// OSFL dashboard. Every fetch goes through hit(), which stamps the endpoint URL +
// latency onto the panel that rendered from it — so the UI literally shows the backend working.

function dash() {
  return {
    state: { goals: [], shot_types: [], queue: [], wellbeing: null, followups: [], personas: {} },
    activeGoalId: null,
    seed: 42,
    hits: {},
    sim: null,
    validation: null,
    logForm: { shot_type_id: '', n_attempts: 20, k_successes: 3 },
    lastLog: null,
    personaTab: 'professional',
    draftForm: { shot_type_id: '', subcluster: 'normal', name: '', use_llm: true },
    draft: null,
    orchReq: 'is my plan realistic?',
    trace: null,
    showNewGoal: false,
    newGoal: { title: '', deadline: '' },
    advice: null,
    adviceLoading: false,
    adviceForm: { question: 'Which goal should I prioritize this week, and why?', persona: 'professional' },

    // ---------- helpers ----------
    pct(x) { return (x === null || x === undefined) ? '—' : Math.round(x * 100) + '%'; },
    badge(id) { const h = this.hits[id]; return h ? `${h.url} · ${h.ms}ms` : '—'; },
    activeGoal() { return this.state.goals.find(g => g.id === this.activeGoalId); },
    verdictClass(g) {
      if (!g.last_sim) return 'text-slate-400';
      return g.last_sim.p_success >= g.threshold ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10';
    },
    barPct(survivors, n0) { return n0 ? Math.max(2, Math.min(100, survivors / n0 * 100)) : 0; },
    shotTypeOptions() {
      const g = this.activeGoal();
      const byId = Object.fromEntries(this.state.shot_types.map(s => [s.id, s]));
      if (!g) return this.state.shot_types.map(s => ({ id: s.id, label: s.name }));
      const ids = g.kind === 'funnel' ? g.stages.map(s => s.shot_type_id) : (g.shot_type_id ? [g.shot_type_id] : []);
      return ids.map(id => ({ id, label: byId[id] ? byId[id].name : id }));
    },

    async hit(id, url, opts) {
      const t = performance.now();
      const r = await fetch(url, opts);
      const ms = Math.round(performance.now() - t);
      const j = await r.json();
      const method = opts && opts.method ? opts.method + ' ' : 'GET ';
      this.hits[id] = { url: method + url, ms };
      return j;
    },
    post(id, url, body) {
      return this.hit(id, url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    },

    // ---------- lifecycle ----------
    async init() { await this.reloadAll(); },

    async reloadAll() {
      this.state = await this.hit('state', '/api/state');
      this.hits['queue'] = this.hits['wellbeing'] = this.hits['state'];
      if (!this.activeGoalId && this.state.goals.length) this.activeGoalId = this.state.goals[0].id;
      this.syncForms();
      await this.simulate();
      await this.validate();
    },

    syncForms() {
      const opts = this.shotTypeOptions();
      if (opts.length) {
        if (!this.logForm.shot_type_id) this.logForm.shot_type_id = opts[0].id;
        if (!this.draftForm.shot_type_id) this.draftForm.shot_type_id = opts[0].id;
      }
    },

    async selectGoal(id) {
      this.activeGoalId = id;
      this.lastLog = null; this.draft = null;
      this.logForm.shot_type_id = ''; this.draftForm.shot_type_id = '';
      this.syncForms();
      await this.simulate();
      await this.validate();
    },

    // ---------- actions ----------
    async simulate() {
      const g = this.activeGoal(); if (!g) return;
      this.sim = await this.post('sim', `/api/goals/${g.id}/simulate`, { seed: this.seed });
      this.$nextTick(() => this.drawHist());
    },
    async validate() {
      const g = this.activeGoal(); if (!g) return;
      this.validation = await this.post('val', `/api/goals/${g.id}/validate`, { seed: this.seed });
    },
    async logOutcome() {
      const g = this.activeGoal(); if (!g) return;
      const prevP = this.sim ? this.sim.p_success : null;
      const resp = await this.post('log', `/api/goals/${g.id}/outcomes`, {
        shot_type_id: this.logForm.shot_type_id,
        n_attempts: this.logForm.n_attempts,
        k_successes: this.logForm.k_successes,
      });
      if (resp.detail) {
        const msg = Array.isArray(resp.detail) ? resp.detail.map(e => e.msg || e).join('; ') : resp.detail;
        alert(msg); return;
      }
      this.lastLog = { before_mean: resp.before_mean, after_mean: resp.after_mean, last_sim: resp.last_sim, prev_p: prevP };
      this.sim = resp.last_sim;
      this.validation = resp.validation;
      this.state = resp.state;
      this.hits['queue'] = this.hits['wellbeing'] = this.hits['state'] = this.hits['log'];
      this.$nextTick(() => this.drawHist());
    },
    async applyFix(s) {
      const g = this.activeGoal(); if (!g) return;
      let patch = {};
      if (s.kind === 'more_volume' && this.validation) patch = { n0_volume: this.validation.min_volume_for_threshold };
      else if (s.kind === 'extend_deadline') {
        const d = new Date(g.deadline); d.setDate(d.getDate() + 30);
        patch = { deadline: d.toISOString().slice(0, 10) };
      } else return;
      await this.hit('val', `/api/goals/${g.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) });
      this.state = await this.hit('state', '/api/state');
      this.hits['queue'] = this.hits['wellbeing'] = this.hits['state'];
      await this.simulate();
      await this.validate();
    },
    async makeDraft() {
      const g = this.activeGoal();
      this.draft = await this.post('draft', '/api/draft', {
        shot_type_id: this.draftForm.shot_type_id,
        persona: this.personaTab,
        subcluster: this.draftForm.subcluster,
        context: { name: this.draftForm.name || 'there', goal_id: g ? g.id : null },
        seed: this.seed,
        use_llm: this.draftForm.use_llm,
      });
    },
    async orchestrate() {
      const g = this.activeGoal();
      this.trace = await this.post('orch', '/api/orchestrate', { request: this.orchReq, goal_id: g ? g.id : null });
    },
    async advise() {
      const g = this.activeGoal();
      this.adviceLoading = true;
      try {
        this.advice = await this.post('advise', '/api/advise', {
          question: this.adviceForm.question,
          goal_id: g ? g.id : null,
          persona: this.adviceForm.persona,
        });
      } finally {
        this.adviceLoading = false;
      }
    },
    async createGoal() {
      if (!this.newGoal.title) return;
      const deadline = this.newGoal.deadline || new Date(Date.now() + 60 * 864e5).toISOString().slice(0, 10);
      await this.post('state', '/api/goals', { title: this.newGoal.title, deadline });
      this.newGoal = { title: '', deadline: '' };
      this.showNewGoal = false;
      await this.reloadAll();
    },

    // ---------- canvas histogram ----------
    drawHist() {
      const c = document.getElementById('hist');
      if (!c || !this.sim) return;
      const dpr = window.devicePixelRatio || 1;
      const W = c.clientWidth || 480, H = 180;
      c.width = W * dpr; c.height = H * dpr; c.style.height = H + 'px';
      const ctx = c.getContext('2d'); ctx.scale(dpr, dpr); ctx.clearRect(0, 0, W, H);

      const bins = this.sim.hist_bins, target = this.sim.target, n = bins.length;
      if (!n) return;
      let maxIdx = 0;
      for (let i = n - 1; i >= 0; i--) { if (bins[i] > 0) { maxIdx = i; break; } }
      const show = Math.max(maxIdx + 1, target + 1, 5);
      const maxCount = Math.max(...bins);
      const padB = 18, plotH = H - padB, bw = W / show;

      for (let i = 0; i < show; i++) {
        const h = maxCount ? (bins[i] || 0) / maxCount * plotH : 0;
        ctx.fillStyle = i >= target ? 'rgba(16,185,129,0.78)' : 'rgba(244,63,94,0.6)';
        ctx.fillRect(i * bw + 0.5, plotH - h, Math.max(bw - 1.5, 1), h);
      }
      const tx = target * bw;
      ctx.strokeStyle = '#3b82f6'; ctx.setLineDash([4, 3]);
      ctx.beginPath(); ctx.moveTo(tx, 0); ctx.lineTo(tx, plotH); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = '#64748b'; ctx.font = '10px monospace';
      ctx.fillText('0', 2, H - 4);
      ctx.fillText(String(show - 1), W - 20, H - 4);
      ctx.fillStyle = '#3b82f6';
      ctx.fillText('target ≥' + target, Math.min(tx + 4, W - 64), 10);
    },
  };
}
window.dash = dash;
