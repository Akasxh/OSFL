import SectionHeading from "./ui/SectionHeading.jsx";
import Reveal from "./ui/Reveal.jsx";
import SkillCard from "./SkillCard.jsx";
import { SKILLS } from "../data/skills.js";

const SOURCES = ["GitHub", "Slack", "résumé", "calendar"];

export default function SkillsFolder() {
  return (
    <section id="folder" className="sec" style={{ background: "linear-gradient(180deg, transparent, color-mix(in srgb, var(--primary) 4%, var(--paper)) 50%, transparent)" }}>
      <div className="wrap">
        <SectionHeading
          label="§04 / THE FOLDER OF YOU"
          title={<>A folder of you. It <em>learns who you are.</em></>}
          lead="A person isn't one skill — they're a stack of them. Connect what's already you (your GitHub, your chats, your résumé) and OSFL reads it into a labeled folder of skills. Every card feeds two engines: mimicry, so it speaks in your voice, and improvement, so it sharpens your odds."
          maxw="58ch"
        />

        <Reveal delay={0.1}>
          <div className="scr-row" style={{ gap: 10, marginTop: 26, flexWrap: "wrap" }}>
            <span className="mono" style={{ fontSize: 11, color: "var(--ink-faint)" }}>parsing</span>
            {SOURCES.map((s) => (
              <span key={s} className="chip">{s} <span style={{ color: "var(--win-soft)" }}>✓</span></span>
            ))}
          </div>
        </Reveal>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginTop: 30 }}>
          {SKILLS.map((skill, i) => (
            <Reveal key={skill.title} delay={0.05 * i}>
              <SkillCard skill={skill} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
