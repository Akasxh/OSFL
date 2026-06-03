import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import SectionHeading from "./ui/SectionHeading.jsx";
import { ARC, DEAD_ENDS } from "../data/restOfStory.js";

const W = 1000, H = 380;
const px = (x) => (x / 100) * W;
const py = (y) => (y / 100) * H;
const takenPath = ARC.map((n, i) => `${i === 0 ? "M" : "L"} ${px(n.x).toFixed(0)} ${py(n.y).toFixed(0)}`).join(" ");
// deterministic faint "futures cloud"
const CLOUD = Array.from({ length: 46 }, (_, i) => ({ cx: ((i * 137) % 100), cy: ((i * 53 + 17) % 100), r: 2 + ((i * 31) % 3) }));

export default function TheArc() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-15% 0px" });
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (!inView) return undefined;
    const id = setInterval(() => setActive((a) => (a + 1) % ARC.length), 2000);
    return () => clearInterval(id);
  }, [inView]);

  return (
    <section id="arc" className="sec" style={{ paddingTop: 0 }} ref={ref}>
      <div className="wrap">
        <SectionHeading
          label="§02 / THE 90-DAY SCENARIO · MONTE-CARLO FUTURES"
          title={<>It plays your next 90 days, <em>before you live them.</em></>}
          lead="OSFL runs an autonomous arc as a branching graph — the strategist takes the green path, abandons the red-dashed ones, survives a crisis, and earns the win. Most futures fail; this is the one worth steering toward."
          maxw="56ch"
        />

        <div className="panel panel-vignette" style={{ marginTop: 40, padding: "clamp(16px,2.5vw,26px)" }}>
          <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", display: "block" }} role="img" aria-label="90-day scenario branching graph">
            {/* futures cloud */}
            {CLOUD.map((d, i) => (
              <circle key={i} cx={px(d.cx)} cy={py(d.cy)} r={d.r} fill="var(--panel-line)" opacity="0.5" />
            ))}
            {/* rejected dashed branches */}
            {DEAD_ENDS.map((d, i) => (
              <g key={i}>
                <motion.line x1={px(d.fromX)} y1={py(d.fromY)} x2={px(d.toX)} y2={py(d.toY)} stroke="var(--loss)" strokeWidth="2" strokeDasharray="6 6"
                  initial={{ pathLength: 0, opacity: 0 }} animate={inView ? { pathLength: 1, opacity: 0.6 } : {}} transition={{ duration: 0.8, delay: 0.6 + i * 0.4 }} />
                <text x={px(d.toX)} y={py(d.toY) + 18} fill="var(--loss)" opacity="0.7" style={{ fontFamily: "var(--font-mono)", fontSize: 13 }}>{d.label}</text>
              </g>
            ))}
            {/* taken green path */}
            <motion.path d={takenPath} fill="none" stroke="var(--win)" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"
              initial={{ pathLength: 0 }} animate={inView ? { pathLength: 1 } : {}} transition={{ duration: 3.2, ease: [0.4, 0, 0.2, 1] }} style={{ filter: "drop-shadow(0 0 8px rgba(63,209,122,0.4))" }} />
            {/* nodes */}
            {ARC.map((n, i) => (
              <g key={n.day}>
                <motion.circle cx={px(n.x)} cy={py(n.y)} r={active === i ? 13 : 9} fill="var(--panel-deep)" stroke={n.color} strokeWidth="3"
                  initial={{ scale: 0, opacity: 0 }} animate={inView ? { scale: 1, opacity: 1 } : {}} transition={{ duration: 0.4, delay: 0.4 + i * 0.62, ease: [0.22, 1, 0.36, 1] }}
                  style={{ transformOrigin: `${px(n.x)}px ${py(n.y)}px`, filter: active === i ? `drop-shadow(0 0 10px ${n.color})` : "none" }} />
                <motion.g initial={{ opacity: 0 }} animate={inView ? { opacity: 1 } : {}} transition={{ delay: 0.6 + i * 0.62 }}>
                  <text x={px(n.x)} y={py(n.y) - 22} textAnchor="middle" fill={n.color} style={{ fontFamily: "var(--font-mono)", fontSize: 13, letterSpacing: "0.04em" }}>{n.day} · {n.kind}</text>
                </motion.g>
              </g>
            ))}
          </svg>

          {/* filmstrip of the 5 beats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px,1fr))", gap: 10, marginTop: 18 }}>
            {ARC.map((n, i) => (
              <div key={n.day} style={{ padding: "12px 13px", borderRadius: 12, background: active === i ? "var(--panel-raised)" : "transparent", border: `1px solid ${active === i ? n.color : "var(--panel-line)"}`, transition: "border-color .3s, background .3s" }}>
                <div className="scr-row" style={{ gap: 7 }}>
                  <span style={{ width: 7, height: 7, borderRadius: "50%", background: n.color }} />
                  <span className="mono" style={{ fontSize: 10, color: "var(--panel-muted)" }}>{n.day} · {n.kind}</span>
                </div>
                <div style={{ fontSize: "0.92rem", color: "var(--panel-ink)", marginTop: 6 }}>{n.title}</div>
                <div className="mono" style={{ fontSize: 10, color: "var(--panel-muted)", marginTop: 5, lineHeight: 1.45, opacity: active === i ? 1 : 0.5, transition: "opacity .3s" }}>{n.note}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
