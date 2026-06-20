"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { request } from "@/lib/http";
import type { LeagueEvent } from "@/lib/api";
import {
  ACCESS_LABEL,
  EVENT_TIER_LABEL,
  FORMAT_LABEL,
  PLAYER_TIER_LABEL,
  TIMER_LABEL,
} from "@/lib/events";

const EMPTY = {
  name: "",
  description: "",
  event_tier: "chapter",
  format: "vibe",
  timer: "sprint",
  access_mode: "application",
  player_tier_restriction: "any",
  scheduled_start: "",
  scheduled_end: "",
};

// datetime-local gives a naive "YYYY-MM-DDTHH:MM"; we treat it as UTC (matches how the
// app displays times) by appending Z, then normalize to a full ISO string.
function toUtcIso(local: string): string {
  return new Date(`${local}Z`).toISOString();
}

function options(map: Record<string, string>) {
  return Object.entries(map).map(([value, label]) => (
    <option key={value} value={value}>
      {label}
    </option>
  ));
}

function NewEventForm() {
  const router = useRouter();
  const chapter = useSearchParams().get("chapter") ?? "";
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  function set(key: keyof typeof EMPTY, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  if (!chapter) {
    return (
      <main className="container block">
        <h1 className="page-title"># new event</h1>
        <p className="note">
          // pick which chapter to host under from your{" "}
          <Link href="/dashboard">dashboard</Link>.
        </p>
      </main>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErrors([]);
    const payload = {
      chapter,
      ...form,
      scheduled_start: toUtcIso(form.scheduled_start),
      scheduled_end: toUtcIso(form.scheduled_end),
    };
    const res = await request<LeagueEvent>("/api/events/", "POST", payload);
    setBusy(false);
    if (res.status === 201 && res.data) {
      router.push(`/events/${res.data.chapter.slug}/${res.data.slug}/manage`);
      return;
    }
    if (res.status === 403) {
      setErrors(["You don't manage this chapter."]);
      return;
    }
    setErrors(res.errors.length ? res.errors : ["Could not create event."]);
  }

  return (
    <main className="container block">
      <h1 className="page-title"># new event</h1>
      <p className="subtitle">// hosting under chapter: {chapter}</p>
      <form className="form" onSubmit={onSubmit}>
        <label className="field">
          <span>name *</span>
          <input value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </label>
        <label className="field">
          <span>description</span>
          <textarea
            rows={3}
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </label>
        <label className="field">
          <span>format</span>
          <select value={form.format} onChange={(e) => set("format", e.target.value)}>
            {options(FORMAT_LABEL)}
          </select>
        </label>
        <label className="field">
          <span>timer</span>
          <select value={form.timer} onChange={(e) => set("timer", e.target.value)}>
            {options(TIMER_LABEL)}
          </select>
        </label>
        <label className="field">
          <span>scope (event tier)</span>
          <select value={form.event_tier} onChange={(e) => set("event_tier", e.target.value)}>
            {options(EVENT_TIER_LABEL)}
          </select>
        </label>
        <label className="field">
          <span>registration</span>
          <select value={form.access_mode} onChange={(e) => set("access_mode", e.target.value)}>
            {options(ACCESS_LABEL)}
          </select>
        </label>
        <label className="field">
          <span>player eligibility</span>
          <select
            value={form.player_tier_restriction}
            onChange={(e) => set("player_tier_restriction", e.target.value)}
          >
            {options(PLAYER_TIER_LABEL)}
          </select>
        </label>
        <label className="field">
          <span>starts (UTC) *</span>
          <input
            type="datetime-local"
            value={form.scheduled_start}
            onChange={(e) => set("scheduled_start", e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>ends (UTC) *</span>
          <input
            type="datetime-local"
            value={form.scheduled_end}
            onChange={(e) => set("scheduled_end", e.target.value)}
            required
          />
        </label>
        {errors.map((m, i) => (
          <p className="form-error" key={i}>
            {m}
          </p>
        ))}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "..." : "[ create event ]"}
        </button>
      </form>
      <p className="note">
        <Link href="/dashboard">&larr; dashboard</Link>
      </p>
    </main>
  );
}

export default function NewEventPage() {
  // useSearchParams must be inside a Suspense boundary in the App Router.
  return (
    <Suspense fallback={<main className="container block"><p className="body">Loading…</p></main>}>
      <NewEventForm />
    </Suspense>
  );
}
