const GRADE_COLOR = { HIGH: "var(--win-soft)", MEDIUM: "var(--accent-deep)", LOW: "var(--ink-faint)", DERIVED: "var(--primary)" };

export default function SkillCard({ skill }) {
  const gc = GRADE_COLOR[skill.grade] || "var(--ink-faint)";
  return (
    <div
      style={{
        padding: "20px 20px 18px",
        borderRadius: "var(--r-md)",
        background: "var(--paper-raised)",
        border: "1px solid var(--line)",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div className="scr-row" style={{ justifyContent: "space-between" }}>
        <span className="mono" style={{ fontSize: 10.5, color: "var(--accent-deep)" }}>{skill.source}</span>
        <span className="mono" style={{ fontSize: 9.5, color: gc, border: `1px solid ${gc}`, borderRadius: 999, padding: "2px 7px" }}>{skill.grade}</span>
      </div>
      <h3 className="display" style={{ fontSize: "1.55rem", marginTop: 8, lineHeight: 1 }}>{skill.title}</h3>
      <ul style={{ listStyle: "none", padding: 0, margin: "14px 0 0", display: "grid", gap: 8 }}>
        {skill.insights.map((t) => (
          <li key={t} className="scr-row" style={{ gap: 9, alignItems: "flex-start", fontSize: "0.9rem", color: "var(--ink-soft)", lineHeight: 1.4 }}>
            <span style={{ marginTop: 7, width: 5, height: 5, borderRadius: "50%", background: "var(--primary)", flex: "none" }} />
            {t}
          </li>
        ))}
      </ul>
      <div className="scr-row" style={{ justifyContent: "space-between", marginTop: "auto", paddingTop: 16 }}>
        <span className="mono" style={{ fontSize: 10, color: "var(--ink-faint)" }}>{skill.conf !== "—" ? `conf ${skill.conf} · ` : ""}{skill.stat}</span>
        <span className="mono" style={{ fontSize: 9.5, color: "var(--win-soft)" }}>↳ {skill.used}</span>
      </div>
    </div>
  );
}
