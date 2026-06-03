import { useRef } from "react";
import { motion, useInView } from "framer-motion";

export default function Philosophy() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-15% 0px" });
  const COLS = 30, ROWS = 9, N = COLS * ROWS;
  // deterministic: ~22% become wins, scattered
  const dots = Array.from({ length: N }, (_, i) => ((i * 73 + 13) % 100) < 22);
  return (
    <section ref={ref} className="panel" style={{ borderRadius: 0, borderInline: 0, padding: "clamp(60px,9vw,110px) 0" }}>
      <div className="graticule" style={{ position: "absolute", inset: 0, opacity: 0.35 }} />
      <div className="wrap" style={{ position: "relative", textAlign: "center" }}>
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${COLS}, 1fr)`, gap: "clamp(5px,1.1vw,11px)", maxWidth: 720, margin: "0 auto 40px" }}>
          {dots.map((win, i) => (
            <motion.span
              key={i}
              initial={{ background: "var(--miss-ink)", opacity: 0.3, scale: 0.7 }}
              animate={inView ? { background: win ? "var(--win)" : (i % 4 === 0 ? "var(--loss)" : "var(--miss-ink)"), opacity: win ? 1 : 0.4, scale: 1 } : {}}
              transition={{ delay: 0.2 + (i % COLS) * 0.012 + ((i / COLS) | 0) * 0.04, duration: 0.4 }}
              style={{ width: "100%", aspectRatio: "1", borderRadius: "50%", boxShadow: win ? "0 0 10px var(--win)" : "none" }}
            />
          ))}
        </div>
        <h2 className="display" style={{ fontSize: "clamp(2.1rem,5vw,3.6rem)", color: "var(--panel-ink)", lineHeight: 1.02 }}>
          Every dot is a shot.<br /><em style={{ color: "var(--win)" }}>Green dots are wins.</em>
        </h2>
        <p className="mono" style={{ fontSize: "0.92rem", color: "var(--panel-muted)", marginTop: 20, maxWidth: "52ch", marginInline: "auto" }}>
          OSFL doesn't promise you'll win. It tells you the truth about your odds — then makes sure you take enough honest shots that the math turns green.
        </p>
      </div>
    </section>
  );
}
