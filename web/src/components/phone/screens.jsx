import { motion } from "framer-motion";

/* ---------- shared bits ---------- */
const grat = {
  position: "absolute",
  inset: 0,
  opacity: 0.5,
  backgroundImage:
    "linear-gradient(var(--panel-line) 1px, transparent 1px), linear-gradient(90deg, var(--panel-line) 1px, transparent 1px)",
  backgroundSize: "22px 22px",
};
const fade = (d = 0) => ({
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, delay: d, ease: [0.22, 1, 0.36, 1] },
});
const Mono = ({ children, c = "var(--panel-muted)", s = 11, ...p }) => (
  <span style={{ fontFamily: "var(--font-mono)", fontSize: s, color: c }} {...p}>{children}</span>
);

/* ---------- 1. BOOT ---------- */
function Boot() {
  return (
    <div className="scr" style={{ alignItems: "center", justifyContent: "center", textAlign: "center" }}>
      <div style={grat} />
      <motion.div {...fade()} style={{ position: "relative" }}>
        <motion.span
          initial={{ background: "var(--loss)" }}
          animate={{ background: "var(--win)" }}
          transition={{ duration: 1.2, delay: 0.3 }}
          style={{ display: "inline-block", width: 16, height: 16, borderRadius: "50%", boxShadow: "0 0 24px var(--win)" }}
        />
        <div className="display" style={{ fontSize: 40, marginTop: 18, color: "var(--panel-ink)" }}>OSFL</div>
        <Mono s={11} c="var(--panel-muted)">outcome = probability × volume</Mono>
        <div style={{ marginTop: 22 }}><Mono s={10} c="var(--accent)">▸ booting your life kernel…</Mono></div>
      </motion.div>
    </div>
  );
}

/* ---------- 2. CONNECT ---------- */
function ConnectRow({ label, sub, glyph, delay }) {
  return (
    <motion.div
      {...fade(delay)}
      className="scr-row"
      style={{ justifyContent: "space-between", padding: "13px 14px", borderRadius: 14, background: "var(--panel-raised)", border: "1px solid var(--panel-line)" }}
    >
      <div className="scr-row">
        <span style={{ width: 30, height: 30, borderRadius: 9, background: "#0d0b15", display: "grid", placeItems: "center", fontSize: 15 }}>{glyph}</span>
        <div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{label}</div>
          <Mono s={10}>{sub}</Mono>
        </div>
      </div>
      <motion.span
        initial={{ color: "var(--accent)" }}
        animate={{ color: "var(--win)" }}
        transition={{ delay: delay + 1.1, duration: 0.4 }}
        style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}
      >
        <motion.span initial={{ opacity: 1 }} animate={{ opacity: 0 }} transition={{ delay: delay + 1.0, duration: 0.2 }} style={{ position: "absolute" }}>connect →</motion.span>
        <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: delay + 1.1, duration: 0.3 }}>✓ linked</motion.span>
      </motion.span>
    </motion.div>
  );
}
function Connect() {
  return (
    <div className="scr">
      <div style={grat} />
      <motion.div {...fade()} style={{ position: "relative" }}>
        <div className="scr-h">Build your OS, <span style={{ color: "var(--accent)" }}>Akash</span></div>
        <Mono s={10}>connect what's already you →</Mono>
      </motion.div>
      <div style={{ position: "relative", display: "grid", gap: 10, marginTop: 18 }}>
        <ConnectRow label="GitHub" sub="github.com/Akasxh" glyph="⌥" delay={0.3} />
        <ConnectRow label="Slack export" sub="3 clusters · 2,107 msgs" glyph="◍" delay={0.7} />
        <ConnectRow label="résumé.pdf" sub="IIT Patna · CERN GSoC" glyph="▤" delay={1.1} />
      </div>
      <motion.div {...fade(1.8)} style={{ position: "relative", marginTop: "auto", textAlign: "center", padding: 12, borderRadius: 12, background: "var(--primary)", color: "#fff", fontWeight: 600, fontSize: 13 }}>
        Read me →
      </motion.div>
    </div>
  );
}

