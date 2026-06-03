import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useInView } from "framer-motion";

import { BEATS, SPOTLIGHTS } from "../data/demoScript.js";
import { useDemoMachine } from "../lib/useDemoMachine.js";
import { SCREENS } from "./phone/screens.jsx";

function CursorArrow() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22">
      <path d="M5 3l13.5 7.6-5.7 1.6L9.4 19 5 3z" fill="#fff" stroke="#14161d" strokeWidth="1.2" strokeLinejoin="round" />
    </svg>
  );
}

function Spotlight({ data }) {
  const glow = "0 0 34px rgba(63,209,122,0.55)";
  return (
    <>
      <motion.div className="spot-dim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }} />
      <motion.div className="spot-pop"
        initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.25 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}>
        {data.kind === "stat" && (
          <>
            <div className="display" style={{ fontSize: 92, color: data.color, lineHeight: 1, textShadow: glow }}>{data.big}</div>
            <div className="mono" style={{ fontSize: 11, color: "var(--panel-ink)", marginTop: 6, whiteSpace: "nowrap" }}>{data.sub}</div>
          </>
        )}
        {data.kind === "shift" && (
          <>
            <div style={{ display: "flex", alignItems: "baseline", gap: 12, justifyContent: "center" }}>
              <span className="num" style={{ fontSize: 40, color: "var(--panel-muted)" }}>{data.from}</span>
              <span style={{ color: "var(--accent)", fontSize: 26 }}>→</span>
              <span className="num" style={{ fontSize: 60, color: data.color, textShadow: glow }}>{data.to}</span>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--panel-ink)", marginTop: 8, whiteSpace: "nowrap" }}>{data.sub}</div>
          </>
        )}
        {data.kind === "sent" && (
          <>
            <motion.div initial={{ x: -16, y: 24, opacity: 0, rotate: -10 }} animate={{ x: 70, y: -70, opacity: [0, 1, 1, 0], rotate: 12 }} transition={{ duration: 1.15, ease: "easeOut" }} style={{ position: "absolute", left: 0, top: 0, fontSize: 30 }}>✈</motion.div>
            <div className="display" style={{ fontSize: 56, color: "var(--win)", textShadow: glow }}>Sent ✓</div>
          </>
        )}
      </motion.div>
    </>
  );
}

export default function PhoneDemo() {
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-10% 0px", amount: 0.3 });
  const [hover, setHover] = useState(false);
  const paused = hover || !inView;
  const index = useDemoMachine(BEATS, paused);
  const beat = BEATS[index];
  const Screen = SCREENS[beat.key];
  const [ripple, setRipple] = useState(false);
  const [spot, setSpot] = useState(null);

  useEffect(() => {
    setRipple(false);
    setSpot(null);
    if (paused) return undefined;
    const timers = [];
    if (beat.tap) {
      timers.push(setTimeout(() => setRipple(true), 620));
      timers.push(setTimeout(() => setRipple(false), 1150));
    }
    if (beat.spot) {
      const at = beat.seconds * 1000 * 0.4;
      timers.push(setTimeout(() => setSpot(beat.spot), at));
      timers.push(setTimeout(() => setSpot(null), at + 1300));
    }
    return () => timers.forEach(clearTimeout);
  }, [index, paused, beat]);

  return (
    <div className="phone-stage" ref={ref}>
      <div className="phone" onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>
        <div className="phone-screen graticule panel-vignette">
          <div className="phone-island" />
          <div className="phone-statusbar"><span>9:41</span><span>OSFL</span></div>
          <div className="phone-progress" aria-hidden>
            {BEATS.map((b, i) => <i key={b.key} className={i === index ? "on" : ""} />)}
          </div>
          <div className="phone-caption" style={{ opacity: spot ? 0.2 : 1 }}>
            <span className="rec" /><span>{beat.caption}</span>
          </div>
          <div className="phone-canvas">
            <AnimatePresence mode="wait">
              <motion.div key={beat.key} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }} style={{ position: "absolute", inset: 0 }}>
                <Screen />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* overlay — cursor + ripple + spotlight; NOT clipped, so spotlights pop past the frame */}
        <div className="phone-overlay">
          <motion.div
            className="demo-cursor"
            initial={false}
            animate={{ left: `${beat.cursor.x}%`, top: `${beat.cursor.y}%`, scale: ripple ? 0.82 : 1 }}
            transition={{ left: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }, top: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }, scale: { duration: 0.12 } }}
          >
            <CursorArrow />
          </motion.div>
          <AnimatePresence>
            {ripple && (
              <motion.span className="tap-ripple" style={{ left: `${beat.cursor.x}%`, top: `${beat.cursor.y}%` }}
                initial={{ opacity: 0.5, scale: 0.4 }} animate={{ opacity: 0, scale: 2.6 }} exit={{ opacity: 0 }} transition={{ duration: 0.55 }} />
            )}
          </AnimatePresence>
          <AnimatePresence>
            {spot && <Spotlight key={spot} data={SPOTLIGHTS[spot]} />}
          </AnimatePresence>
        </div>
      </div>
      <div className="phone-reflection" />
    </div>
  );
}
