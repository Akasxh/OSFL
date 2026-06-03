import { useEffect, useRef, useState } from "react";

/**
 * Drives the looping phone demo. Advances through `beats` on per-beat timers,
 * loops forever, and pauses when `paused` is true (hover / off-screen). The
 * current index persists across pauses so it resumes where it stopped.
 */
export function useDemoMachine(beats, paused) {
  const [index, setIndex] = useState(0);
  const idxRef = useRef(0);

  useEffect(() => {
    if (paused || beats.length === 0) return undefined;
    let timer;
    const schedule = () => {
      const cur = idxRef.current;
      const ms = (beats[cur]?.seconds ?? 2.6) * 1000;
      timer = setTimeout(() => {
        const next = (cur + 1) % beats.length;
        idxRef.current = next;
        setIndex(next);
        schedule();
      }, ms);
    };
    schedule();
    return () => clearTimeout(timer);
  }, [paused, beats]);

  return index;
}
