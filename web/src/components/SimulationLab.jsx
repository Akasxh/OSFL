import { useEffect, useMemo, useRef, useState } from "react";
import { useInView } from "framer-motion";
import SplitSection from "./ui/SplitSection.jsx";

const PROD = 0.08 * 0.4 * 0.25;
const closedP = (n) => 1 - Math.pow(1 - PROD, n);
const mcP = (n) => Math.max(0, closedP(n) * 0.84 - 0.003);

function DotField({ p, play }) {
  const ref = useRef(null);
  const order = useMemo(() => {
    const COLS = 24, ROWS = 16, N = COLS * ROWS;
    const a = Array.from({ length: N }, (_, i) => i);
    let s = 42;
    for (let i = N - 1; i > 0; i--) { s = (s * 1103515245 + 12345) & 0x7fffffff; const j = s % (i + 1); [a[i], a[j]] = [a[j], a[i]]; }
    const rank = new Array(N); a.forEach((idx, r) => (rank[idx] = r / N));
    return { COLS, ROWS, N, rank };
  }, []);
  const target = useRef(0); const cur = useRef(0);
  useEffect(() => { target.current = play ? p : 0; }, [p, play]);
  useEffect(() => {
    const cv = ref.current; if (!cv) return undefined;
    const ctx = cv.getContext("2d");
    let raf;
    const draw = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const Wd = cv.clientWidth, Hd = cv.clientHeight;
      cv.width = Wd * dpr; cv.height = Hd * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, Wd, Hd);
      cur.current += (target.current - cur.current) * 0.08;
      const { COLS, ROWS, N, rank } = order;
      const gx = Wd / COLS, gy = Hd / ROWS, r = Math.min(gx, gy) * 0.26;
      for (let i = 0; i < N; i++) {
        const col = i % COLS, row = (i / COLS) | 0;
        const won = rank[i] < cur.current;
        ctx.beginPath();
        ctx.arc(col * gx + gx / 2, row * gy + gy / 2, won ? r * 1.15 : r, 0, 6.283);
        ctx.fillStyle = won ? "#3fd17a" : (rank[i] < 0.6 ? "rgba(229,72,77,0.5)" : "rgba(110,101,128,0.5)");
        ctx.fill();
      }
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, [order]);
  return <canvas ref={ref} style={{ width: "100%", height: "100%", display: "block" }} />;
}

const STEPS = [
  { k: "THE NAIVE GUESS", b: "60 applications feels like plenty. It's a 32% shot — a coin-flip you lose." },
  { k: "DRAG THE VOLUME", b: "Every dot is one simulated run. The emerald area is your odds — they rise, but nonlinearly." },
  { k: "THE PRICE OF 80%", b: "You need 201 shots, not 60. Volume is the only variable you actually control." },
];

export default function SimulationLab() {
  const [vol, setVol] = useState(60);
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-20% 0px", amount: 0.3 });
  const cp = closedP(vol), mp = mcP(vol);
  const surv = [vol, vol * 0.08, vol * 0.08 * 0.4, vol * 0.08 * 0.4 * 0.25];
  const step = vol < 90 ? 0 : vol <= 200 ? 1 : 2;

  return (
    <div ref={ref}>
      <SplitSection
        id="sim"
        label="§03 / LIVE FORECAST · MONTE-CARLO · 10,000 RUNS"
        title={<>Watch your odds <em>get honest.</em></>}
        lead="The number isn't a vibe — it's the engine. Drag the volume and watch it move."
        steps={STEPS}
        activeIndex={step}
      >
        <div className="scr-row" style={{ justifyContent: "space-between" }}>
          <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>OUTCOME DISTRIBUTION · n={vol}</span>
          <span className="mono" style={{ fontSize: 11, color: "var(--win)" }}>● win&nbsp;&nbsp;<span style={{ color: "var(--loss)" }}>● loss</span></span>
        </div>
        <div style={{ position: "relative", flex: 1, minHeight: 200, marginTop: 12, borderRadius: 12, overflow: "hidden", background: "#0d0b15", border: "1px solid var(--panel-line)" }}>
          <DotField p={mp} play={inView} />
        </div>

        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: 18, gap: 20, flexWrap: "wrap" }}>
          <div>
            <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>P(≥1 OFFER)</span>
            <div className="display" style={{ fontSize: "clamp(2.8rem,6vw,4rem)", color: "var(--win)", lineHeight: 1 }}>{Math.round(mp * 100)}<span style={{ fontSize: "0.45em" }}>%</span></div>
            <div className="mono" style={{ fontSize: 10.5, color: "var(--panel-muted)" }}>closed-form {Math.round(cp * 100)}% · uncertainty drops it</div>
          </div>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div className="scr-row" style={{ justifyContent: "space-between" }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--accent)" }}>VOLUME · {vol} shots</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--panel-muted)" }}>10→300</span>
            </div>
            <input type="range" min="10" max="300" value={vol} onChange={(e) => setVol(+e.target.value)} style={{ width: "100%", marginTop: 8, accentColor: "#f4a52b" }} aria-label="volume of shots" />
            <div className="scr-row" style={{ justifyContent: "space-between", marginTop: 2 }}>
              <button onClick={() => setVol(60)} className="osfl-mark mono" style={{ fontSize: 10, color: vol === 60 ? "var(--accent)" : "var(--panel-muted)" }}>60 · naive</button>
              <button onClick={() => setVol(201)} className="osfl-mark mono" style={{ fontSize: 10, color: vol === 201 ? "var(--win)" : "var(--panel-muted)" }}>201 · for 80%</button>
            </div>
            <div style={{ marginTop: 12, display: "grid", gap: 5 }}>
              {["APPLY", "SCREEN", "ONSITE", "OFFER"].map((s, i) => (
                <div key={s} className="scr-row" style={{ justifyContent: "space-between" }}>
                  <span className="mono" style={{ fontSize: 9.5, color: "var(--panel-muted)", minWidth: 48 }}>{s}</span>
                  <div style={{ flex: 1, height: 5, margin: "0 10px", borderRadius: 3, background: "var(--panel-line)", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${(surv[i] / surv[0]) * 100}%`, background: i === 3 ? "var(--win)" : "var(--primary-bright)", transition: "width .25s" }} />
                  </div>
                  <span className="num" style={{ fontSize: 10.5, color: "var(--panel-ink)", minWidth: 34, textAlign: "right" }}>{surv[i] < 10 ? surv[i].toFixed(1) : Math.round(surv[i])}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <style>{`.osfl-mark{background:none;border:0;cursor:pointer}`}</style>
      </SplitSection>
    </div>
  );
}
