"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { request } from "@/lib/http";
import { Icon } from "@/components/Icon";
import type { Chapter, ChapterStat, LeagueEvent, Participant } from "@/lib/api";
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
  const [stats, setStats] = useState<ChapterStat[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "unauth">("loading");

  useEffect(() => {
    (async () => {
      const ch = await request<Chapter[]>("/api/chapters/mine/", "GET");
      if (ch.status !== 200 || !Array.isArray(ch.data)) {
        setState("unauth");
        return;
      }
      setChapters(ch.data);
      const [ev, pp, st] = await Promise.all([
        request<LeagueEvent[]>("/api/events/mine/", "GET"),
        request<Participant[]>("/api/event-participants/mine/", "GET"),
        request<ChapterStat[]>("/api/chapters/stats/", "GET"),
      ]);
      if (ev.data) setEvents(ev.data);
      if (pp.data) setParts(pp.data);
      if (st.data) setStats(st.data);
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

  const statById = new Map(stats.map((s) => [s.chapter_id, s]));
  const totals = stats.reduce(
    (a, s) => ({
      events: a.events + s.events_total,
      players: a.players + s.players,
      rounds: a.rounds + s.rounds_total,
      ranked: a.ranked + s.ranked_players,
    }),
    { events: 0, players: 0, rounds: 0, ranked: 0 },
  );
  const metric = (num: number, label: string) => (
    <div className="stat stat--sm">
      <span className="stat-num">{num}</span>
      <span className="stat-label">{label}</span>
    </div>
  );

  return (
    <main className="container block">
      <h1 className="page-title"># dashboard</h1>

      {chapters.length > 0 && (
        <div className="statband">
          <div className="stat">
            <span className="stat-num">{chapters.length}</span>
            <span className="stat-label">chapters</span>
          </div>
          <div className="stat">
            <span className="stat-num">{totals.events}</span>
            <span className="stat-label">events hosted</span>
          </div>
          <div className="stat">
            <span className="stat-num">{totals.players}</span>
            <span className="stat-label">player regs</span>
          </div>
          <div className="stat">
            <span className="stat-num">{totals.rounds}</span>
            <span className="stat-label">rounds run</span>
          </div>
          <div className="stat">
            <span className="stat-num">{totals.ranked}</span>
            <span className="stat-label">ranked players</span>
          </div>
        </div>
      )}

      {/* chapters */}
      <h2 className="h2" id="my-chapters"># my chapters</h2>
      {chapters.length === 0 ? (
        <p className="note">
          // no chapters yet. <Link href="/chapters/new">apply to create one &rarr;</Link>
        </p>
      ) : (
        <div className="statcards">
          {chapters.map((c) => {
            const badge = CHAPTER_STATUS[c.verification_status] ?? {
              label: c.verification_status,
              cls: "badge-unverified",
            };
            const s = statById.get(c.id);
            return (
              <div className="statcard" key={c.id}>
                <div className="statcard-head">
                  <Link href={`/chapters/${c.slug}`} className="statcard-title">
                    {c.name}
                  </Link>
                  <span className="dim">Tier {c.tier}</span>
                  <span className={`badge ${badge.cls}`}>{badge.label}</span>
                </div>
                <div className="statcard-metrics">
                  {metric(s?.events_total ?? 0, "events")}
                  {metric(s?.players ?? 0, "players")}
                  {metric(s?.judges ?? 0, "judges")}
                  {metric(s?.members_total ?? 0, "members")}
                  {metric(s?.rounds_total ?? 0, "rounds")}
                  {metric(s?.ranked_players ?? 0, "ranked")}
                </div>
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
              </div>
            );
          })}
        </div>
      )}

      {/* events I run */}
      <h2 className="h2" id="events-i-run"># events i run</h2>
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
