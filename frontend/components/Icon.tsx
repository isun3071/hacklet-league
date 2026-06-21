// Monochrome line icons — stroke = currentColor, sized to 1em, so they inherit the
// surrounding text color/size. Structural (roles, time), not decorative.

import type { SVGProps } from "react";

export type IconName = "player" | "judge" | "audience" | "event" | "clock";

const PATHS: Record<IconName, React.ReactNode> = {
  // competitor — a person
  player: (
    <>
      <circle cx="12" cy="8" r="3.2" />
      <path d="M5 20c0-3.6 3.1-6.2 7-6.2s7 2.6 7 6.2" />
    </>
  ),
  // judge — a balance scale
  judge: (
    <>
      <path d="M12 3v18" />
      <path d="M6 21h12" />
      <path d="M5 7h14" />
      <path d="M5 7l-2.5 5h5z" />
      <path d="M19 7l-2.5 5h5z" />
    </>
  ),
  // audience — an eye
  audience: (
    <>
      <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z" />
      <circle cx="12" cy="12" r="2.4" />
    </>
  ),
  // event — a calendar
  event: (
    <>
      <rect x="3.5" y="5" width="17" height="15" rx="1.5" />
      <path d="M3.5 9.5h17M8 3v4M16 3v4" />
    </>
  ),
  // time — a clock
  clock: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </>
  ),
};

export function Icon({
  name,
  className,
  ...rest
}: { name: IconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg
      className={`icon${className ? ` ${className}` : ""}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {PATHS[name]}
    </svg>
  );
}
