"use client";

import { useState } from "react";
import Link from "next/link";
import { signup } from "@/lib/auth";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const res = await signup(email, password);
    setBusy(false);
    // 400 = validation error (email taken, weak password). 200/401 = created
    // (401 means email verification is pending, which is the expected path).
    if (res.status === 400) {
      setError(res.errors[0] ?? "Could not create account.");
      return;
    }
    setDone(true);
  }

  if (done) {
    return (
      <main className="container block">
        <h1 className="page-title"># check your email</h1>
        <p className="body">
          Account created. We sent a verification link to <span className="hl">{email}</span>.
          Click it, then <Link href="/auth/login">log in</Link>.
        </p>
        <p className="note">
          // dev: the email prints in the backend logs (<code>docker compose logs backend</code>).
        </p>
      </main>
    );
  }

  return (
    <main className="container block">
      <h1 className="page-title"># sign up</h1>
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
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "..." : "[ create account ]"}
        </button>
      </form>
      <div className="oauth-divider"><span>or</span></div>
      <GoogleSignInButton callbackUrl="/dashboard" />
      <p className="note">
        have an account? <Link href="/auth/login">log in &rarr;</Link>
      </p>
    </main>
  );
}