/* ---------- 3. FOLDER ---------- */
const LOG = [
  "scan github.com/Akasxh",
  "  repos: 41 · commits: 3,212 · langs: 6",
  "  → JAX/TPU · LLVM/MLIR · CUDA · vLLM",
  "parse slack_export.zip · 2,107 msgs",
  "  → professional · friends · family",
  "fit persona params · build profile…",
];
function MiniCard({ title, src, stat, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, rotateY: 40, y: 10 }}
      animate={{ opacity: 1, rotateY: 0, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      style={{ padding: "10px 11px", borderRadius: 11, background: "var(--panel-raised)", border: "1px solid var(--panel-line)" }}
    >
      <Mono s={9} c="var(--accent)">{src}</Mono>
      <div style={{ fontWeight: 600, fontSize: 12, margin: "2px 0" }}>{title}</div>
      <Mono s={9}>{stat}</Mono>
    </motion.div>
  );
}
function Folder() {
  return (
    <div className="scr">
      <div style={grat} />
      <div style={{ position: "relative" }} className="scr-h">A folder of you</div>
      <div style={{ position: "relative", marginTop: 10, padding: 10, borderRadius: 10, background: "#0d0b15", border: "1px solid var(--panel-line)", minHeight: 116 }}>
        {LOG.map((l, i) => (
          <motion.div key={l} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 + i * 0.22 }}>
            <Mono s={9.5} c={i % 3 === 2 ? "var(--win)" : "var(--panel-muted)"}>{l}</Mono>
          </motion.div>
        ))}
      </div>
      <div style={{ position: "relative", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 12 }}>
        <MiniCard src="github" title="Coding style" stat="conf 0.91 · 3,212 commits" delay={1.5} />
        <MiniCard src="github" title="Collaboration" stat="conf 0.84 · 188 PRs" delay={1.75} />
        <MiniCard src="slack" title="Communication" stat="conf 0.88 · 3 clusters" delay={2.0} />
        <MiniCard src="résumé" title="Domain expertise" stat="conf 0.92 · 8 skills" delay={2.25} />
      </div>
    </div>
  );
}

