export default function Nav() {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        backdropFilter: "blur(10px)",
        background: "color-mix(in srgb, var(--paper) 82%, transparent)",
        borderBottom: "1px solid var(--line)",
      }}
    >
      <div
        className="wrap"
        style={{ display: "flex", alignItems: "center", height: 64, gap: 16 }}
      >
        <a href="#top" className="scr-row" style={{ gap: 10 }}>
          <span
            style={{ width: 9, height: 9, borderRadius: "50%", background: "var(--win)", boxShadow: "0 0 0 4px color-mix(in srgb, var(--win) 22%, transparent)" }}
          />
          <span style={{ fontWeight: 600, fontSize: "1.15rem", letterSpacing: "-0.02em" }}>OSFL</span>
          <span className="mono" style={{ fontSize: 10, color: "var(--ink-faint)", marginTop: 4 }}>os&nbsp;for&nbsp;life</span>
        </a>
        <nav
          className="mono"
          style={{ marginLeft: "auto", display: "flex", gap: 26, fontSize: "0.78rem", letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-soft)" }}
        >
          <a href="#model" className="nav-link">The&nbsp;Model</a>
          <a href="#folder" className="nav-link">The&nbsp;Folder</a>
          <a href="#sim" className="nav-link">The&nbsp;Sim</a>
          <a href="#faq" className="nav-link">FAQ</a>
        </nav>
        <a
          href="https://github.com/Akasxh/OSFL"
          target="_blank"
          rel="noreferrer"
          className="btn btn-primary"
          style={{ padding: "9px 18px", fontSize: "0.86rem" }}
        >
          View on GitHub
        </a>
      </div>
    </header>
  );
}
