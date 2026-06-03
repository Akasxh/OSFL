export default function Footer() {
  return (
    <footer style={{ borderTop: "1px solid var(--line)", background: "var(--paper-raised)", position: "relative", zIndex: 2 }}>
      <div className="wrap" style={{ paddingBlock: 48, display: "flex", flexWrap: "wrap", gap: 28, justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="scr-row" style={{ gap: 10 }}>
            <span style={{ width: 9, height: 9, borderRadius: "50%", background: "var(--win)" }} />
            <span style={{ fontWeight: 600, fontSize: "1.3rem", letterSpacing: "-0.02em" }}>OSFL</span>
          </div>
          <div className="mono" style={{ fontSize: 11, color: "var(--ink-faint)", marginTop: 8 }}>outcome = probability × volume.</div>
        </div>
        <div className="mono" style={{ display: "flex", gap: 28, fontSize: "0.78rem", color: "var(--ink-soft)", flexWrap: "wrap" }}>
          <a className="nav-link" href="#model">The Model</a>
          <a className="nav-link" href="#folder">The Folder</a>
          <a className="nav-link" href="#sim">The Sim</a>
          <a className="nav-link" href="https://github.com/Akasxh/OSFL" target="_blank" rel="noreferrer">GitHub ↗</a>
        </div>
      </div>
      <div className="wrap" style={{ paddingBottom: 28 }}>
        <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-faint)" }}>© 2026 OSFL · os for life · built in the open</div>
      </div>
    </footer>
  );
}
