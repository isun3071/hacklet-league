import type { Ranking } from "@/lib/rounds";

/** Presentational leaderboard table (server component). Shared by the global board and the
 * per-chapter board. */
export function LeaderboardTable({ rows }: { rows: Ranking[] }) {
  if (rows.length === 0) {
    return <p className="note">// no ranked players yet — standings appear once a round completes.</p>;
  }
  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            <th>#</th>
            <th>player</th>
            <th>points</th>
            <th>events</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.user_id}>
              <td>{r.rank}</td>
              <td>{r.player_display || "—"}</td>
              <td>{Number(r.rank_points).toFixed(1)}</td>
              <td>{r.events_competed}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
