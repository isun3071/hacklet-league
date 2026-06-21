// One informative diagram of the round arc, drawn in the terminal palette:
// build (24:00, one AI) -> buzzer (network drops, commit = submission) -> attack -> score.
const ACCENT = "#b6f400";
const DANGER = "#ff7a7a";
const MUTED = "#828b7e";

export function FormatTimeline() {
  return (
    <svg
      className="fmt-timeline"
      viewBox="0 0 640 150"
      role="img"
      aria-label="Round timeline: build for 24 minutes with one AI; at the buzzer the network drops and your commit becomes your submission; then it is attacked by a fuzzer and players; then it is scored."
    >
      <text x="24" y="22" fill={ACCENT} fontSize="11" opacity="0.8">
        $ ./round --timeline
      </text>

      {/* captions above each zone */}
      <text x="210" y="48" fill={MUTED} fontSize="10" textAnchor="middle">
        one AI · no web search · no paste
      </text>
      <text x="478" y="48" fill={MUTED} fontSize="10" textAnchor="middle">
        fuzzer + attackers
      </text>
      <text x="588" y="48" fill={MUTED} fontSize="10" textAnchor="middle">
        judged
      </text>

      {/* the bar: build / attack / score */}
      <rect x="24" y="62" width="372" height="30" fill="rgba(182,244,0,0.12)" stroke={ACCENT} />
      <rect x="396" y="62" width="164" height="30" fill="rgba(255,122,122,0.12)" stroke={DANGER} />
      <rect x="560" y="62" width="56" height="30" fill="rgba(130,139,126,0.14)" stroke={MUTED} />

      <text x="210" y="81" fill={ACCENT} fontSize="12.5" textAnchor="middle" letterSpacing="0.5">
        BUILD · 24:00
      </text>
      <text x="478" y="81" fill={DANGER} fontSize="12.5" textAnchor="middle" letterSpacing="0.5">
        ATTACK
      </text>
      <text x="588" y="81" fill={MUTED} fontSize="12" textAnchor="middle" letterSpacing="0.5">
        SCORE
      </text>

      {/* buzzer — the boundary between build and attack */}
      <line x1="396" y1="52" x2="396" y2="102" stroke={ACCENT} strokeWidth="2" />
      <text x="396" y="116" fill={ACCENT} fontSize="10.5" textAnchor="middle">
        ▲ buzzer
      </text>
      <text x="396" y="130" fill={MUTED} fontSize="9.5" textAnchor="middle">
        network drops · commit = submission
      </text>

      <text x="24" y="108" fill={MUTED} fontSize="9.5">
        0:00
      </text>
    </svg>
  );
}
