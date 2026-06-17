"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/auth";

export default function VerifyEmailPage() {
  const params = useParams<{ key: string }>();
  const [state, setState] = useState<"verifying" | "ok" | "error">("verifying");

  useEffect(() => {
    const raw = params?.key;
    if (!raw) {
      setState("error");
      return;
    }
    // allauth percent-encodes the key's colons in the email link (Mw%3A...%3A...),
    // and useParams() hands it back still-encoded. Decode before sending, or the
    // backend sees a key it never signed -> invalid_or_expired_key.
    let key = raw;
    try {
      key = decodeURIComponent(raw);
    } catch {
      /* not encoded; use as-is */
    }
    verifyEmail(key).then((res) => setState(res.ok ? "ok" : "error"));
  }, [params?.key]);

  return (
    <main className="container block">
      <h1 className="page-title"># verify email</h1>
      {state === "verifying" && <p className="body">Verifying…</p>}
      {state === "ok" && (
        <p className="body">
          Email verified. You can now <Link href="/auth/login">log in</Link>.
        </p>
      )}
      {state === "error" && (
        <p className="body">
          That verification link is invalid or expired. Try{" "}
          <Link href="/auth/signup">signing up</Link> again.
        </p>
      )}
    </main>
  );
}
