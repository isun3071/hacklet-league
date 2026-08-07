// The HackLet mark: a forward-skewed H trailing a phosphor scanline band. Drawn with
// currentColor (both the solid H and the fade gradient), so it takes the color of whatever
// element it sits in — set `color` on the parent to tint it. No background; use on a dark
// surface. The favicon/branding variants (with a dark rounded-square bg and baked lime) live in
// public/logo-mark-square.svg and app/icon.svg.
export function HackletMark({ className }: { className?: string }) {
  const y0 = 16;
  return (
    <svg className={className} viewBox="0 0 160 120" role="img" aria-label="HackLet League">
      <defs>
        <linearGradient id="hlmark-fade" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="currentColor" stopOpacity="0" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0.9" />
        </linearGradient>
      </defs>
      <g transform="translate(10,0) skewX(-9)">
        <g fill="url(#hlmark-fade)">
          {Array.from({ length: 13 }, (_, i) => (
            <rect key={i} x="28" y={y0 + i * 7} width="62" height="4" />
          ))}
        </g>
        <g fill="currentColor">
          <rect x="90" y="16" width="16" height="88" />
          <rect x="134" y="16" width="16" height="88" />
          <rect x="106" y="52" width="28" height="16" />
        </g>
      </g>
    </svg>
  );
}
