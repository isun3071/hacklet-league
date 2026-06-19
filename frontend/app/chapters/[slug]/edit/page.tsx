"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { request } from "@/lib/http";
import type { Chapter } from "@/lib/api";

type Form = {
  name: string;
  description: string;
  location_text: string;
  institutional_affiliation: string;
  tier: string;
  contact_email: string;
  website_url: string;
};

export default function EditChapterPage() {
  const router = useRouter();
  const params = useParams<{ slug: string }>();
  const slug = params?.slug;

  const [form, setForm] = useState<Form | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "unauth" | "notfound">("loading");
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  // Load from /mine so the page only ever edits chapters the user owns (and so we get
  // the owner-only contact_email to prefill).
  useEffect(() => {
    if (!slug) return;
    request<Chapter[]>("/api/chapters/mine/", "GET").then((res) => {
      if (res.status !== 200 || !Array.isArray(res.data)) {
        setState("unauth");
        return;
      }
      const c = res.data.find((x) => x.slug === slug);
      if (!c) {
        setState("notfound");
        return;
      }
      setForm({
        name: c.name ?? "",
        description: c.description ?? "",
        location_text: c.location_text ?? "",
        institutional_affiliation: c.institutional_affiliation ?? "",
        tier: c.tier ?? "C",
        contact_email: c.contact_email ?? "",
        website_url: c.website_url ?? "",
      });
      setState("ready");
    });
  }, [slug]);

  function set(key: keyof Form, value: string) {
    setForm((f) => (f ? { ...f, [key]: value } : f));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    setBusy(true);
    setErrors([]);
    const res = await request(`/api/chapters/${slug}/`, "PATCH", form);
    setBusy(false);
    if (res.ok) {
      router.push("/dashboard");
      router.refresh();
      return;
    }
    setErrors(res.errors.length ? res.errors : ["Could not save changes."]);
  }

  if (state === "loading") {
    return (
      <main className="container block">
        <p className="body">Loading…</p>
      </main>
    );
  }

  if (state === "unauth") {
    return (
      <main className="container block">
        <h1 className="page-title"># edit chapter</h1>
        <p className="body">
          You need to <Link href="/auth/login">log in</Link> to edit a chapter.
        </p>
      </main>
    );
  }

  if (state === "notfound" || !form) {
    return (
      <main className="container block">
        <h1 className="page-title"># edit chapter</h1>
        <p className="body">That chapter doesn&apos;t exist or isn&apos;t yours to edit.</p>
        <p className="note">
          <Link href="/dashboard">&larr; dashboard</Link>
        </p>
      </main>
    );
  }

  return (
    <main className="container block">
      <h1 className="page-title"># edit chapter</h1>
      <p className="subtitle">
        // editing <span className="hl">{form.name}</span>
      </p>
      <form className="form" onSubmit={onSubmit}>
        <label className="field">
          <span>name *</span>
          <input value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </label>
        <label className="field">
          <span>description</span>
          <textarea rows={3} value={form.description} onChange={(e) => set("description", e.target.value)} />
        </label>
        <label className="field">
          <span>location</span>
          <input value={form.location_text} onChange={(e) => set("location_text", e.target.value)} placeholder="Boston, MA" />
        </label>
        <label className="field">
          <span>institutional affiliation</span>
          <input value={form.institutional_affiliation} onChange={(e) => set("institutional_affiliation", e.target.value)} />
        </label>
        <label className="field">
          <span>tier</span>
          <select value={form.tier} onChange={(e) => set("tier", e.target.value)}>
            <option value="C">C — Practice</option>
            <option value="B">B — Standard</option>
            <option value="A">A — Verified</option>
          </select>
        </label>
        <label className="field">
          <span>contact email</span>
          <input type="email" value={form.contact_email} onChange={(e) => set("contact_email", e.target.value)} />
        </label>
        <label className="field">
          <span>website</span>
          <input type="url" value={form.website_url} onChange={(e) => set("website_url", e.target.value)} placeholder="https://…" />
        </label>
        {errors.map((m, i) => (
          <p className="form-error" key={i}>{m}</p>
        ))}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "..." : "[ save changes ]"}
        </button>
      </form>
      <p className="note">
        <Link href="/dashboard">&larr; dashboard</Link>
      </p>
    </main>
  );
}
