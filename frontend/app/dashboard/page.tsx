"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { request } from "@/lib/http";
import { Icon } from "@/components/Icon";
import type { Chapter, LeagueEvent, Participant } from "@/lib/api";
import {
  PARTICIPANT_STATUS_LABEL,
  ROLE_LABEL,
  SOURCE_LABEL,
  STATUS_LABEL,
  fmtDate,
} from "@/lib/events";

const CHAPTER_STATUS: Record<string, { label: string; cls: string }> = {
  pending: { label: "pending review", cls: "badge-pending" },
  verified: { label: "verified", cls: "badge-verified" },
  suspended: { label: "suspended", cls: "badge-suspended" },
  unverified: { label: "not approved", cls: "badge-unverified" },
};

export default function DashboardPage() {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [events, setEvents] = useState<LeagueEvent[]>([]);
  const [parts, setParts] = useState<Participant[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "unauth">("loading");

  useEffect(() => {
    (async () => {
      const ch = await request<Chapter[]>("/api/chapters/mine/", "GET");
      if (ch.status !== 200 || !Array.isArray(ch.data)) {
        setState("unauth");
        return;
      }
      setChapters(ch.data);
      const [ev, pp] = await Promise.all([
        request<LeagueEvent[]>("/api/events/mine/", "GET"),
        request<Participant[]>("/api/event-participants/mine/", "GET"),
      ]);
      if (ev.data) setEvents(ev.data);
      if (pp.data) setParts(pp.data);
      setState("ready");
    })();
  }, []);

  async function refetchParts() {
    const pp = await request<Participant[]>("/api/event-participants/mine/", "GET");
    if (pp.data) setParts(pp.data);
  }

  async function respond(p: Participant, action: "accept" | "decline") {
    const res = await request(`/api/event-participants/${p.id}/respond/`, "POST", { action });
    if (res.ok) refetchParts();
  }

  async function withdraw(p: Participant) {
    if (!window.confirm("Withdraw from this event?")) return;
    const res = await request(`/api/event-participants/${p.id}/withdraw/`, "POST", {});
    if (res.ok) refetchParts();
  }

  async function deleteChapter(c: Chapter) {
    if (!window.confirm(`Delete "${c.name}"? This can't be undone.`)) return;
    const res = await request(`/api/chapters/${c.slug}/`, "DELETE");
    if (res.ok) setChapters((prev) => prev.filter((x) => x.id !== c.id));
    else window.alert("Could not delete that chapter.");
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
        <h1 className="page-title"># dashboard</h1>
        <p className="body">
          You need to <Link href="/auth/login">log in</Link> to see your dashboard.
        </p>
      </main>
    );
  }

  return (
    <main className="container block">
      <h1 className="page-title"># dashboard</h1>

      {/* chapters */}
      <h2 className="h2"># my chapters</h2>
      {chapters.length === 0 ? (
        <p className="note">
          // no chapters yet. <Link href="/chapters/new">apply to create one &rarr;</Link>
        </p>
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>chapter</th>
                <th>tier</th>
                <th>status</th>
                <th>actions</th>
              </tr>
            </thead>
            <tbody>
              {chapters.map((c) => {
                const s = CHAPTER_STATUS[c.verification_status] ?? {
                  label: c.verification_status,
                  cls: "badge-unverified",
                };
                return (
                  <tr key={c.id}>
                    <td>
                      <Link href={`/chapters/${c.slug}`}>{c.name}</Link>
                    </td>
                    <td>{c.tier}</td>
                    <td>
                      <span className={`badge ${s.cls}`}>{s.label}</span>
                    </td>
                    <td>
                      <div className="row-actions">
                        <Link href={`/events/new?chapter=${c.slug}`}>new event</Link>
                        <Link href={`/chapters/${c.slug}/staff`}>staff</Link>
                        <Link href={`/chapters/${c.slug}/edit`}>edit</Link>
                        <button
                          type="button"
                          className="linkbtn-danger"
                          onClick={() => deleteChapter(c)}
                        >
                          delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* events I run */}
      <h2 className="h2"># events i run</h2>
      {events.length === 0 ? (
        <p className="note">// no events yet — create one from a chapter above.</p>
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>event</th>
                <th>chapter</th>
                <th>when</th>
                <th>status</th>
                <th>actions</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>
                    <Link href={`/events/${e.chapter.slug}/${e.slug}`}>{e.name}</Link>
                  </td>
                  <td>{e.chapter.name}</td>
                  <td>{fmtDate(e.scheduled_start)}</td>
                  <td>{STATUS_LABEL[e.status]}</td>
                  <td>
                    <div className="row-actions">
                      <Link href={`/events/${e.chapter.slug}/${e.slug}/manage`}>manage</Link>
                      <Link href={`/events/${e.chapter.slug}/${e.slug}/edit`}>edit</Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* my participations */}
      <h2 className="h2"># my invitations &amp; applications</h2>
      {parts.length === 0 ? (
        <p className="note">
          // nothing yet. <Link href="/events">browse events &rarr;</Link>
        </p>
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>event</th>
                <th>role</th>
                <th>via</th>
                <th>status</th>
                <th>actions</th>
              </tr>
            </thead>
            <tbody>
              {parts.map((p) => {
                const isInvitePending = p.source === "invited" && p.status === "pending";
                const canWithdraw = p.status === "pending" || p.status === "registered";
                return (
                  <tr key={p.id}>
                    <td>
                      <Link href={`/events/${p.event.chapter_slug}/${p.event.slug}`}>
                        {p.event.name}
                      </Link>
                    </td>
                    <td>
                      <span className="icon-label">
                        <Icon name={p.role} /> {ROLE_LABEL[p.role]}
                      </span>
                    </td>
                    <td>{SOURCE_LABEL[p.source]}</td>
                    <td>{PARTICIPANT_STATUS_LABEL[p.status]}</td>
                    <td>
                      <div className="row-actions">
                        {isInvitePending && (
                          <>
                            <button
                              type="button"
                              className="linkbtn"
                              onClick={() => respond(p, "accept")}
                            >
                              accept
                            </button>
                            <button
                              type="button"
                              className="linkbtn-danger"
                              onClick={() => respond(p, "decline")}
                            >
                              decline
                            </button>
                          </>
                        )}
                        {!isInvitePending && canWithdraw && (
                          <button
                            type="button"
                            className="linkbtn-danger"
                            onClick={() => withdraw(p)}
                          >
                            withdraw
                          </button>
                        )}
                        {!isInvitePending && !canWithdraw && <span className="dim">—</span>}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
