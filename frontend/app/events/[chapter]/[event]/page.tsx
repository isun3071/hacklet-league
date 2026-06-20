import Link from "next/link";
import { notFound } from "next/navigation";
import { getEvent, getEventParticipants, type Participant } from "@/lib/api";
import {
  ACCESS_LABEL,
  EVENT_TIER_LABEL,
  PLAYER_TIER_LABEL,
  ROLE_LABEL,
  SPECIALIZATION_LABEL,
  STATUS_LABEL,
  TIMER_MINUTES,
  fmtDateTime,
  variantName,
} from "@/lib/events";

export const dynamic = "force-dynamic";

const ROLE_ORDER: Record<string, number> = { player: 0, judge: 1, audience: 2 };

export default async function EventPage({
  params,
}: {
  params: Promise<{ chapter: string; event: string }>;
}) {
  const { chapter, event: eventSlug } = await params;
  const event = await getEvent(chapter, eventSlug);
  if (!event) notFound();

  let participants: Participant[] = [];
  try {
    participants = await getEventParticipants(event.id);
  } catch {
    participants = [];
  }
  participants.sort(
    (a, b) => (ROLE_ORDER[a.role] ?? 9) - (ROLE_ORDER[b.role] ?? 9),
  );

  const counts = participants.reduce<Record<string, number>>((acc, p) => {
    acc[p.role] = (acc[p.role] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <main className="container block">
      <p className="prompt">/events/{event.chapter.slug}/{event.slug}</p>
      <h1 className="page-title">{event.name}</h1>
      <p className="subtitle">
        // {variantName(event.format, event.timer)} · {TIMER_MINUTES[event.timer]} ·
        hosted by{" "}
        <Link href={`/chapters/${event.chapter.slug}`}>{event.chapter.name}</Link>
      </p>

      <div className="panel">
        <dl className="kv">
          <div>
            <dt>status</dt>
            <dd>{STATUS_LABEL[event.status]}</dd>
          </div>
          <div>
            <dt>starts</dt>
            <dd>{fmtDateTime(event.scheduled_start)}</dd>
          </div>
          <div>
            <dt>ends</dt>
            <dd>{fmtDateTime(event.scheduled_end)}</dd>
          </div>
          <div>
            <dt>registration</dt>
            <dd>{ACCESS_LABEL[event.access_mode]}</dd>
          </div>
          {/* The three distinct "tier" axes, labeled so they can't be confused. */}
          <div>
            <dt>scope</dt>
            <dd>{EVENT_TIER_LABEL[event.event_tier]} event</dd>
          </div>
          <div>
            <dt>host chapter tier</dt>
            <dd>Tier {event.chapter.tier}</dd>
          </div>
          <div>
            <dt>player eligibility</dt>
            <dd>{PLAYER_TIER_LABEL[event.player_tier_restriction]}</dd>
          </div>
        </dl>
        {event.description && <p className="chapter-desc">{event.description}</p>}
      </div>

      <h2 className="h2"># participants</h2>
      {participants.length === 0 ? (
        <p className="note">// no one registered yet.</p>
      ) : (
        <>
          <p className="subtitle">
            //{" "}
            {(["player", "judge", "audience"] as const)
              .filter((r) => counts[r])
              .map((r) => `${counts[r]} ${ROLE_LABEL[r].toLowerCase()}${counts[r] === 1 ? "" : "s"}`)
              .join(" · ")}
          </p>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>who</th>
                  <th>role</th>
                  <th>specialty</th>
                </tr>
              </thead>
              <tbody>
                {participants.map((p) => (
                  <tr key={p.id}>
                    <td>{p.display_name || "—"}</td>
                    <td>{ROLE_LABEL[p.role]}</td>
                    <td>
                      {p.role === "judge" ? SPECIALIZATION_LABEL[p.judge_specialization] : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <p className="note">
        <Link href="/events">&larr; all events</Link>
      </p>
    </main>
  );
}
