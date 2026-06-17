"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getSession, logout } from "@/lib/auth";

export function AuthNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [authed, setAuthed] = useState<boolean | null>(null);

  // Re-check on every route change: the header lives in the root layout and never
  // remounts, so a mount-only effect would go stale after login/logout navigation.
  useEffect(() => {
    getSession().then((status) => setAuthed(status === 200));
  }, [pathname]);

  async function onLogout() {
    await logout();
    setAuthed(false);
    router.push("/");
    router.refresh();
  }

  return (
    <nav className="nav-links">
      <Link href="/chapters">chapters</Link>
      {authed === true && (
        <>
          <Link href="/chapters/new">new chapter</Link>
          <Link href="/profile">profile</Link>
          <button type="button" className="navbtn" onClick={onLogout}>
            log out
          </button>
        </>
      )}
      {authed === false && (
        <>
          <Link href="/auth/login">log in</Link>
          <Link className="bar-link" href="/auth/signup">[ sign up ]</Link>
        </>
      )}
    </nav>
  );
}
