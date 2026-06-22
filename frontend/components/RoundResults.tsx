"use client";

import { useCallback, useEffect, useState } from "react";
import { request } from "@/lib/http";
import type { RoundResults as Results, Standing } from "@/lib/rounds";

type View = "loading" | "hidden" | "ready" | "error";

/** Standings + categorical awards for a round. Self-hides (403) when results aren't yet
 * revealed and the viewer isn't staff, so it's safe to mount for anyone. */
export function RoundResults({ roundId, refreshKey = 0 }: { roundId: string; refreshKey?: number }) {
  const [view, setView] = useState<View>("loading");
  const [data, setData] = useState<Results | null>(null);

  const load = useCallback(async () => {
    const res = await request<Results>(`/api/rounds/${roundId}/results/`, "GET");
    if (res.status === 403) {
      setView("hidden");
      return;
    }
    if (res.ok && res.data) {
      setData(res.data);
      setView("ready");
      return;
    }
    setView("error");
  }, [roundId]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  if (view === "loading" || view === "hidden") return null;
  if (view === "error") {
    return <p className="note">// couldn&apos;t load results.</p>;
  }
  if (!data) return null;

  const winners = new Set(data.awards.best_overall);
  const byPlayer = (ids: string[]) =>
    ids
      .map((id) => data.standings.find((s) => s.player_id === id)?.player_display || "—")
      .join(", ") || "—";

  return (
    <section className="block">
      <h2 className="h2"># results{!data.revealed && " (preview)"}</h2>
      {!data.revealed && (
        <p className="note">// not yet public — visible to you as staff. Completing the round reveals them.</p>
      )}

      {data.standings.length === 0 ? (
        <p className="note">// no scored submissions yet.</p>
      ) : (
        <>
          <div className="panel">
            <p className="subtitle">// awards</p>
            <dl className="kv">
              <div>
                <dt>best overall</dt>
                <dd>{byPlayer(data.awards.best_overall)}</dd>
              </div>
              <div>
                <dt>most resilient</dt>
                <dd>{byPlayer(data.awards.most_resilient)}</dd>
              </div>
              <div>
                <dt>best communicator</dt>
                <dd>{byPlayer(data.awards.best_communicator)}</dd>
              </div>
            </dl>
          </div>

          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>player</th>
                  <th>engineering</th>
                  <th>communication</th>
                  <th>rank-sum</th>
                </tr>
              </thead>
              <tbody>
                {data.standings.map((s: Standing) => (
                  <tr key={s.submission_id}>
                    <td>
                      {s.overall_rank}
                      {winners.has(s.player_id) ? " ★" : ""}
                    </td>
                    <td>{s.player_display || "—"}</td>
                    <td>
                      {s.engineering_score.toFixed(1)}{" "}
                      <span className="dim">(#{s.engineering_rank})</span>
                    </td>
                    <td>
                      {s.communication_score.toFixed(1)}{" "}
                      <span className="dim">(#{s.communication_rank})</span>
                    </td>
                    <td>{s.rank_sum}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="note">
            // engineering = judge stand-in for the Fuzz Score until the Stage 5 runner lands.
          </p>
        </>
      )}
    </section>
  );
}
