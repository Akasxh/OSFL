import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import SectionHeading from "./ui/SectionHeading.jsx";

const VOICES = {
  professional: {
    to: "Hiring Manager · Google TPU",
    body: ["Hi — circling back on the inference-optimization roadmap.", "I lead TPU kernel work upstream (vLLM, LLVM/MLIR).", "Could we find 15 minutes this week?"],
    tone: "formality 0.85 · warmth 0.40 · no emoji",
  },
  friends: {
    to: "Dev · #kernels",
    body: ["yo the MLIR offload PR finally landed", "TPU path is ~1.8x faster now", "lunch fri to celebrate?"],
    emoji: "🔥",
    tone: "formality 0.25 · warmth 0.80 · emoji ~1-in-2",
  },
  family: {
    to: "Ma",
    body: ["Hi Ma! Quick update — the Google conversation is moving.", "Nothing to worry about, it's going well.", "Call you tonight."],
    emoji: "❤️",
    tone: "formality 0.45 · warmth 0.95 · reassurance first",
  },
};

export default function DigitalTwin() {
  const [v, setV] = useState("professional");
  const d = VOICES[v];
  return (
    <section className="sec">
      <div className="wrap">
        <SectionHeading
          label="§06 / THE TWIN"
          title={<>A folder of you. It <em>drafts in your voice.</em></>}
          lead="Three clusters, three registers — learned from your real messages. The strategist decides what to send; the twin only decides how it reads. Mimicry where fidelity is the truth; the math never touches your wording."
          maxw="56ch"
        />
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,0.9fr) minmax(0,1.1fr)", gap: "clamp(20px,4vw,56px)", marginTop: 40, alignItems: "center" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {Object.keys(VOICES).map((k) => (
              <button
                key={k}
                onClick={() => setV(k)}
                style={{
                  textAlign: "left", padding: "16px 18px", borderRadius: "var(--r-md)",
                  border: `1.5px solid ${v === k ? "var(--primary)" : "var(--line)"}`,
                  background: v === k ? "color-mix(in srgb, var(--primary) 7%, var(--paper-raised))" : "var(--paper-raised)",
                  transition: "border-color .2s, background .2s",
                }}
              >
                <div style={{ fontWeight: 600, textTransform: "capitalize", fontSize: "1.05rem" }}>{k}</div>
                <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-faint)", marginTop: 2 }}>{VOICES[k].tone}</div>
              </button>
            ))}
          </div>

          <div className="panel panel-vignette" style={{ padding: 22, minHeight: 280 }}>
            <div className="scr-row" style={{ justifyContent: "space-between", borderBottom: "1px solid var(--panel-line)", paddingBottom: 12 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--panel-muted)" }}>to: {d.to}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--win)", textTransform: "capitalize" }}>{v}</span>
            </div>
            <AnimatePresence mode="wait">
              <motion.div key={v} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.3 }} style={{ paddingTop: 16 }}>
                {d.body.map((line, i) => (
                  <p key={i} style={{ margin: "0 0 10px", fontSize: "1rem", lineHeight: 1.5, color: "var(--panel-ink)" }}>
                    {line}{d.emoji && i === d.body.length - 1 ? <span style={{ fontSize: "0.8em", opacity: 0.7, marginLeft: 4 }}>{d.emoji}</span> : null}
                  </p>
                ))}
                <div style={{ marginTop: 18, display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ padding: "9px 16px", borderRadius: 999, background: "var(--win)", color: "#08110a", fontWeight: 600, fontSize: "0.9rem" }}>Send ↗</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--accent)" }}>✦ drafted in your voice · MIRROR</span>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
