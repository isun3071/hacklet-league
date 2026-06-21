// A section divider drawn in ASCII — a run of tildes that reads as a wave (echoing the
// fuzz signal). Overflow is clipped, so it fills any width without ever spilling.
export function AsciiRule() {
  return (
    <div className="ascii-rule" aria-hidden="true">
      {"~".repeat(240)}
    </div>
  );
}
