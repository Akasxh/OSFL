import { useRef, useState } from "react";
import { AnimatePresence, motion, useInView } from "framer-motion";

import { BEATS } from "../data/demoScript.js";
import { useDemoMachine } from "../lib/useDemoMachine.js";
import { SCREENS } from "./phone/screens.jsx";

export default function PhoneDemo() {
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-10% 0px", amount: 0.3 });
  const [hover, setHover] = useState(false);
  const index = useDemoMachine(BEATS, hover || !inView);
  const beat = BEATS[index];
  const Screen = SCREENS[beat.key];

  return (
    <div className="phone-stage" ref={ref}>
      <div
        className="phone"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        <div className="phone-screen graticule panel-vignette">
          <div className="phone-island" />
          <div className="phone-statusbar"><span>9:41</span><span>OSFL</span></div>

          <div className="phone-progress" aria-hidden>
            {BEATS.map((b, i) => (
              <i key={b.key} className={i === index ? "on" : ""} />
            ))}
          </div>

          <div className="phone-canvas">
            <AnimatePresence mode="wait">
              <motion.div
                key={beat.key}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35 }}
                style={{ position: "absolute", inset: 0 }}
              >
                <Screen />
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="phone-caption">
            <span className="rec" />
            <span>{beat.caption}</span>
          </div>
        </div>
      </div>
      <div className="phone-reflection" />
    </div>
  );
}
