import Reveal from "./ui/Reveal.jsx";

export default function CTA() {
  return (
    <section className="sec">
      <div className="wrap">
        <Reveal>
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
