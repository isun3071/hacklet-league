// A proportional timeline bar for a format's phases — shows the *shape* of the round
// (build dominates; defend is the adversarial phase) at a glance, complementing the exact
// labels in the code block beside it. Pure SVG, scales to its container.

type Tone = "muted" | "accent" | "danger";

export type Phase = { name: string; mins: number; time: string; tone: Tone };

const TONE: Record<Tone, { fill: string; stroke: string; text: string }> = {
  muted: { fill: "rgba(130,139,126,0.12)", stroke: "#828b7e", text: "#828b7e" },
  accent: { fill: "rgba(182,244,0,0.16)", stroke: "#b6f400", text: "#b6f400" },
  danger: { fill: "rgba(255,122,122,0.14)", stroke: "#ff7a7a", text: "#ff7a7a" },
};

const W = 640;

export function TimelineBar({ phases }: { phases: Phase[] }) {
  const total = phases.reduce((s, p) => s + p.mins, 0);
  let x = 0;
  const segs = phases.map((p) => {
    const w = (p.mins / total) * W;
    const seg = { ...p, x, w, cx: x + w / 2 };
    x += w;
    return seg;
  });

  return (
    <svg
      className="timeline-bar"
      viewBox="0 0 640 56"
      role="img"
      aria-label={phases.map((p) => `${p.name} ${p.time}`).join(", ")}
    >
      {segs.map((s) => {
        const t = TONE[s.tone];
        return (
          <g key={s.name}>
            <rect x={s.x + 0.5} y="8" width={Math.max(s.w - 1, 1)} height="26" fill={t.fill} stroke={t.stroke} />
            <text x={s.cx} y="25" fill={t.text} fontSize="10" textAnchor="middle">
              {s.time}
            </text>
            <text x={s.cx} y="48" fill="#828b7e" fontSize="9.5" textAnchor="middle">
              {s.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
