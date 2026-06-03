import SectionHeading from "./ui/SectionHeading.jsx";
import Reveal from "./ui/Reveal.jsx";

const WHO = [
  ["Job hunters", "Apply → screen → onsite → offer. A real funnel with brutal gates."],
  ["Founders", "Outreach → meeting → term sheet. Volume is your only lever."],
  ["Sales & BD", "Cold reply rates are tiny. Shots compound; feelings don't."],
  ["Applicants", "Grad school, grants, residencies — the long-odds games."],
];

export default function WhoItsFor() {
  return (
    <section className="sec" style={{ paddingTop: 0 }}>
      <div className="wrap">
        <SectionHeading
          label="§05 / BUILT FOR HIGH-VARIANCE OPERATORS"
          title={<>If your wins come from <em>many shots,</em> OSFL is your edge.</>}
          maxw="40ch"
        />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px,1fr))", gap: 16, marginTop: 36 }}>
          {WHO.map(([t, d], i) => (
            <Reveal key={t} delay={i * 0.06}>
              <div style={{ padding: "22px 20px", borderTop: "2px solid var(--primary)", background: "var(--paper-raised)", borderRadius: "0 0 var(--r-md) var(--r-md)", height: "100%" }}>
                <div className="display" style={{ fontSize: "1.6rem" }}>{t}</div>
                <p style={{ marginTop: 10, fontSize: "0.94rem", color: "var(--ink-soft)", lineHeight: 1.5 }}>{d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
