// The brand's signature mark: a jagged signal-with-noise line ("the fuzz"). Pure SVG so
// it scales; the line draws itself in via CSS (stroke-dashoffset), oscilloscope-style.
const POINTS =
  "0,30 20,26 40,34 60,20 80,31 100,10 120,33 140,27 160,38 180,29 200,14 220,31 " +
  "240,44 260,28 280,30 300,6 320,33 340,25 360,39 380,29 400,18 420,31 440,47 460,27 " +
  "480,30 500,12 520,33 540,26 560,40 580,29 600,22 620,33 640,30";

export function FuzzWave() {
  return (
    <svg
      className="fuzzwave"
      viewBox="0 0 640 60"
      preserveAspectRatio="none"
      role="img"
      aria-label="a fuzz signal waveform"
    >
      <polyline
        points={POINTS}
        fill="none"
        stroke="#b6f400"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
