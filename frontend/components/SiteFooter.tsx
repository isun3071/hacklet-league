import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="foot">
      <div className="container bar-inner">
        <span className="logo">
          hacklet<span className="accent">_league</span>
        </span>
        <span className="nav-links">
          <Link href="/about">about</Link>
          <Link href="/scoring">how scoring works</Link>
        </span>
        <span className="muted">in development &middot; 2026</span>
      </div>
    </footer>
  );
}
