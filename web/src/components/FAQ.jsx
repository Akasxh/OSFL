import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import SectionHeading from "./ui/SectionHeading.jsx";

const QA = [
  ["Is this a to-do list with a probability sticker?", "No. It's a Monte-Carlo + Bayesian engine. Every goal is a Beta-Binomial funnel; the forecast comes from 10,000 simulated runs, and your real outcomes update it conjugately. The numbers are derived, not decorative."],
  ["Where do the probabilities come from before I have data?", "Layered priors: a cited domain benchmark, tilted by your profile, then sharpened by your own logged outcomes. Weak guesses are deliberately weak, so one or two real results dominate them."],
  ["Does it just imitate me, or actually push me?", "Both, on purpose. Your voice is mirrored (fidelity is the truth). Your strategy is guided — OSFL will tell you a plan is a 32% long-shot and force a smarter one, even if you'd rather just send more."],
  ["Is my data private?", "It runs fully offline by default — one inspectable JSON file, no account, no cloud. The LLM features are opt-in and only fire when you add your own key."],
  ["What does the 'folder of you' actually store?", "Skills parsed from what you connect — coding style and collaboration from GitHub, communication tone from chats, domain expertise from your résumé — each with a confidence score, used for mimicry and self-improvement."],
];

function Item({ q, a, open, onClick }) {
  return (
    <div style={{ borderBottom: "1px solid var(--line)" }}>
      <button onClick={onClick} style={{ width: "100%", textAlign: "left", padding: "22px 0", display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
        <span style={{ fontSize: "1.12rem", fontWeight: 500 }}>{q}</span>
        <span className="mono" style={{ fontSize: "1.4rem", color: "var(--primary)", transform: open ? "rotate(45deg)" : "none", transition: "transform .2s" }}>+</span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }} style={{ overflow: "hidden" }}>
            <p style={{ margin: "0 0 24px", maxWidth: "62ch", color: "var(--ink-soft)", lineHeight: 1.6 }}>{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function FAQ() {
  const [open, setOpen] = useState(0);
  return (
    <section id="faq" className="sec">
      <div className="wrap">
        <SectionHeading label="§06 / FAQ" title={<>The skeptical questions, <em>answered.</em></>} />
        <div style={{ marginTop: 36, borderTop: "1px solid var(--line)" }}>
          {QA.map(([q, a], i) => (
            <Item key={q} q={q} a={a} open={open === i} onClick={() => setOpen(open === i ? -1 : i)} />
          ))}
        </div>
      </div>
    </section>
  );
}
