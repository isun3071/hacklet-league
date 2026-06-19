"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getSession, login } from "@/lib/auth";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Already logged in? Don't show the form (and don't let a re-login 409).
  useEffect(() => {
    getSession().then((status) => {
      if (status === 200) router.replace("/");
    });
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const res = await login(email, password);
    setBusy(false);
    // 200 = logged in; 409 = already authenticated. Either way, you're in.
    if (res.ok || res.status === 409) {
      router.push("/");
      router.refresh();
      return;
    }
    if (res.status === 401) {
      setError("Verify your email before logging in — check the link we sent.");
    } else {
      setError(res.errors[0] ?? "Invalid email or password.");
    }
  }

  return (
    <main className="container block">
      <h1 className="page-title"># log in</h1>
      <form className="form" onSubmit={onSubmit}>
        <label className="field">
          <span>email</span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "..." : "[ log in ]"}
        </button>
      </form>
      <div className="oauth-divider"><span>or</span></div>
      <GoogleSignInButton callbackUrl="/dashboard" />
      <p className="note">
        no account? <Link href="/auth/signup">sign up &rarr;</Link>
      </p>
    </main>
  );
}
