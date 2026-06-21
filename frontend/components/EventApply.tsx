"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { request } from "@/lib/http";
import { getSession } from "@/lib/auth";
import { Icon } from "@/components/Icon";
import type { AccessMode, EventStatus, ParticipantRole } from "@/lib/api";

const OPTIONS: { role: ParticipantRole; label: string }[] = [
  { role: "player", label: "I want to compete" },
  { role: "judge", label: "I want to judge" },
  { role: "audience", label: "I want to attend" },
];

const CLOSED_NOTE: Partial<Record<EventStatus, string>> = {
  scheduled: "registration hasn't opened yet — check back soon.",
  registration_closed: "registration has closed for this event.",
  in_progress: "this event is underway.",
  completed: "this event has concluded.",
  cancelled: "this event was cancelled.",
};

export function EventApply({
  eventId,
  accessMode,
  status,
}: {
  eventId: string;
  accessMode: AccessMode;
  status: EventStatus;
}) {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [spec, setSpec] = useState("general");

  useEffect(() => {
    getSession().then((s) => setAuthed(s === 200));
  }, []);

  if (accessMode !== "application") {
    return (
      <p className="note">// invite-only — you need an invitation from the organizers to take part.</p>
    );
  }
  if (status !== "registration_open") {
    return <p className="note">// {CLOSED_NOTE[status] ?? "registration is closed."}</p>;
  }
  if (authed === null) return null;
  if (authed === false) {
    return (
      <p className="note">
        // <Link href="/auth/login">log in</Link> to compete, judge, or attend.
      </p>
    );
  }
  if (result) return <p className="ok-msg">{result}</p>;

  async function apply(role: ParticipantRole) {
    setBusy(true);
    setErrors([]);
    const body: Record<string, string> = { role };
    if (role === "judge") body.judge_specialization = spec;
    const res = await request<{ status: string }>(
      `/api/events/${eventId}/apply/`,
      "POST",
      body,
    );
    setBusy(false);
    if (res.status === 201 && res.data) {
      setResult(
        res.data.status === "registered"
          ? "You're in — see you there. 🎉"
          : "Application submitted — pending organizer review.",
      );
      return;
    }
    setErrors(res.errors.length ? res.errors : ["Could not apply."]);
  }

  return (
    <div className="panel">
      <p className="subtitle">// take part</p>
      <div className="actions">
        {OPTIONS.map((o) => (
          <button
            key={o.role}
            className="btn"
            type="button"
            disabled={busy}
            onClick={() => apply(o.role)}
          >
            [ <Icon name={o.role} /> {o.label} ]
          </button>
        ))}
      </div>
      <label className="field">
        <span>judge specialty (only if judging)</span>
        <select value={spec} onChange={(e) => setSpec(e.target.value)}>
          <option value="general">General</option>
          <option value="tester">Tester</option>
          <option value="ux_designer">UX Designer</option>
        </select>
      </label>
      {errors.map((m, i) => (
        <p className="form-error" key={i}>
          {m}
        </p>
      ))}
    </div>
  );
}