/* ---------- 4. GOAL ---------- */
function Goal() {
  const text = "Land a senior TPU optimization role at Google";
  return (
    <div className="scr" style={{ justifyContent: "center" }}>
      <div style={grat} />
      <motion.div {...fade()} style={{ position: "relative" }}>
        <Mono s={10} c="var(--panel-muted)">your goal</Mono>
        <div className="display" style={{ fontSize: 26, lineHeight: 1.1, marginTop: 8, color: "var(--panel-ink)" }}>
          {text.split("").map((ch, i) => (
            <motion.span key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 + i * 0.022 }}>{ch}</motion.span>
          ))}
          <motion.span animate={{ opacity: [1, 0, 1] }} transition={{ repeat: Infinity, duration: 0.9 }} style={{ color: "var(--accent)" }}>▍</motion.span>
        </div>
        <div className="scr-row" style={{ gap: 6, marginTop: 18, flexWrap: "wrap" }}>
          {["$200k+", "1–3 months", "needs H1B"].map((c, i) => (
            <motion.span key={c} {...fade(1.4 + i * 0.15)} style={{ fontFamily: "var(--font-mono)", fontSize: 10, padding: "5px 9px", borderRadius: 999, border: "1px solid var(--panel-line)", color: "var(--panel-ink)" }}>{c}</motion.span>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

/* ---------- 5. FUNNEL ---------- */
const STAGES = [
  { name: "APPLY", rate: "8%", w: 100, surv: "60" },
  { name: "RECRUITER SCREEN", rate: "40%", w: 60, surv: "4.8" },
  { name: "ONSITE → OFFER", rate: "25%", w: 26, surv: "1.9" },
];
function Funnel() {
  return (
    <div className="scr" style={{ justifyContent: "center" }}>
      <div style={grat} />
      <div style={{ position: "relative" }} className="scr-h">The funnel</div>
      <Mono s={10}>each gate is a Beta(α,β) you can move</Mono>
      <div style={{ position: "relative", display: "grid", gap: 14, marginTop: 20 }}>
        {STAGES.map((s, i) => (
          <motion.div key={s.name} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.25 }}>
            <div className="scr-row" style={{ justifyContent: "space-between" }}>
              <Mono s={10} c="var(--panel-ink)">{s.name}</Mono>
              <Mono s={11} c={i === 0 ? "var(--accent)" : "var(--panel-muted)"}>{s.rate}</Mono>
            </div>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${s.w}%` }}
              transition={{ delay: 0.35 + i * 0.25, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
              style={{ height: 18, marginTop: 5, borderRadius: 6, background: i === 0 ? "color-mix(in srgb, var(--accent) 80%, var(--panel-deep))" : "var(--primary)" }}
            />
            <Mono s={9}>survivors → {s.surv}</Mono>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

/* ---------- 6. FORECAST ---------- */
function Forecast() {
  const N = 96;
  const dots = Array.from({ length: N }, (_, i) => i);
  return (
    <div className="scr">
      <div style={grat} />
      <div style={{ position: "relative" }} className="scr-h">Monte-Carlo · 10,000 runs</div>
      <Mono s={10}>60 applications · one dream job</Mono>
      <div style={{ position: "relative", display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gap: 4, marginTop: 14 }}>
        {dots.map((i) => {
          const isWin = (i * 31) % 100 < 32;
          return (
            <motion.span
              key={i}
              initial={{ background: "var(--miss-ink)", scale: 0.6, opacity: 0 }}
              animate={{ background: isWin ? "var(--win)" : "var(--loss)", scale: 1, opacity: isWin ? 1 : 0.55 }}
              transition={{ delay: 0.2 + (i % 12) * 0.03 + Math.floor(i / 12) * 0.05, duration: 0.3 }}
              style={{ width: "100%", aspectRatio: "1", borderRadius: "50%" }}
            />
          );
        })}
      </div>
      <div style={{ position: "relative", marginTop: "auto", display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <motion.div {...fade(1.4)} className="display" style={{ fontSize: 46, color: "var(--win)" }}>32<span style={{ fontSize: 24 }}>%</span></motion.div>
        <div style={{ textAlign: "right" }}>
          <Mono s={10} c="var(--panel-muted)">P(≥1 offer)</Mono><br />
          <Mono s={10} c="var(--accent)">need n=201 for 80%</Mono>
        </div>
      </div>
    </div>
  );
}

/* ---------- 7. BAYES ---------- */
function betaShape(a, b, xs) {
  const v = xs.map((x) => (x <= 0 || x >= 1 ? 0 : Math.exp((a - 1) * Math.log(x) + (b - 1) * Math.log(1 - x))));
  const m = Math.max(...v);
  return v.map((y) => y / m);
}
function pathFrom(vals, W, H) {
  return vals
    .map((y, i) => `${i === 0 ? "M" : "L"} ${((i / (vals.length - 1)) * W).toFixed(1)} ${(H - y * H * 0.92 - 4).toFixed(1)}`)
    .join(" ");
}
function Bayes() {
  const W = 250, H = 120;
  const xs = Array.from({ length: 48 }, (_, i) => (i / 47) * 0.45);
  const prior = pathFrom(betaShape(2, 23, xs), W, H);
  const post = pathFrom(betaShape(7, 48, xs), W, H);
  return (
    <div className="scr">
      <div style={grat} />
      <div style={{ position: "relative" }} className="scr-h">Your rate, not the average</div>
      <motion.div {...fade(0.2)}><Mono s={10}>logged · 5 replies / 30 cold emails</Mono></motion.div>
      <div style={{ position: "relative", marginTop: 12 }}>
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
          <motion.path d={prior} fill="none" stroke="var(--panel-muted)" strokeWidth="1.5" strokeDasharray="3 3"
            initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} transition={{ delay: 0.3 }} />
          <motion.path fill="none" stroke="var(--primary-bright)" strokeWidth="2.5"
            initial={{ d: prior, opacity: 0 }} animate={{ d: post, opacity: 1 }} transition={{ delay: 0.8, duration: 1.1, ease: [0.22, 1, 0.36, 1] }} />
        </svg>
      </div>
      <div style={{ position: "relative", marginTop: "auto", display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <Mono s={11} c="var(--panel-muted)">population<br /><span style={{ fontSize: 22, color: "var(--panel-ink)" }}>8.0%</span></Mono>
        <Mono s={11} c="var(--accent)">→</Mono>
        <Mono s={11} c="var(--win)">you<br /><span style={{ fontSize: 22 }}>12.7%</span></Mono>
      </div>
    </div>
  );
}

/* ---------- 8. DRAFT ---------- */
const EMAIL = "Hi — I lead TPU kernel work (vLLM upstream, LLVM/MLIR). I'd love 15 minutes on the inference-optimization roadmap. Could we find a slot this week?";
function Draft() {
  return (
    <div className="scr">
      <div style={grat} />
      <div style={{ position: "relative" }} className="scr-h">Drafted in your voice</div>
      <div className="scr-row" style={{ justifyContent: "space-between", marginTop: 4 }}>
        <Mono s={10}>to: Hiring Manager · Google TPU</Mono>
        <Mono s={9} c="var(--win)">professional</Mono>
      </div>
      <motion.div {...fade(0.3)} style={{ position: "relative", marginTop: 12, padding: 13, borderRadius: 12, background: "var(--panel-raised)", border: "1px solid var(--panel-line)", fontSize: 12.5, lineHeight: 1.5, color: "var(--panel-ink)", flex: 1 }}>
        {EMAIL.split(" ").map((w, i) => (
          <motion.span key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 + i * 0.04 }}>{w} </motion.span>
        ))}
      </motion.div>
      <motion.div {...fade(2.4)} style={{ position: "relative", marginTop: 12, display: "flex", gap: 8 }}>
        <span style={{ flex: 1, textAlign: "center", padding: 11, borderRadius: 11, background: "var(--win)", color: "#08110a", fontWeight: 600, fontSize: 13 }}>Send ↗</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, alignSelf: "center", color: "var(--accent)" }}>✦ your voice</span>
      </motion.div>
    </div>
  );
}

export const SCREENS = { boot: Boot, connect: Connect, folder: Folder, goal: Goal, funnel: Funnel, forecast: Forecast, bayes: Bayes, draft: Draft };
