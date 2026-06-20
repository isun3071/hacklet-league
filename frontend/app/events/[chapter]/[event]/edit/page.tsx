"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { request } from "@/lib/http";
import type { LeagueEvent } from "@/lib/api";
import {
  ACCESS_LABEL,
  EVENT_TIER_LABEL,
  FORMAT_LABEL,
  PLAYER_TIER_LABEL,
  STATUS_LABEL,
  TIMER_LABEL,
} from "@/lib/events";

const BLANK = {
  name: "",
  description: "",
  event_tier: "chapter",
  format: "vibe",
  timer: "sprint",
  access_mode: "application",
  player_tier_restriction: "any",
  status: "scheduled",
  scheduled_start: "",
  scheduled_end: "",
};

const toUtcIso = (local: string) => new Date(`${local}Z`).toISOString();
const toLocalInput = (iso: string) => iso.slice(0, 16); // UTC wall-clock for datetime-local

function options(map: Record<string, string>) {
  return Object.entries(map).map(([value, label]) => (
    <option key={value} value={value}>
      {label}
    </option>
  ));
}

export default function EditEventPage() {
  const router = useRouter();
  const params = useParams<{ chapter: string; event: string }>();
  const [event, setEvent] = useState<LeagueEvent | null>(null);
  const [form, setForm] = useState(BLANK);
  const [state, setState] = useState<"loading" | "ready" | "notfound">("loading");
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    request<LeagueEvent[]>(
      `/api/events/?chapter=${params.chapter}&slug=${params.event}`,
      "GET",
    ).then((res) => {
      const ev = res.data?.[0];
      if (!ev) {
        setState("notfound");
        return;
      }
      setEvent(ev);
      setForm({
        name: ev.name,
        description: ev.description,
        event_tier: ev.event_tier,
        format: ev.format,
        timer: ev.timer,
        access_mode: ev.access_mode,
        player_tier_restriction: ev.player_tier_restriction,
        status: ev.status,
        scheduled_start: toLocalInput(ev.scheduled_start),
        scheduled_end: toLocalInput(ev.scheduled_end),
      });
      setState("ready");
    });
  }, [params.chapter, params.event]);

  function set(key: keyof typeof BLANK, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!event) return;
    setBusy(true);
    setErrors([]);
    const payload = {
      ...form,
      scheduled_start: toUtcIso(form.scheduled_start),
      scheduled_end: toUtcIso(form.scheduled_end),
    };
    const res = await request<LeagueEvent>(`/api/events/${event.id}/`, "PATCH", payload);
    setBusy(false);
    if (res.ok && res.data) {
      router.push(`/events/${res.data.chapter.slug}/${res.data.slug}`);
      return;
    }
    if (res.status === 404) {
      setErrors(["You don't manage this event."]);
      return;
    }
    setErrors(res.errors.length ? res.errors : ["Could not save."]);
  }

  if (state === "loading") {
    return (
      <main className="container block">
        <p className="body">Loading…</p>
      </main>
    );
  }
  if (state === "notfound") {
    return (
      <main className="container block">
        <h1 className="page-title"># edit event</h1>
        <p className="note">// event not found, or you don&apos;t manage it.</p>
      </main>
    );
  }

  return (
    <main className="container block">
      <h1 className="page-title"># edit event</h1>
      <p className="subtitle">// {event?.name}</p>
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
          <span>status</span>
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            {options(STATUS_LABEL)}
          </select>
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
          {busy ? "..." : "[ save changes ]"}
        </button>
      </form>
      {event && (
        <p className="note">
          <Link href={`/events/${event.chapter.slug}/${event.slug}`}>&larr; back to event</Link>
        </p>
      )}
    </main>
  );
}
