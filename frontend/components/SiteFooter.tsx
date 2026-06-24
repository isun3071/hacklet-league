import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="foot">
      <div className="container bar-inner">
        <span className="logo">
          hacklet<span className="accent">_league</span>
        </span>
        <Link className="textlink" href="/scoring">
          how scoring works
        </Link>
        <span className="muted">in development &middot; 2026</span>
      </div>
    </footer>
  );
}
