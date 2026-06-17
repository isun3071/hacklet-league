"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { request } from "@/lib/http";

type Profile = {
  email: string;
  display_name: string;
  verified_email: boolean;
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [status, setStatus] = useState<"loading" | "ready" | "unauth">("loading");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    request<Profile>("/api/me/", "GET").then((res) => {
      if (res.status === 200 && res.data) {
        setProfile(res.data);
        setDisplayName(res.data.display_name ?? "");
        setStatus("ready");
      } else {
        setStatus("unauth");
      }
    });
  }, []);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setSaved(false);
    const res = await request("/api/me/", "PATCH", { display_name: displayName });
    setBusy(false);
    if (res.ok) setSaved(true);
  }

  if (status === "loading") {
    return (
      <main className="container block">
        <p className="body">Loading…</p>
      </main>
    );
  }

  if (status === "unauth" || !profile) {
    return (
      <main className="container block">
        <h1 className="page-title"># profile</h1>
        <p className="body">
          You need to <Link href="/auth/login">log in</Link> to view your profile.
        </p>
      </main>
    );
  }

  return (
    <main className="container block">
      <h1 className="page-title"># profile</h1>
      <div className="panel">
        <dl className="kv">
          <div>
            <dt>email</dt>
            <dd>{profile.email}</dd>
          </div>
          <div>
            <dt>verified</dt>
            <dd>{profile.verified_email ? "yes" : "no"}</dd>
          </div>
        </dl>
        <form className="form" onSubmit={onSave}>
          <label className="field">
            <span>display name</span>
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </label>
          <button className="btn" type="submit" disabled={busy}>
            {busy ? "..." : "[ save ]"}
          </button>
          {saved && <p className="ok-msg">saved.</p>}
        </form>
      </div>
    </main>
  );
}
