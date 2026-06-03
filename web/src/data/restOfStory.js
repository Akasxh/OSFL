// The parts the phone demo doesn't show: one cross-life queue + the 90-day arc.

export const QUEUE = [
  { rank: 1, domain: "CAREER", color: "#5b4fe9", task: "Warm intro → a target eng manager", score: 0.81,
    f: { impact: 0.9, urgency: 0.55, ltv: 0.9, dp: 1.0 } },
  { rank: 2, domain: "FUNDRAISE", color: "#f4a52b", task: "Reply to the lead investor — keep it warm", score: 0.74,
    f: { impact: 0.85, urgency: 0.7, ltv: 0.75, dp: 0.8 } },
  { rank: 3, domain: "BODY", color: "#3fd17a", task: "4 gym sessions this week — hold the streak", score: 0.63,
    f: { impact: 0.5, urgency: 0.45, ltv: 1.0, dp: 0.7 } },
  { rank: 4, domain: "FAMILY", color: "#c77dff", task: "Call home — 9 days since the last one", score: 0.58,
    f: { impact: 0.6, urgency: 0.8, ltv: 0.7, dp: 0.4 } },
];

export const FACTORS = [
  ["impact", "#e5484d"],
  ["urgency", "#f4a52b"],
  ["ltv", "#5b4fe9"],
  ["dp", "#3fd17a"],
];

// 5 beats of the autonomous scenario. coords are % of the SVG stage.
export const ARC = [
  { day: "DAY 1", kind: "REJECT", color: "#e5484d", x: 9, y: 64, title: "Auto-apply, 30 cold", note: "0 callbacks. The market says no — your portfolio is the gate, not your effort." },
  { day: "DAY 14", kind: "PIVOT", color: "#4338ca", x: 31, y: 38, title: "Stop spraying. Warm intros.", note: "The strategist kills the cold channel; a referral path lifts the gate 3×." },
  { day: "DAY 30", kind: "CRISIS", color: "#e5484d", x: 52, y: 70, title: "Burnout — throttle", note: "Rejection streak detected. OSFL caps your volume and protects recovery." },
  { day: "DAY 45", kind: "MOONSHOT", color: "#f4a52b", x: 74, y: 30, title: "Ship one loud thing", note: "A public artifact goes out. One reply from someone who matters." },
  { day: "DAY 60", kind: "WIN", color: "#3fd17a", x: 93, y: 50, title: "Offer in hand", note: "The win was a strategy, not luck — luck only changed the timing." },
];

// rejected branches (red-dashed) that fork off the taken path
export const DEAD_ENDS = [
  { fromX: 9, fromY: 64, toX: 22, toY: 86, label: "send more cold →" },
  { fromX: 52, fromY: 70, toX: 64, toY: 90, label: "push through →" },
];
