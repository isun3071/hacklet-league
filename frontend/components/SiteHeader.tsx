import Link from "next/link";
import { AuthNav } from "@/components/AuthNav";
import { HackletMark } from "@/components/HackletMark";

export function SiteHeader() {
  return (
    <header className="bar">
      <div className="container bar-inner">
        <Link className="logo" href="/">
          <HackletMark className="logo-mark" />
          hacklet<span className="accent">_league</span>
        </Link>
        <AuthNav />
      </div>
    </header>
  );
}
