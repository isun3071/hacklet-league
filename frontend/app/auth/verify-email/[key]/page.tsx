"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/auth";

export default function VerifyEmailPage() {
  const params = useParams<{ key: string }>();
  const [state, setState] = useState<"verifying" | "ok" | "error">("verifying");

  useEffect(() => {
    const key = params?.key;
    if (!key) {
      setState("error");
      return;
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
