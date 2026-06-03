import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  AnimatePresence, motion, useInView, useMotionValue, useSpring, useMotionTemplate,
} from "framer-motion";

import { BEATS, SPOTLIGHTS } from "../data/demoScript.js";
import { useDemoMachine } from "../lib/useDemoMachine.js";
import { SCREENS } from "./phone/screens.jsx";

const GLOW = "0 0 44px rgba(63,209,122,0.55)";

function CursorArrow() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20">
      <path d="M5 3l13.5 7.6-5.7 1.6L9.4 19 5 3z" fill="#fff" stroke="#14161d" strokeWidth="1.2" strokeLinejoin="round" />
    </svg>
  );
}

function Spotlight({ data }) {
  return (
    <motion.div className="spot-portal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.22 }}>
      <div className="spot-scrim" />
      <motion.div className="spot-stage"
        initial={{ opacity: 0, scale: 0.5, x: "16vw" }} animate={{ opacity: 1, scale: 1, x: 0 }} exit={{ opacity: 0, scale: 0.6, x: "12vw" }}
        transition={{ type: "spring", stiffness: 260, damping: 22 }}>
        {data.kind === "stat" && (
          <>
            <div className="display" style={{ fontSize: "clamp(72px,12vw,150px)", color: data.color, lineHeight: 1, textShadow: GLOW }}>{data.big}</div>
            <div className="mono" style={{ fontSize: 14, color: "#ede9f5", marginTop: 10 }}>{data.sub}</div>
          </>
        )}
        {data.kind === "shift" && (
          <>
            <div style={{ display: "flex", alignItems: "baseline", gap: "min(4vw,40px)", justifyContent: "center" }}>
              <span className="num" style={{ fontSize: "clamp(40px,6vw,72px)", color: "#8b81a6" }}>{data.from}</span>
              <span style={{ color: "var(--accent)", fontSize: "clamp(28px,4vw,44px)" }}>→</span>
              <span className="num" style={{ fontSize: "clamp(56px,9vw,110px)", color: data.color, textShadow: GLOW }}>{data.to}</span>
            </div>
            <div className="mono" style={{ fontSize: 14, color: "#ede9f5", marginTop: 12 }}>{data.sub}</div>
          </>
        )}
      </motion.div>
    </motion.div>
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

  const [pressed, setPressed] = useState(false);
  const [clickRing, setClickRing] = useState(false);
  const [spot, setSpot] = useState(null);

  // spring-driven cursor: fast arrow + lagging ring → smooth, magnetic, never jumps
  const cx = useMotionValue(beat.cursor.x);
  const cy = useMotionValue(beat.cursor.y);
  const sx = useSpring(cx, { stiffness: 220, damping: 26, mass: 0.9 });
  const sy = useSpring(cy, { stiffness: 220, damping: 26, mass: 0.9 });
  const rx = useSpring(cx, { stiffness: 150, damping: 24, mass: 1 });
  const ry = useSpring(cy, { stiffness: 150, damping: 24, mass: 1 });
  const aLeft = useMotionTemplate`${sx}%`;
  const aTop = useMotionTemplate`${sy}%`;
  const rLeft = useMotionTemplate`${rx}%`;
  const rTop = useMotionTemplate`${ry}%`;

  useEffect(() => {
    cx.set(beat.cursor.x);
    cy.set(beat.cursor.y);
    setPressed(false);
    setClickRing(false);
    setSpot(null);
    if (paused) return undefined;
    const t = [];
    if (beat.tap) {
      t.push(setTimeout(() => setPressed(true), 560)); // press after the spring settles
      t.push(setTimeout(() => setClickRing(true), 680));
      t.push(setTimeout(() => { setClickRing(false); }, 1180));
      t.push(setTimeout(() => setPressed(false), 920));
    }
    if (beat.spot) {
      const at = beat.seconds * 1000 * 0.4;
      t.push(setTimeout(() => setSpot(beat.spot), at));
      t.push(setTimeout(() => setSpot(null), at + 1400));
    }
    return () => t.forEach(clearTimeout);
  }, [index, paused, beat, cx, cy]);

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

        {/* cursor layer — lagging ring + fast arrow + click ring */}
        <div className="phone-overlay">
          <motion.div className="cursor-ring" style={{ left: rLeft, top: rTop, opacity: clickRing ? 0 : 0.85 }} />
          <motion.div className="demo-cursor" style={{ left: aLeft, top: aTop }}
            animate={{ scale: pressed ? 0.78 : 1, y: pressed ? 2 : 0 }}
            transition={{ duration: pressed ? 0.1 : 0.24, ease: pressed ? [0.4, 0, 1, 1] : [0.16, 1, 0.3, 1] }}>
            <motion.div animate={{ x: [0, 1.5, -1, 0], y: [0, -1, 1.5, 0] }} transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}>
              <CursorArrow />
            </motion.div>
          </motion.div>
          <AnimatePresence>
            {clickRing && (
              <motion.span className="click-ring" style={{ left: aLeft, top: aTop }}
                initial={{ opacity: 0.7, scale: 0.35 }} animate={{ opacity: 0, scale: 2.3 }} exit={{ opacity: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} />
            )}
          </AnimatePresence>
        </div>
      </div>
      <div className="phone-reflection" />

      {/* spotlight — centered on the viewport via a body portal */}
      {createPortal(
        <AnimatePresence>{spot && <Spotlight key={spot} data={SPOTLIGHTS[spot]} />}</AnimatePresence>,
        document.body
      )}
    </div>
  );
}
