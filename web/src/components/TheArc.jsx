import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import SplitSection from "./ui/SplitSection.jsx";
import { ARC, DEAD_ENDS } from "../data/restOfStory.js";

const W = 1000, H = 420;
const px = (x) => (x / 100) * W;
const py = (y) => (y / 100) * H;
const takenPath = ARC.map((n, i) => `${i === 0 ? "M" : "L"} ${px(n.x).toFixed(0)} ${py(n.y).toFixed(0)}`).join(" ");
const CLOUD = Array.from({ length: 46 }, (_, i) => ({ cx: (i * 137) % 100, cy: (i * 53 + 17) % 100, r: 2 + ((i * 31) % 3) }));
const STEPS = ARC.map((n) => ({ k: `${n.day} · ${n.kind}`, b: n.note }));

export default function TheArc() {
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-20% 0px" });
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (!inView) return undefined;
    const id = setInterval(() => setActive((a) => (a + 1) % ARC.length), 2100);
    return () => clearInterval(id);
  }, [inView]);

  const firstSeen = useRef(false);
  if (inView) firstSeen.current = true;
  const seen = firstSeen.current;

  return (
    <div ref={ref}>
      <SplitSection
        id="arc"
        label="§01 / THE 90-DAY SCENARIO · MONTE-CARLO FUTURES"
        title={<>It plays your next 90 days, <em>before you live them.</em></>}
        lead="OSFL runs an autonomous arc as a branching graph — takes the green path, abandons the red-dashed ones, survives a crisis, earns the win."
        steps={STEPS}
        activeIndex={active}
      >
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", flex: 1, minHeight: 0 }} role="img" aria-label="90-day scenario branching graph">
          {CLOUD.map((d, i) => <circle key={i} cx={px(d.cx)} cy={py(d.cy)} r={d.r} fill="var(--panel-line)" opacity="0.5" />)}
          {DEAD_ENDS.map((d, i) => (
            <g key={i}>
              <motion.line x1={px(d.fromX)} y1={py(d.fromY)} x2={px(d.toX)} y2={py(d.toY)} stroke="var(--loss)" strokeWidth="2" strokeDasharray="6 6"
                initial={{ pathLength: 0, opacity: 0 }} animate={seen ? { pathLength: 1, opacity: 0.6 } : {}} transition={{ duration: 0.8, delay: 0.6 + i * 0.4 }} />
              <text x={px(d.toX)} y={py(d.toY) + 20} fill="var(--loss)" opacity="0.7" style={{ fontFamily: "var(--font-mono)", fontSize: 15 }}>{d.label}</text>
            </g>
          ))}
          <motion.path d={takenPath} fill="none" stroke="var(--win)" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"
            initial={{ pathLength: 0 }} animate={seen ? { pathLength: 1 } : {}} transition={{ duration: 3.2, ease: [0.4, 0, 0.2, 1] }} style={{ filter: "drop-shadow(0 0 8px rgba(63,209,122,0.4))" }} />
          {ARC.map((n, i) => (
            <g key={n.day}>
              <motion.circle cx={px(n.x)} cy={py(n.y)} r={active === i ? 14 : 9} fill="var(--panel-deep)" stroke={n.color} strokeWidth="3"
                initial={{ scale: 0, opacity: 0 }} animate={seen ? { scale: 1, opacity: 1 } : {}} transition={{ duration: 0.4, delay: 0.4 + i * 0.62, ease: [0.22, 1, 0.36, 1] }}
                style={{ transformOrigin: `${px(n.x)}px ${py(n.y)}px`, filter: active === i ? `drop-shadow(0 0 12px ${n.color})` : "none" }} />
              <motion.text x={px(n.x)} y={py(n.y) - 24} textAnchor="middle" fill={n.color} initial={{ opacity: 0 }} animate={seen ? { opacity: 1 } : {}} transition={{ delay: 0.6 + i * 0.62 }}
                style={{ fontFamily: "var(--font-mono)", fontSize: 15, letterSpacing: "0.04em" }}>{n.day} · {n.kind}</motion.text>
            </g>
          ))}
        </svg>
      </SplitSection>
    </div>
  );
}
