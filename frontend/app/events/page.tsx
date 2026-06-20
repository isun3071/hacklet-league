import Link from "next/link";
import { getEvents, type LeagueEvent } from "@/lib/api";
import {
  EVENT_TIER_LABEL,
  STATUS_LABEL,
  eventPath,
  fmtDate,
  variantName,
} from "@/lib/events";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Events — HackLet League",
};

export default async function EventsPage() {
  let events: LeagueEvent[] = [];
  let failed = false;
  try {
    events = await getEvents();
  } catch {
    failed = true;
  }

  return (
    <main className="container block">
      <h1 className="page-title"># events</h1>

      {failed ? (
        <p className="note">// events directory temporarily unavailable.</p>
      ) : events.length === 0 ? (
        <p className="note">
          // no events scheduled yet. <Link href="/chapters">browse chapters &rarr;</Link>
        </p>
      ) : (
        <>
          <p className="subtitle">
            // {events.length} event{events.length === 1 ? "" : "s"} on the board
          </p>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>event</th>
                  <th>format</th>
                  <th>scope</th>
                  <th>host</th>
                  <th>when</th>
                  <th>status</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td>
                      <Link href={eventPath(e)}>{e.name}</Link>
                    </td>
                    <td>{variantName(e.format, e.timer)}</td>
                    <td>{EVENT_TIER_LABEL[e.event_tier]}</td>
                    <td>
                      <Link href={`/chapters/${e.chapter.slug}`}>{e.chapter.name}</Link>
                    </td>
                    <td>{fmtDate(e.scheduled_start)}</td>
                    <td>{STATUS_LABEL[e.status]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
