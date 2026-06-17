import Link from "next/link";
import { AuthNav } from "@/components/AuthNav";

export function SiteHeader() {
  return (
    <header className="bar">
      <div className="container bar-inner">
        <Link className="logo" href="/">
          hacklet<span className="accent">_league</span>
        </Link>
        <AuthNav />
      </div>
    </header>
  );
}
