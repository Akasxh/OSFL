import Reveal from "./Reveal.jsx";

export default function SectionHeading({ label, title, lead, align = "left", maxw }) {
  return (
    <div style={{ textAlign: align, marginInline: align === "center" ? "auto" : 0, maxWidth: maxw }}>
      {label && (
        <Reveal>
          <div className="seclabel" style={{ justifyContent: align === "center" ? "center" : "flex-start" }}>
            <span className="tick" />
            <span className="eyebrow">{label}</span>
          </div>
        </Reveal>
      )}
      <Reveal delay={0.06}>
        <h2 className="display h2" style={{ marginTop: 16 }}>{title}</h2>
      </Reveal>
      {lead && (
        <Reveal delay={0.12}>
          <p className="lead" style={{ marginTop: 18, marginInline: align === "center" ? "auto" : 0 }}>{lead}</p>
        </Reveal>
      )}
    </div>
  );
}
