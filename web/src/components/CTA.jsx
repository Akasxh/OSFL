import Reveal from "./ui/Reveal.jsx";

export default function CTA() {
  return (
    <section className="sec">
      <div className="wrap">
        <Reveal>
          <div style={{ display: "flex", justifyContent: "center", marginBottom: "clamp(28px,4vw,48px)" }}>
            <div className="panel" style={{ position: "relative", maxWidth: 520, width: "100%", padding: "20px 22px", borderRadius: "var(--r-lg)", borderLeft: "3px solid var(--win)" }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.14em", color: "var(--win)", marginBottom: 12 }}>● THE SHOT LANDED — 6 DAYS LATER</div>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ flex: "none", width: 36, height: 36, borderRadius: 10, background: "var(--win)", color: "#08110a", display: "grid", placeItems: "center", fontWeight: 700, fontFamily: "var(--font-ui)" }}>G</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                    <span style={{ fontWeight: 600, color: "var(--panel-ink)", fontSize: "0.95rem" }}>Google · Recruiter</span>
                    <span className="mono" style={{ fontSize: 10, color: "var(--panel-muted)" }}>Re: TPU roadmap</span>
                  </div>
                  <p style={{ margin: "7px 0 0", fontSize: "0.96rem", lineHeight: 1.5, color: "var(--panel-muted)" }}>
                    "Love this — exactly the work we're scaling. Are you free <span style={{ color: "var(--win)", fontWeight: 500 }}>Thursday 2pm</span> to meet the TPU team?"
                  </p>
                </div>
              </div>
              <div className="mono" style={{ fontSize: 10.5, color: "var(--panel-muted)", marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--panel-line)" }}>
                1 of 27 shots · the model predicted 12.7% · <span style={{ color: "var(--panel-ink)" }}>this is a shot that counted.</span>
              </div>
            </div>
          </div>
          <div className="panel panel-vignette graticule" style={{ padding: "clamp(40px,7vw,84px) clamp(24px,5vw,72px)", textAlign: "center", borderLeft: "3px solid var(--accent)" }}>
            <h2 className="display" style={{ fontSize: "clamp(2.4rem,6vw,4.4rem)", color: "var(--panel-ink)", lineHeight: 1.02 }}>
              Stop guessing.<br /><em style={{ color: "var(--accent)" }}>Start forecasting.</em>
            </h2>
            <p className="lead" style={{ color: "var(--panel-muted)", margin: "22px auto 0", maxWidth: "48ch" }}>
              OSFL is open-source and runs fully offline today — a real Monte-Carlo engine, a digital twin, and one queue for a whole life.
            </p>
            <div style={{ display: "flex", gap: 12, justifyContent: "center", marginTop: 34, flexWrap: "wrap" }}>
              <a href="https://github.com/Akasxh/OSFL" target="_blank" rel="noreferrer" className="btn" style={{ background: "var(--accent)", color: "#1a1100" }}>Get OSFL on GitHub →</a>
              <a href="https://github.com/Akasxh/OSFL#run-one-command" target="_blank" rel="noreferrer" className="btn" style={{ background: "transparent", color: "var(--panel-ink)", border: "1.5px solid var(--panel-line)" }}>Read the math</a>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--panel-muted)", marginTop: 22 }}>uv sync &nbsp;·&nbsp; uv run osfl &nbsp;·&nbsp; open 127.0.0.1:8000</div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
