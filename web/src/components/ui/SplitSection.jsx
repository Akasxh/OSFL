import { useRef } from "react";

/**
 * Co-visibility layout: a STICKY narrative column (eyebrow + tight headline + lead + stepped
 * captions) beside the LIVE sim panel, both in one viewport (Apple sticky-copy × Linear 2-col).
 */
export default function SplitSection({ id, label, title, lead, steps = [], activeIndex = 0, footer, children }) {
  const ref = useRef(null);
  return (
    <section className="sec splitsec" id={id} ref={ref}>
      <div className="wrap split-grid">
        <aside className="split-narr">
          <div className="seclabel"><span className="tick" /><span className="eyebrow">{label}</span></div>
          <h2 className="display split-title">{title}</h2>
          {lead && <p className="lead split-lead">{lead}</p>}
          {steps.length > 0 && (
            <ol className="split-steps">
              {steps.map((s, i) => (
                <li key={s.k} className={"split-step" + (i === activeIndex ? " is-active" : "")}>
                  <span className="dot" />
                  <div><span className="st-k">{s.k}</span><span className="st-b">{s.b}</span></div>
                </li>
              ))}
            </ol>
          )}
          {footer}
        </aside>
        <div className="split-sim panel panel-vignette graticule">{children}</div>
      </div>
    </section>
  );
}
