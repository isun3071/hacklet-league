"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { request } from "@/lib/http";

const EMPTY = {
  name: "",
  description: "",
  location_text: "",
  institutional_affiliation: "",
  tier: "C",
  contact_email: "",
  website_url: "",
};

export default function NewChapterPage() {
  const router = useRouter();
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  function set(key: keyof typeof EMPTY, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErrors([]);
    const res = await request<{ slug: string }>("/api/chapters/", "POST", form);
    setBusy(false);
    if (res.status === 201 && res.data) {
      router.push(`/chapters/${res.data.slug}`);
      return;
    }
    if (res.status === 403) {
      setErrors(["You need to log in to create a chapter."]);
      return;
    }
    setErrors(res.errors.length ? res.errors : ["Could not create chapter."]);
  }

  return (
    <main className="container block">
      <h1 className="page-title"># new chapter</h1>
      <p className="subtitle">
        // submitted chapters are reviewed before they appear in the directory.
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
          {busy ? "..." : "[ submit chapter ]"}
        </button>
      </form>
      <p className="note">
        <Link href="/chapters">&larr; all chapters</Link>
      </p>
    </main>
  );
}
