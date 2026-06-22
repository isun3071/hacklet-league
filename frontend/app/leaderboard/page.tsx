import Link from "next/link";
import { LeaderboardTable } from "@/components/LeaderboardTable";
import { getRankings } from "@/lib/api";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Leaderboard — HackLet League",
};

export default async function LeaderboardPage() {
  const rows = await getRankings("global");

  return (
    <main className="container block">
      <p className="prompt">/leaderboard</p>
      <h1 className="page-title"># global leaderboard</h1>
      <p className="subtitle">
        // all-time · Tier A chapters only — only controlled-workstation events carry global
        credentialing weight. Chapter boards live on each chapter&apos;s page.
      </p>

      <LeaderboardTable rows={rows} />

      <p className="note">
        <Link href="/chapters">browse chapters &rarr;</Link>
      </p>
    </main>
  );
}
