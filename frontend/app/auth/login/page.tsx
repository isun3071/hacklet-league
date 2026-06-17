"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const res = await login(email, password);
    setBusy(false);
    if (res.ok) {
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
      <p className="note">
        no account? <Link href="/auth/signup">sign up &rarr;</Link>
      </p>
    </main>
  );
}
