"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { request } from "@/lib/http";
import {
  PHASE_LABEL,
  TIMING_PROFILE_LABEL,
  type Round,
  type TimingProfile,
} from "@/lib/rounds";

const PROFILES: TimingProfile[] = ["tier_c_mvr", "tier_c_extended", "tier_a"];

/** Chapter-manager controls for an event's rounds: create, schedule, start, complete, cancel.
 * Embedded in the event manage page. All actions are server-authoritative (the server owns the
 * absolute phase timeline); this is just the trigger surface. */
export function RoundManager({
  eventId,
  chapterSlug,
  eventSlug,
}: {
  eventId: string;
  chapterSlug: string;
  eventSlug: string;
}) {
  const [rounds, setRounds] = useState<Round[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState({ profile: "tier_c_mvr", players: "", prompt: "" });
  const [when, setWhen] = useState<Record<string, string>>({}); // roundId -> datetime-local

  const load = useCallback(async () => {
    const res = await request<Round[]>(`/api/rounds/?event=${eventId}`, "GET");
    if (res.ok && res.data) {
      setRounds([...res.data].sort((a, b) => a.round_number - b.round_number));
    }
    setLoaded(true);
  }, [eventId]);

  useEffect(() => {
    load();
  }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    const body: Record<string, unknown> = { event: eventId, timing_profile: form.profile };
    if (form.players) body.player_count = Number(form.players);
    if (form.prompt) body.prompt_revealed = form.prompt;
    const res = await request(`/api/rounds/`, "POST", body);
    if (res.status === 201) {
      setForm({ profile: form.profile, players: "", prompt: "" });
      await load();
    } else setErr(res.errors[0] ?? "Could not create round.");
  }

  async function act(round: Round, action: "schedule" | "start" | "complete" | "cancel") {
    setErr(null);
    let body: Record<string, unknown> = {};
    if (action === "schedule") {
      const local = when[round.id];
      if (!local) {
        setErr("Pick an opening time first.");
        return;
      }
      // datetime-local is local wall-clock; convert to absolute UTC ISO for the server.
      body = { opening_at: new Date(local).toISOString() };
    }
    const res = await request(`/api/rounds/${round.id}/${action}/`, "POST", body);
    if (res.ok) await load();
    else setErr(res.errors[0] ?? `Could not ${action} the round.`);
  }

  if (!loaded) return <p className="note">// loading rounds…</p>;

  const terminal = (r: Round) => r.status === "completed" || r.status === "cancelled";

  return (
    <section className="block">
      <h2 className="h2"># rounds</h2>
      {err && <p className="form-error">{err}</p>}

      {rounds.length === 0 ? (
        <p className="note">// no rounds yet — create the first one below.</p>
      ) : (
        rounds.map((r) => (
          <div className="panel" key={r.id}>
            <p className="subtitle">
              // round #{r.round_number} · {TIMING_PROFILE_LABEL[r.timing_profile]} ·{" "}
              <strong>{PHASE_LABEL[r.phase]}</strong> ·{" "}
              <Link href={`/events/${chapterSlug}/${eventSlug}/rounds/${r.round_number}`}>
                live view
              </Link>
            </p>

            {!terminal(r) && (
              <>
                <div className="actions">
                  <input
                    type="datetime-local"
                    value={when[r.id] ?? ""}
                    onChange={(e) => setWhen((w) => ({ ...w, [r.id]: e.target.value }))}
                  />
                  <button type="button" className="btn" onClick={() => act(r, "schedule")}>
                    [ schedule ]
                  </button>
                  <button type="button" className="btn" onClick={() => act(r, "start")}>
                    [ start now ]
                  </button>
                </div>
                <div className="row-actions">
                  <button type="button" className="linkbtn" onClick={() => act(r, "complete")}>
                    complete
                  </button>
                  <button type="button" className="linkbtn-danger" onClick={() => act(r, "cancel")}>
                    cancel
                  </button>
                </div>
              </>
            )}
            {r.build_end_at && (
              <p className="note">
                // freeze at {new Date(r.build_end_at).toLocaleString("en-US", { timeZone: "UTC" })} UTC
              </p>
            )}
          </div>
        ))
      )}

      <h2 className="h2"># new round</h2>
      <form className="form" onSubmit={create}>
        <label className="field">
          <span>timing profile</span>
          <select
            value={form.profile}
            onChange={(e) => setForm((f) => ({ ...f, profile: e.target.value }))}
          >
            {PROFILES.map((p) => (
              <option key={p} value={p}>
                {TIMING_PROFILE_LABEL[p]}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>expected players (optional)</span>
          <input
            type="number"
            min={0}
            value={form.players}
            onChange={(e) => setForm((f) => ({ ...f, players: e.target.value }))}
          />
        </label>
        <label className="field">
          <span>prompt (revealed when build begins)</span>
          <textarea
            rows={3}
            value={form.prompt}
            onChange={(e) => setForm((f) => ({ ...f, prompt: e.target.value }))}
          />
        </label>
        <button type="submit" className="btn">
          [ create round ]
        </button>
      </form>
    </section>
  );
}
