// 10-beat phone demo — feels like a real person tapping. ~33s loop.
// tap: cursor travels to {x,y}% of the phone and presses before the transition.
// spot: a key element pops ABOVE the frame over a dimmed screen for emphasis.
const REST = { x: 80, y: 90 };
const BTN = { x: 50, y: 87 };

export const BEATS = [
  { key: "boot", caption: "BOOTING YOUR LIFE KERNEL", seconds: 2.2, cursor: REST },
  { key: "connect", caption: "STEP 1 · CONNECT WHAT IS ALREADY YOU", seconds: 3.6, cursor: BTN, tap: true },
  { key: "folder", caption: "STEP 2 · OSFL READS YOU → A FOLDER OF YOU", seconds: 4.2, cursor: REST },
  { key: "goal", caption: "STEP 3 · NAME THE GOAL", seconds: 3.0, cursor: BTN, tap: true },
  { key: "funnel", caption: "DECOMPOSE THE OUTCOME", seconds: 3.0, cursor: REST },
  { key: "forecast", caption: "FORECAST", seconds: 4.4, cursor: REST, spot: "forecast" },
  { key: "bayes", caption: "LEARN YOUR REAL RATE · 8% → 12.7%", seconds: 4.4, cursor: REST, spot: "bayes" },
  { key: "wholelife", caption: "ONE QUEUE ACROSS ALL OF LIFE", seconds: 3.8, cursor: REST },
  { key: "draft", caption: "ACTS IN YOUR VOICE — ONE TAP", seconds: 3.4, cursor: BTN, tap: true },
  { key: "sent", caption: "SENT ✓", seconds: 2.6, cursor: REST, spot: "sent" },
];

export const SPOTLIGHTS = {
  forecast: { kind: "stat", big: "32%", sub: "P(≥1 offer) — a coin-flip you lose", color: "var(--win)" },
  bayes: { kind: "shift", from: "8.0%", to: "12.7%", sub: "your rate, not the average", color: "var(--win)" },
  sent: { kind: "sent" },
};
