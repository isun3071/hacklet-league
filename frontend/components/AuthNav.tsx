"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getSession, logout } from "@/lib/auth";
import { request } from "@/lib/http";

type Me = { display_name: string; email: string };

// Personal / login-gated destinations, collapsed under the [username] menu. chapter+event
// mgmt live on the dashboard, so they deep-link to its sections (see dashboard anchors).
const MENU: { href: string; label: string }[] = [
  { href: "/dashboard", label: "dashboard" },
  { href: "/dashboard#my-chapters", label: "chapter mgmt" },
  { href: "/dashboard#events-i-run", label: "event mgmt" },
  { href: "/chapters/new", label: "new chapter" },
  { href: "/profile", label: "profile" },
];

export function AuthNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Re-check session + identity on every route change: the header lives in the root layout
  // and never remounts, so a mount-only effect would go stale after login/logout.
  useEffect(() => {
    (async () => {
      const ok = (await getSession()) === 200;
      setAuthed(ok);
      if (ok) {
        const res = await request<Me>("/api/me/", "GET");
        setMe(res.data ?? null);
      } else {
        setMe(null);
      }
    })();
    setOpen(false);
  }, [pathname]);

  // Close on outside click or Escape.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function onLogout() {
    await logout();
    setAuthed(false);
    setMe(null);
    setOpen(false);
    router.push("/");
    router.refresh();
  }

  const username = me?.display_name?.trim() || me?.email?.split("@")[0] || "account";

  return (
    <nav className="nav-links">
      <Link href="/chapters">chapters</Link>
      <Link href="/events">events</Link>
      <Link href="/leaderboard">leaderboard</Link>

      {authed === true && (
        <div
          className="menu"
          ref={ref}
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={() => setOpen(false)}
        >
          <button
            type="button"
            className="menu-trigger"
            aria-haspopup="menu"
            aria-expanded={open}
            onClick={() => setOpen((o) => !o)}
          >
            [{username}]
          </button>
          <div className={`menu-panel${open ? " open" : ""}`} role="menu">
            {MENU.map((m) => (
              <Link key={m.href} href={m.href} role="menuitem" onClick={() => setOpen(false)}>
                {m.label}
              </Link>
            ))}
            <button type="button" className="menu-item-btn" role="menuitem" onClick={onLogout}>
              log out
            </button>
          </div>
        </div>
      )}

      {authed === false && (
        <>
          <Link href="/auth/login">log in</Link>
          <Link className="bar-link" href="/auth/signup">
            [ sign up ]
          </Link>
        </>
      )}
    </nav>
  );
}
