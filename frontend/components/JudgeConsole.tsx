"use client";

import { useCallback, useEffect, useState } from "react";
import { request } from "@/lib/http";
import { SCORE_DIMENSIONS, type Score, type Submission } from "@/lib/rounds";

type Draft = Record<string, string>; // key: `${submissionId}:${scoreType}`

const key = (sub: string, dim: string) => `${sub}:${dim}`;

/** A judge's scoring surface for one round: every submission, every dimension, prefilled with
 * the judge's own prior scores. Saving a submission posts each changed dimension (the API
 * scores one dimension per call and upserts). */
export function JudgeConsole({ roundId }: { roundId: string }) {
  const [subs, setSubs] = useState<Submission[]>([]);
  const [saved, setSaved] = useState<Draft>({});
  const [draft, setDraft] = useState<Draft>({});
  const [myEmail, setMyEmail] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<Record<string, string>>({});
  const [err, setErr] = useState<Record<string, string>>({});
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    const [meRes, subRes, scoreRes] = await Promise.all([
      request<{ email: string }>("/api/me/", "GET"),
      request<Submission[]>(`/api/submissions/?round=${roundId}`, "GET"),
      request<Score[]>(`/api/scores/?round=${roundId}`, "GET"),
    ]);
    const email = meRes.data?.email ?? "";
    setMyEmail(email);
    setSubs(subRes.data ?? []);
    const mine: Draft = {};
    for (const s of scoreRes.data ?? []) {
      if (s.judge_email === email) mine[key(s.submission, s.score_type)] = String(s.value);
    }
    setSaved(mine);
    setDraft(mine);
    setLoaded(true);
  }, [roundId]);

  useEffect(() => {
    load();
  }, [load]);

  async function saveSubmission(sub: Submission) {
    setBusy(sub.id);
    setErr((e) => ({ ...e, [sub.id]: "" }));
    setMsg((m) => ({ ...m, [sub.id]: "" }));
    const errors: string[] = [];
    const next = { ...saved };
    for (const dim of SCORE_DIMENSIONS) {
      const k = key(sub.id, dim.key);
      const v = (draft[k] ?? "").trim();
      if (v === "" || v === saved[k]) continue;
      const res = await request(`/api/scores/`, "POST", {
        submission: sub.id,
        score_type: dim.key,
        value: v,
      });
      if (res.ok) next[k] = v;
      else errors.push(`${dim.label}: ${res.errors[0] ?? "rejected"}`);
    }
    setSaved(next);
    setBusy(null);
    if (errors.length) setErr((e) => ({ ...e, [sub.id]: errors.join(" · ") }));
    else setMsg((m) => ({ ...m, [sub.id]: "scores saved." }));
  }

  if (!loaded) return <p className="note">// loading scoring console…</p>;

  return (
    <section className="block">
      <h2 className="h2"># judge console</h2>
      <p className="subtitle">
        // scoring as {myEmail || "you"} · 0–100 per dimension · engineering + communication axes
      </p>
      {subs.length === 0 ? (
        <p className="note">// no submissions to score yet.</p>
      ) : (
        subs.map((sub) => (
          <div className="panel" key={sub.id}>
            <p className="subtitle">
              // {sub.player_display || sub.player_email || "player"} ·{" "}
              {sub.status.replace(/_/g, " ")}
              {sub.has_archive && (
                <>
                  {" · "}
                  <a href={`/api/submissions/${sub.id}/download/`}>download zip</a>
                </>
              )}
              {sub.deployed_url && (
                <>
                  {" · "}
                  <a href={sub.deployed_url} target="_blank" rel="noopener noreferrer">
                    deployed
                  </a>
                </>
              )}
            </p>
            {sub.readme_content && (
              <pre className="codeblock">{sub.readme_content}</pre>
            )}
            <div className="score-grid">
              {SCORE_DIMENSIONS.map((dim) => {
                const k = key(sub.id, dim.key);
                return (
                  <label className="field" key={dim.key}>
                    <span>
                      {dim.label} <span className="dim">[{dim.axis}]</span>
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step="0.5"
                      value={draft[k] ?? ""}
                      onChange={(e) =>
                        setDraft((d) => ({ ...d, [k]: e.target.value }))
                      }
                    />
                  </label>
                );
              })}
            </div>
            <button
              type="button"
              className="btn"
              disabled={busy === sub.id}
              onClick={() => saveSubmission(sub)}
            >
              [ {busy === sub.id ? "saving…" : "save scores"} ]
            </button>
            {msg[sub.id] && <p className="ok-msg">{msg[sub.id]}</p>}
            {err[sub.id] && <p className="form-error">{err[sub.id]}</p>}
          </div>
        ))
      )}
    </section>
  );
}
