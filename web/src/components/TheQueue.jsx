import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import SplitSection from "./ui/SplitSection.jsx";
import { QUEUE, FACTORS } from "../data/restOfStory.js";

const STEPS = [
  { k: "ONE ENGINE", b: "Career, the raise, your body, the people you love — scored on one scale, not separate apps." },
  { k: "THE SCORE", b: "impact × urgency × long-term value × the odds a single shot moves them." },
  { k: "THE NEXT THING", b: "Not a to-do list. The single highest-leverage shot you can take right now." },
];

function FactorBar({ f }) {
  return (
    <div style={{ display: "flex", height: 6, borderRadius: 3, overflow: "hidden", marginTop: 9, background: "var(--panel-line)" }}>
      {FACTORS.map(([k, c]) => (
        <motion.div key={k} title={k} initial={{ flexGrow: 0 }} whileInView={{ flexGrow: f[k] }} viewport={{ once: true }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }} style={{ flexBasis: 0, background: c, marginRight: 1 }} />
      ))}
    </div>
  );
}

export default function TheQueue() {
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-20% 0px" });
  const [scan, setScan] = useState(0);
  useEffect(() => {
    if (!inView) return undefined;
    const id = setInterval(() => setScan((s) => (s + 1) % QUEUE.length), 1800);
    return () => clearInterval(id);
  }, [inView]);

  return (
    <div ref={ref}>
      <SplitSection
        id="queue"
        label="§07 / THE PRIORITY ENGINE · ONE QUEUE · ALL OF LIFE"
        title={<>You don't have a job. You have <em>a life.</em></>}
        lead="One engine ranks every shot across every domain and hands you the single next thing."
        steps={STEPS}
        activeIndex={scan % STEPS.length}
      >
        <div className="scr-row" style={{ justifyContent: "space-between", marginBottom: 14 }}>
          <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>TODAY'S QUEUE · 4 OF 27 SURFACED</span>
          <span className="mono" style={{ fontSize: 11, color: "var(--win)" }}>● re-ranking live</span>
        </div>
        <div style={{ display: "grid", gap: 10, flex: 1 }}>
          {QUEUE.map((q, i) => (
            <div key={q.rank}
              style={{
                padding: "14px 16px", borderRadius: 14, background: "var(--panel-raised)",
                border: `1px solid ${scan === i ? q.color : "var(--panel-line)"}`,
                boxShadow: scan === i ? `0 0 0 3px color-mix(in srgb, ${q.color} 20%, transparent)` : "none",
                transition: "border-color .3s, box-shadow .3s",
              }}>
              <div className="scr-row" style={{ justifyContent: "space-between" }}>
                <span className="scr-row" style={{ gap: 10 }}>
                  <span className="num" style={{ color: "var(--panel-muted)", fontSize: 13 }}>#{q.rank}</span>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: q.color }} />
                  <span className="mono" style={{ fontSize: 10, color: "var(--panel-muted)", letterSpacing: "0.08em" }}>{q.domain}</span>
                </span>
                <span className="stat" style={{ color: "var(--win)", fontSize: "1.25rem" }}>{q.score.toFixed(2)}</span>
              </div>
              <div style={{ marginTop: 6, fontSize: "1rem", color: "var(--panel-ink)" }}>{q.task}</div>
              <FactorBar f={q.f} />
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 14, marginTop: 16, flexWrap: "wrap" }}>
          {FACTORS.map(([k, c]) => (
            <span key={k} className="scr-row" style={{ gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
              <span className="mono" style={{ fontSize: 10, color: "var(--panel-muted)" }}>{k}</span>
            </span>
          ))}
        </div>
      </SplitSection>
    </div>
  );
}
