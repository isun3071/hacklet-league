import Link from "next/link";
import { LeaderboardTable } from "@/components/LeaderboardTable";
import { getRankings } from "@/lib/api";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Leaderboard, HackLet League",
};

export default async function LeaderboardPage() {
  const rows = await getRankings("global");

  return (
    <main className="container block">
      <p className="prompt">/leaderboard</p>
      <h1 className="page-title"># the verified board</h1>
      <p className="subtitle">
        // all-time, Tier A events only. HackLet keeps a global board per tier: Verified (Tier A,
        shown here), Open (Tier B), and Developmental (Tier C). You never compare across them, so
        the other two open once those tiers run. Chapter boards live on each chapter&apos;s page.
      </p>

      {rows.length === 0 ? (
        <p className="note">// nothing here yet. first event fall 2026.</p>
      ) : (
        <>
          <LeaderboardTable rows={rows} />
          <p className="note">
            <Link href="/chapters">browse chapters &rarr;</Link>
          </p>
        </>
      )}
    </main>
  );
}
