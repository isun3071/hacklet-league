"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { request } from "@/lib/http";
import { RoundManager } from "@/components/RoundManager";
import type {
  ChapterStaffRow,
  LeagueEvent,
  Participant,
  ParticipantRole,
} from "@/lib/api";
import {
  PARTICIPANT_STATUS_LABEL,
  ROLE_LABEL,
  SOURCE_LABEL,
  SPECIALIZATION_LABEL,
  STATUS_LABEL,
  variantName,
} from "@/lib/events";

type LoadState = "loading" | "ready" | "notmanager" | "notfound";

const SPEC_OPTIONS = [
  { value: "general", label: "General" },
  { value: "tester", label: "Tester" },
  { value: "ux_designer", label: "UX Designer" },
];

export default function ManageEventPage() {
  const params = useParams<{ chapter: string; event: string }>();
  const [state, setState] = useState<LoadState>("loading");
  const [event, setEvent] = useState<LeagueEvent | null>(null);
  const [staff, setStaff] = useState<ChapterStaffRow[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);

  // invite form
  const [invite, setInvite] = useState({ email: "", role: "player", spec: "general" });
  // corps judge assignment
  const [corps, setCorps] = useState({ staffId: "", spec: "general" });
  const [actionError, setActionError] = useState<string | null>(null);

  const refetchParticipants = useCallback(async (eventId: string) => {
    const res = await request<Participant[]>(`/api/events/${eventId}/participants/`, "GET");
    if (res.ok && res.data) setParticipants(res.data);
  }, []);

  useEffect(() => {
    (async () => {
      const evRes = await request<LeagueEvent[]>(
        `/api/events/?chapter=${params.chapter}&slug=${params.event}`,
        "GET",
      );
      const ev = evRes.data?.[0];
      if (!ev) {
        setState("notfound");
        return;
      }
      setEvent(ev);
      const staffRes = await request<ChapterStaffRow[]>(
        `/api/chapter-staff/?chapter=${params.chapter}`,
        "GET",
      );
      if (staffRes.status === 403 || staffRes.status === 401) {
        setState("notmanager");
        return;
      }
      if (staffRes.ok && staffRes.data) setStaff(staffRes.data);
      await refetchParticipants(ev.id);
      setState("ready");
    })();
  }, [params.chapter, params.event, refetchParticipants]);

  async function decide(p: Participant, action: "approve" | "reject") {
    setActionError(null);
    const res = await request(`/api/event-participants/${p.id}/decide/`, "POST", { action });
    if (res.ok && event) await refetchParticipants(event.id);
    else setActionError(res.errors[0] ?? "Could not update that application.");
  }

  async function sendInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!event) return;
    setActionError(null);
    const body: Record<string, string> = { email: invite.email, role: invite.role };
    if (invite.role === "judge") body.judge_specialization = invite.spec;
    const res = await request(`/api/events/${event.id}/invite/`, "POST", body);
    if (res.status === 201) {
      setInvite({ email: "", role: "player", spec: "general" });
      await refetchParticipants(event.id);
    } else {
      setActionError(res.errors[0] ?? "Could not send invite.");
    }
  }

  async function assignCorps(e: React.FormEvent) {
    e.preventDefault();
    if (!event || !corps.staffId) return;
    setActionError(null);
    const res = await request(`/api/events/${event.id}/add-corps-judge/`, "POST", {
      chapter_staff_id: corps.staffId,
      judge_specialization: corps.spec,
    });
    if (res.status === 201) {
      setCorps({ staffId: "", spec: "general" });
      await refetchParticipants(event.id);
    } else {
      setActionError(res.errors[0] ?? "Could not assign judge.");
    }
  }

  if (state === "loading") {
    return (
      <main className="container block">
        <p className="body">Loading…</p>
      </main>
    );
  }
  if (state === "notfound" || state === "notmanager") {
    return (
      <main className="container block">
        <h1 className="page-title"># manage event</h1>
        <p className="note">
          //{" "}
          {state === "notfound"
            ? "event not found."
            : "you don't manage this event's chapter."}
        </p>
      </main>
    );
  }

  const ev = event!;
  const pendingApplications = participants.filter(
    (p) => p.source === "applied" && p.status === "pending",
  );
  const pendingInvites = participants.filter(
    (p) => p.source === "invited" && p.status === "pending",
  );
  const participantEmails = new Set(participants.map((p) => p.email).filter(Boolean));
  const corpsCandidates = staff.filter(
    (s) =>
      s.status === "active" &&
      s.roles.includes("judge") &&
      !participantEmails.has(s.email),
  );

  return (
    <main className="container block">
      <p className="prompt">/events/{ev.chapter.slug}/{ev.slug}/manage</p>
      <h1 className="page-title"># manage: {ev.name}</h1>
      <p className="subtitle">
        // {variantName(ev.format, ev.timer)} · {STATUS_LABEL[ev.status]} ·{" "}
        <Link href={`/events/${ev.chapter.slug}/${ev.slug}`}>public page</Link> ·{" "}
        <Link href={`/events/${ev.chapter.slug}/${ev.slug}/edit`}>edit event</Link>
      </p>

      {actionError && <p className="form-error">{actionError}</p>}

      {/* rounds — the competition lifecycle */}
      <RoundManager
        eventId={ev.id}
        chapterSlug={ev.chapter.slug}
        eventSlug={ev.slug}
        format={ev.format}
      />

      {/* applications awaiting a decision */}
      <h2 className="h2"># pending applications</h2>
      {pendingApplications.length === 0 ? (
        <p className="note">// nothing waiting.</p>
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>who</th>
                <th>role</th>
                <th>specialty</th>
                <th>decision</th>
              </tr>
            </thead>
            <tbody>
              {pendingApplications.map((p) => (
                <tr key={p.id}>
                  <td>{p.email || p.display_name || "—"}</td>
                  <td>{ROLE_LABEL[p.role]}</td>
                  <td>{p.role === "judge" ? SPECIALIZATION_LABEL[p.judge_specialization] : "—"}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="linkbtn" onClick={() => decide(p, "approve")}>
                        approve
                      </button>
                      <button
                        type="button"
                        className="linkbtn-danger"
                        onClick={() => decide(p, "reject")}
                      >
                        reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* invite */}
      <h2 className="h2"># invite someone</h2>
      <form className="form" onSubmit={sendInvite}>
        <label className="field">
          <span>email *</span>
          <input
            type="email"
            value={invite.email}
            onChange={(e) => setInvite((f) => ({ ...f, email: e.target.value }))}
            required
          />
        </label>
        <label className="field">
          <span>role</span>
          <select
            value={invite.role}
            onChange={(e) => setInvite((f) => ({ ...f, role: e.target.value }))}
          >
            <option value="player">Player</option>
            <option value="judge">Judge</option>
            <option value="audience">Audience</option>
          </select>
        </label>
        {invite.role === "judge" && (
          <label className="field">
            <span>specialty</span>
            <select
              value={invite.spec}
              onChange={(e) => setInvite((f) => ({ ...f, spec: e.target.value }))}
            >
              {SPEC_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        )}
        <button className="btn" type="submit">
          [ send invite ]
        </button>
      </form>
      {pendingInvites.length > 0 && (
        <p className="note">
          // awaiting response:{" "}
          {pendingInvites.map((p) => `${p.email || p.display_name} (${ROLE_LABEL[p.role]})`).join(", ")}
        </p>
      )}

      {/* corps judges */}
      <h2 className="h2"># assign a corps judge</h2>
      {corpsCandidates.length === 0 ? (
        <p className="note">
          // no available chapter judges. Add judges in{" "}
          <Link href={`/chapters/${ev.chapter.slug}/staff`}>staff management</Link>.
        </p>
      ) : (
        <form className="form" onSubmit={assignCorps}>
          <label className="field">
            <span>chapter judge</span>
            <select
              value={corps.staffId}
              onChange={(e) => setCorps((f) => ({ ...f, staffId: e.target.value }))}
              required
            >
              <option value="">— pick a judge —</option>
              {corpsCandidates.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.display_name ? `${s.display_name} (${s.email})` : s.email}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>specialty</span>
            <select
              value={corps.spec}
              onChange={(e) => setCorps((f) => ({ ...f, spec: e.target.value }))}
            >
              {SPEC_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <button className="btn" type="submit">
            [ assign judge ]
          </button>
        </form>
      )}

      {/* everyone */}
      <h2 className="h2"># all participants</h2>
      {participants.length === 0 ? (
        <p className="note">// no participants yet.</p>
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>who</th>
                <th>role</th>
                <th>source</th>
                <th>status</th>
                <th>specialty</th>
              </tr>
            </thead>
            <tbody>
              {participants.map((p) => (
                <tr key={p.id}>
                  <td>{p.email || p.display_name || "—"}</td>
                  <td>{ROLE_LABEL[p.role]}</td>
                  <td>{SOURCE_LABEL[p.source]}</td>
                  <td>{PARTICIPANT_STATUS_LABEL[p.status]}</td>
                  <td>{p.role === "judge" ? SPECIALIZATION_LABEL[p.judge_specialization] : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="note">
        <Link href="/dashboard">&larr; dashboard</Link>
      </p>
    </main>
  );
}
