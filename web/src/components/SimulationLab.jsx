import { useEffect, useMemo, useRef, useState } from "react";
import { useInView } from "framer-motion";
import SectionHeading from "./ui/SectionHeading.jsx";

const PROD = 0.08 * 0.4 * 0.25; // 0.008 point-estimate funnel
const closedP = (n) => 1 - Math.pow(1 - PROD, n);
// MC-with-parameter-uncertainty sits below closed-form near the floor (verified 0.32 @ 60)
const mcP = (n) => Math.max(0, closedP(n) * 0.84 - 0.003);

function DotField({ p, play }) {
  const ref = useRef(null);
  // stable shuffled order so the emerald "water-line" rises in a scattered, Monte-Carlo way
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
    const cv = ref.current; if (!cv) return;
    const ctx = cv.getContext("2d");
    let raf;
    const draw = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const W = cv.clientWidth, H = cv.clientHeight;
      cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      cur.current += (target.current - cur.current) * 0.08;
      const { COLS, ROWS, N, rank } = order;
      const gx = W / COLS, gy = H / ROWS, r = Math.min(gx, gy) * 0.26;
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

export default function SimulationLab() {
  const [vol, setVol] = useState(60);
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-20% 0px", amount: 0.3 });
  const cp = closedP(vol), mp = mcP(vol);
  const surv = [vol, vol * 0.08, vol * 0.08 * 0.4, vol * 0.08 * 0.4 * 0.25];

  return (
    <section id="sim" className="sec" ref={ref}>
      <div className="wrap">
        <SectionHeading
          label="§03 / LIVE FORECAST · MONTE-CARLO · 10,000 RUNS"
          title={<>Watch your odds <em>get honest.</em></>}
          lead="Drag the volume. Every dot is one simulated run of your funnel; the emerald area is the share that ends in a win. The number isn't a vibe — it's the engine."
          maxw="50ch"
        />

        <div className="panel panel-vignette graticule" style={{ marginTop: 44, padding: "clamp(18px,3vw,30px)", display: "grid", gridTemplateColumns: "minmax(0,1.25fr) minmax(0,1fr)", gap: "clamp(20px,3vw,40px)", alignItems: "center" }}>
          {/* dot field */}
          <div>
            <div className="scr-row" style={{ justifyContent: "space-between" }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>OUTCOME DISTRIBUTION · n={vol}</span>
              <span className="mono" style={{ fontSize: 11, color: "var(--win)" }}>● win&nbsp;&nbsp;<span style={{ color: "var(--loss)" }}>● loss</span></span>
            </div>
            <div style={{ position: "relative", aspectRatio: "24 / 16", marginTop: 12, borderRadius: 12, overflow: "hidden", background: "#0d0b15", border: "1px solid var(--panel-line)" }}>
              <DotField p={mp} play={inView} />
            </div>
          </div>

          {/* readout + controls */}
          <div style={{ color: "var(--panel-ink)" }}>
            <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>P(≥1 OFFER)</span>
            <div className="display" style={{ fontSize: "clamp(3.2rem,7vw,4.6rem)", color: "var(--win)", lineHeight: 1 }}>
              {Math.round(mp * 100)}<span style={{ fontSize: "0.45em" }}>%</span>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--panel-muted)", marginTop: 2 }}>
              closed-form {Math.round(cp * 100)}% · sampling your uncertainty drops it
            </div>

            <div style={{ marginTop: 24 }}>
              <div className="scr-row" style={{ justifyContent: "space-between" }}>
                <span className="mono" style={{ fontSize: 11, color: "var(--accent)" }}>VOLUME · {vol} shots</span>
                <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>10 → 300</span>
              </div>
              <input
                type="range" min="10" max="300" value={vol} onChange={(e) => setVol(+e.target.value)}
                style={{ width: "100%", marginTop: 8, accentColor: "#f4a52b" }}
                aria-label="volume of shots"
              />
              <div className="scr-row" style={{ justifyContent: "space-between", marginTop: 4 }}>
                <button className="mono osfl-mark" onClick={() => setVol(60)} style={{ fontSize: 10, color: vol === 60 ? "var(--accent)" : "var(--panel-muted)" }}>60 · naive</button>
                <button className="mono osfl-mark" onClick={() => setVol(201)} style={{ fontSize: 10, color: vol === 201 ? "var(--win)" : "var(--panel-muted)" }}>201 · for 80%</button>
              </div>
            </div>

            <div style={{ marginTop: 22, borderTop: "1px solid var(--panel-line)", paddingTop: 16, display: "grid", gap: 6 }}>
              {["APPLY", "SCREEN", "ONSITE", "OFFER"].map((s, i) => (
                <div key={s} className="scr-row" style={{ justifyContent: "space-between" }}>
                  <span className="mono" style={{ fontSize: 10, color: "var(--panel-muted)" }}>{s}</span>
                  <div style={{ flex: 1, height: 6, margin: "0 10px", borderRadius: 3, background: "var(--panel-line)", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${(surv[i] / surv[0]) * 100}%`, background: i === 3 ? "var(--win)" : "var(--primary-bright)", transition: "width .25s" }} />
                  </div>
                  <span className="num" style={{ fontSize: 11, color: "var(--panel-ink)", minWidth: 38, textAlign: "right" }}>{surv[i] < 10 ? surv[i].toFixed(1) : Math.round(surv[i])}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <style>{`.osfl-mark{background:none;border:0;cursor:pointer}`}</style>
    </section>
  );
}
