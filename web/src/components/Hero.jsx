import { motion } from "framer-motion";
import PhoneDemo from "./PhoneDemo.jsx";

const rise = (d) => ({
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, delay: d, ease: [0.22, 1, 0.36, 1] },
});

export default function Hero() {
  return (
    <section id="top" className="sec" style={{ paddingTop: "clamp(48px, 7vw, 96px)", paddingBottom: "clamp(56px, 8vw, 120px)" }}>
      <div
        className="wrap"
        style={{ display: "grid", gridTemplateColumns: "minmax(0,1.05fr) minmax(0,0.95fr)", gap: "clamp(28px, 5vw, 72px)", alignItems: "center" }}
      >
        {/* left copy */}
        <div>
          <motion.div {...rise(0)} className="eyebrow">OS&nbsp;FOR&nbsp;LIFE · v0.1 · open-source</motion.div>
          <motion.h1 {...rise(0.08)} className="display h1" style={{ marginTop: 18 }}>
            Your life runs<br />on odds.{" "}
            <em style={{ color: "var(--primary)" }}>Forecast&nbsp;them.</em>
          </motion.h1>
          <motion.p {...rise(0.18)} className="lead" style={{ marginTop: 22 }}>
            OSFL is the operating system for a high-variance life. It models{" "}
            <span className="num">outcome = probability × volume</span>, forecasts your real
            odds with a Monte-Carlo engine, learns <em>who you are</em>, and acts in your voice.
          </motion.p>
          <motion.div {...rise(0.28)} style={{ display: "flex", gap: 12, marginTop: 30, flexWrap: "wrap" }}>
            <a href="#sim" className="btn btn-primary">See the forecast →</a>
            <a href="https://github.com/Akasxh/OSFL" target="_blank" rel="noreferrer" className="btn btn-ghost">Read the math</a>
          </motion.div>
          <motion.div {...rise(0.38)} style={{ display: "flex", gap: 20, marginTop: 34, flexWrap: "wrap" }}>
            {[
              ["P(≥1 offer)", "0.382"],
              ["min volume → 80%", "n=201"],
              ["your rate", "8% → 12.7%"],
            ].map(([k, v]) => (
              <div key={k}>
                <div className="num" style={{ fontSize: "1.4rem", color: "var(--ink)" }}>{v}</div>
                <div className="eyebrow" style={{ fontSize: "0.62rem" }}>{k}</div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* right phone */}
        <motion.div
          initial={{ opacity: 0, y: 24, rotate: -1 }}
          animate={{ opacity: 1, y: 0, rotate: 0 }}
          transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          style={{ display: "flex", justifyContent: "center" }}
        >
          <PhoneDemo />
        </motion.div>
      </div>
    </section>
  );
}
