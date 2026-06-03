// A hairline mono data-tape (instrument-consistent, not a chunky ticker).
const ITEMS = [
  "EVERY DOT IS A SHOT",
  "GREEN DOTS ARE WINS",
  "OUTCOME = PROBABILITY × VOLUME",
  "YOUR RATE ≠ THE AVERAGE",
  "ONE QUEUE FOR A WHOLE LIFE",
  "A PRIOR IS WHAT THE WORLD EXPECTS · A POSTERIOR IS WHAT YOU'VE PROVEN",
];
export default function Marquee() {
  const run = [...ITEMS, ...ITEMS];
  return (
    <div style={{ borderBlock: "1px solid var(--line)", background: "var(--paper-raised)", overflow: "hidden", position: "relative", zIndex: 2 }}>
      <div className="osfl-tape" style={{ display: "flex", gap: 0, whiteSpace: "nowrap", padding: "11px 0" }}>
        {run.map((t, i) => (
          <span key={i} className="mono" style={{ fontSize: 11, letterSpacing: "0.12em", color: "var(--ink-soft)", paddingInline: 26, display: "inline-flex", alignItems: "center", gap: 26 }}>
            {t}
            <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--win)" }} />
          </span>
        ))}
      </div>
      <style>{`
        .osfl-tape { width: max-content; animation: osfl-tape 38s linear infinite; }
        @keyframes osfl-tape { to { transform: translateX(-50%); } }
        @media (prefers-reduced-motion: reduce) { .osfl-tape { animation: none; } }
      `}</style>
    </div>
  );
}
