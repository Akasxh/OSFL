import SectionHeading from "./ui/SectionHeading.jsx";
import Reveal from "./ui/Reveal.jsx";

const PROOF = [
  { n: "0.382", k: "the textbook odds", d: "60 applications through an 8% → 40% → 25% funnel. Closed-form says you clear it 38% of the time." },
  { n: "0.32", k: "your actual odds", d: "Sample the uncertainty in each rate per run and the number drops. The average lies; the distribution doesn't.", hot: true },
  { n: "n=201", k: "what 80% costs", d: "To make it likely, you don't try harder — you take 201 shots, not 60. Funnels punish you nonlinearly." },
];

export default function CoreMechanic() {
  return (
    <section id="model" className="sec">
      <div className="wrap">
        <SectionHeading
          label="§01 / THE MODEL"
          title={<>Funnels punish you. <em>Nonlinearly.</em></>}
          lead="You can't will your reply rate to 50%. But you decide how many shots you take — and that's the only variable you actually control. OSFL makes the trade explicit."
          maxw="44ch"
        />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 18, marginTop: 48 }}>
          {PROOF.map((p, i) => (
            <Reveal key={p.k} delay={i * 0.08}>
              <div style={{ padding: "26px 24px", borderRadius: "var(--r-md)", background: "var(--paper-raised)", border: `1px solid ${p.hot ? "var(--primary)" : "var(--line)"}`, height: "100%" }}>
                <div className="num" style={{ fontSize: "2.6rem", color: p.hot ? "var(--primary)" : "var(--ink)" }}>{p.n}</div>
                <div className="eyebrow" style={{ marginTop: 4, color: p.hot ? "var(--accent-deep)" : "var(--ink-faint)" }}>{p.k}</div>
                <p style={{ marginTop: 14, fontSize: "0.98rem", color: "var(--ink-soft)", lineHeight: 1.5 }}>{p.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
