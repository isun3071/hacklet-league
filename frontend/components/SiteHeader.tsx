import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="bar">
      <div className="container bar-inner">
        <Link className="logo" href="/">
          hacklet<span className="accent">_league</span>
        </Link>
        <nav className="nav-links">
          <Link href="/chapters">chapters</Link>
          <Link className="bar-link" href="/#signup">[ get updates ]</Link>
        </nav>
      </div>
    </header>
  );
}
