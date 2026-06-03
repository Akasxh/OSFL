import { motion } from "framer-motion";
import SectionHeading from "./ui/SectionHeading.jsx";
import Reveal from "./ui/Reveal.jsx";
import { QUEUE, FACTORS } from "../data/restOfStory.js";

function FactorBar({ f }) {
  const total = FACTORS.reduce((s, [k]) => s + f[k], 0);
  return (
    <div style={{ display: "flex", height: 6, borderRadius: 3, overflow: "hidden", marginTop: 9, background: "var(--panel-line)" }}>
      {FACTORS.map(([k, c]) => (
        <motion.div key={k} title={k} initial={{ flexGrow: 0 }} whileInView={{ flexGrow: f[k] }} viewport={{ once: true }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }} style={{ flexBasis: 0, background: c, marginRight: 1 }} />
      ))}
      <span style={{ display: "none" }}>{total}</span>
    </div>
  );
}

export default function TheQueue() {
  return (
    <section id="queue" className="sec">
      <div className="wrap">
        <SectionHeading
          label="§01 / THE PRIORITY ENGINE · ONE QUEUE · ALL OF LIFE"
          title={<>You don't have a job. You have <em>a life.</em></>}
          lead="Career, the raise, your body, the people you love — they don't get separate apps. One engine scores every shot across every domain by impact × urgency × long-term value × the odds it moves, and hands you the single next thing."
          maxw="56ch"
        />

        <div className="panel panel-vignette graticule" style={{ marginTop: 44, padding: "clamp(18px,3vw,30px)", display: "grid", gridTemplateColumns: "minmax(0,1.35fr) minmax(0,1fr)", gap: "clamp(20px,3vw,40px)", alignItems: "center" }}>
          {/* the ranked queue */}
          <div>
            <div className="scr-row" style={{ justifyContent: "space-between", marginBottom: 14 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>TODAY'S QUEUE · 4 OF 27 SURFACED</span>
              <span className="mono" style={{ fontSize: 11, color: "var(--win)" }}>● re-ranking live</span>
            </div>
            <div style={{ display: "grid", gap: 10 }}>
              {QUEUE.map((q, i) => (
                <Reveal key={q.rank} delay={i * 0.08}>
                  <div style={{ padding: "14px 16px", borderRadius: 14, background: "var(--panel-raised)", border: "1px solid var(--panel-line)" }}>
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
                </Reveal>
              ))}
            </div>
          </div>

          {/* the engine explainer */}
          <div style={{ color: "var(--panel-ink)" }}>
            <span className="mono" style={{ fontSize: 11, color: "var(--accent)" }}>THE SCORE</span>
            <div className="num" style={{ fontSize: "clamp(1rem,1.5vw,1.35rem)", color: "var(--panel-ink)", marginTop: 8, lineHeight: 1.5 }}>
              impact<br />× urgency<br />× long-term value<br />× Δ probability
            </div>
            <div style={{ display: "flex", gap: 14, marginTop: 20, flexWrap: "wrap" }}>
              {FACTORS.map(([k, c]) => (
                <span key={k} className="scr-row" style={{ gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
                  <span className="mono" style={{ fontSize: 10, color: "var(--panel-muted)" }}>{k}</span>
                </span>
              ))}
            </div>
            <p className="mono" style={{ fontSize: 12, lineHeight: 1.6, color: "var(--panel-muted)", marginTop: 22, borderTop: "1px solid var(--panel-line)", paddingTop: 18 }}>
              Nothing competes for your attention blindly. The gym beats the cold email when the gym moves your odds more — and the model knows which, because it's the same Beta-Binomial math underneath every domain.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
