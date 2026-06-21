"use client";

import { useState } from "react";
import { request } from "@/lib/http";

export function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "busy" | "done">("idle");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setState("busy");
    setError("");
    const res = await request<{ detail: string }>(
      "/api/newsletter/subscribe/",
      "POST",
      { email },
    );
    if (res.ok && res.data) {
      setMessage(res.data.detail);
      setState("done");
      return;
    }
    setError(res.errors[0] ?? "Could not sign you up. Please try again.");
    setState("idle");
  }

  if (state === "done") {
    return <p className="ok-msg">{message}</p>;
  }

  return (
    <form className="signup-form" onSubmit={onSubmit}>
      <label className="sr-only" htmlFor="bd-email">email address</label>
      <span className="form-prompt">subscribe:~$</span>
      <input
        id="bd-email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
        placeholder="you@example.com"
        required
      />
      <button type="submit" className="btn" disabled={state === "busy"}>
        {state === "busy" ? "..." : "[ notify me ]"}
      </button>
      {error && <p className="form-error">{error}</p>}
    </form>
  );
}
