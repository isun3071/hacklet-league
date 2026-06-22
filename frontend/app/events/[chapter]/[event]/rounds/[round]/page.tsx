import Link from "next/link";
import { notFound } from "next/navigation";
import { RoundLive } from "@/components/RoundLive";
import { getEvent, getRoundByNumber } from "@/lib/api";
import { variantName } from "@/lib/events";

export const dynamic = "force-dynamic";

export default async function RoundPage({
  params,
}: {
  params: Promise<{ chapter: string; event: string; round: string }>;
}) {
  const { chapter, event: eventSlug, round: roundParam } = await params;
  const event = await getEvent(chapter, eventSlug);
  if (!event) notFound();

  const roundNumber = Number(roundParam);
  if (!Number.isInteger(roundNumber)) notFound();
  const round = await getRoundByNumber(event.id, roundNumber);
  if (!round) notFound();

  return (
    <main className="container block">
      <p className="prompt">
        /events/{event.chapter.slug}/{event.slug}/rounds/{round.round_number}
      </p>
      <h1 className="page-title">
        {event.name} — round {round.round_number}
      </h1>
      <p className="subtitle">
        // {variantName(event.format, event.timer)} · hosted by{" "}
        <Link href={`/chapters/${event.chapter.slug}`}>{event.chapter.name}</Link> ·{" "}
        <Link href={`/events/${event.chapter.slug}/${event.slug}`}>event page</Link>
      </p>

      <RoundLive initialRound={round} />

      <p className="note">
        <Link href={`/events/${event.chapter.slug}/${event.slug}`}>&larr; back to event</Link>
      </p>
    </main>
  );
}
