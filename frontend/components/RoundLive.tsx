"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { csrfToken, request } from "@/lib/http";
import { getSession } from "@/lib/auth";
import { JudgeConsole } from "@/components/JudgeConsole";
import { RoundResults } from "@/components/RoundResults";
import {
  PHASE_BLURB,
  PHASE_LABEL,
  TIMING_PROFILE_LABEL,
  canCheckIn,
  canSubmit,
  type Round,
  type Submission,
} from "@/lib/rounds";
import type { Participant, ParticipantRole } from "@/lib/api";

const BOUNDARY_LABEL: Record<string, string> = {
  evaluation_end: "evaluation ends",
  pitch_end: "pitching ends",
  pitch_write_end: "pitch window ends",
  judging_end: "judging ends",
  deliberation_end: "deliberation ends",
  awards_end: "awards end",
  zamboni_end: "round closes",
};

type Boundary = { label: string; targetMs: number };

function nextBoundary(round: Round, nowMs: number): Boundary | null {
  const c: { label: string; iso: string | null }[] = [
    { label: "round opens", iso: round.opening_at },
    { label: "prompt drops · build begins", iso: round.build_start_at },
    { label: "CODE FREEZE", iso: round.build_end_at },
    ...Object.entries(round.phase_schedule ?? {}).map(([k, iso]) => ({
      label: BOUNDARY_LABEL[k] ?? k,
      iso,
    })),
  ];
  const future = c
    .map((x) => ({ label: x.label, t: x.iso ? Date.parse(x.iso) : NaN }))
    .filter((x) => !Number.isNaN(x.t) && x.t > nowMs)
    .sort((a, b) => a.t - b.t);
  return future[0] ? { label: future[0].label, targetMs: future[0].t } : null;
}

function fmtCountdown(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
}

export function RoundLive({ initialRound }: { initialRound: Round }) {
  const roundId = initialRound.id;
  const eventId = initialRound.event.id;
  const [round, setRound] = useState<Round>(initialRound);
  const [nowMs, setNowMs] = useState<number>(() => Date.parse(initialRound.server_time) || Date.now());
  const [role, setRole] = useState<ParticipantRole | null>(null);
  const [resultsKey, setResultsKey] = useState(0);
  const skew = useRef<number>(Date.parse(initialRound.server_time) - Date.now());
  const lastPhase = useRef<string>(initialRound.phase);

  const poll = useCallback(async () => {
    const res = await request<Round>(`/api/rounds/${roundId}/`, "GET");
    if (res.ok && res.data) {
      skew.current = Date.parse(res.data.server_time) - Date.now();
      setRound(res.data);
      if (res.data.phase !== lastPhase.current) {
        lastPhase.current = res.data.phase;
        setResultsKey((k) => k + 1); // phase changed -> refresh results
      }
    }
  }, [roundId]);

  // Role detection (once): match my own email in the participant list.
  useEffect(() => {
    (async () => {
      if ((await getSession()) !== 200) return;
      const [me, parts] = await Promise.all([
        request<{ email: string }>("/api/me/", "GET"),
        request<Participant[]>(`/api/events/${eventId}/participants/`, "GET"),
      ]);
      const email = me.data?.email;
      const mine = parts.data?.find(
        (p) => p.email && p.email === email && p.status === "registered",
      );
      if (mine) setRole(mine.role);
    })();
  }, [eventId]);

  // Poll the round every 5s.
  useEffect(() => {
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [poll]);

  // Tick the local clock every second; re-poll immediately when a boundary passes.
  useEffect(() => {
    const id = setInterval(() => {
      const corrected = Date.now() + skew.current;
      setNowMs(corrected);
      const b = nextBoundary(round, corrected);
      if (!b) return;
      if (corrected >= b.targetMs) poll();
    }, 1000);
    return () => clearInterval(id);
  }, [round, poll]);

  const phase = round.phase;
  const boundary = nextBoundary(round, nowMs);
  const isFreeze = boundary?.label === "CODE FREEZE";

  return (
    <div className="block">
      {/* phase + countdown */}
      <div className="status-banner">
        <strong>{PHASE_LABEL[phase]}</strong> — {PHASE_BLURB[phase]}
      </div>

      {boundary && phase !== "completed" && phase !== "cancelled" && (
        <p className={isFreeze ? "readout accent-strong" : "readout"}>
          {isFreeze ? "⏱ freeze in " : `next · ${boundary.label} in `}
          <span className="countdown">{fmtCountdown(boundary.targetMs - nowMs)}</span>
        </p>
      )}

      <dl className="kv">
        <div>
          <dt>format</dt>
          <dd>{TIMING_PROFILE_LABEL[round.timing_profile]}</dd>
        </div>
        <div>
          <dt>round</dt>
          <dd>#{round.round_number}</dd>
        </div>
        <div>
          <dt>checked in</dt>
          <dd>
            {round.checked_in_count}
            {round.player_count ? ` / ${round.player_count}` : ""}
          </dd>
        </div>
      </dl>

      {round.prompt_revealed && (
        <div className="panel">
          <p className="subtitle">// prompt</p>
          <pre className="codeblock">{round.prompt_revealed}</pre>
        </div>
      )}

      {role === "player" && <PlayerPanel round={round} onChanged={poll} />}
      {role === "judge" && <JudgeConsole roundId={roundId} />}

      {/* Self-gates server-side: staff get a preview anytime, the public only after reveal. */}
      <RoundResults roundId={roundId} refreshKey={resultsKey} />
    </div>
  );
}

const COVERAGE_OPTIONS = [
  { value: "", label: "— not specified —" },
  { value: "narrow", label: "Narrow" },
  { value: "moderate", label: "Moderate" },
  { value: "broad", label: "Broad" },
];

function PlayerPanel({ round, onChanged }: { round: Round; onChanged: () => void }) {
  const [mine, setMine] = useState<Submission | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string[]>([]);
  const [ok, setOk] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [readme, setReadme] = useState("");
  const [deployed, setDeployed] = useState("");
  const [coverage, setCoverage] = useState("");

  const loadMine = useCallback(async () => {
    const res = await request<Submission[]>("/api/submissions/mine/", "GET");
    setMine(res.data?.find((s) => s.round === round.id) ?? null);
    setLoaded(true);
  }, [round.id]);

  useEffect(() => {
    loadMine();
  }, [loadMine]);

  async function checkIn() {
    setBusy(true);
    setErr([]);
    const res = await request(`/api/rounds/${round.id}/check-in/`, "POST", {});
    setBusy(false);
    if (res.ok) {
      await loadMine();
      onChanged();
    } else setErr(res.errors.length ? res.errors : ["Could not check in."]);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setErr(["Choose a .zip archive to submit."]);
      return;
    }
    setBusy(true);
    setErr([]);
    setOk("");
    const fd = new FormData();
    fd.append("archive", file);
    fd.append("readme_content", readme);
    if (deployed) fd.append("deployed_url", deployed);
    if (coverage) fd.append("attack_surface_coverage", coverage);
    const res = await fetch(`/api/rounds/${round.id}/submit/`, {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRFToken": await csrfToken() },
      body: fd,
    });
    setBusy(false);
    if (res.ok) {
      setOk("Submitted — you can re-upload until freeze.");
      await loadMine();
      onChanged();
    } else {
      let detail = "Upload failed.";
      try {
        const data = await res.json();
        detail = data.detail ?? Object.values(data).flat().join(" ") ?? detail;
      } catch {
        /* non-JSON */
      }
      setErr([detail]);
    }
  }

  if (!loaded) return null;

  const checkedIn = mine !== null;
  const submitted = mine?.status?.startsWith("submitted");

  return (
    <section className="block">
      <h2 className="h2"># your submission</h2>

      {!checkedIn ? (
        canCheckIn(round.phase) ? (
          <div className="panel">
            <p className="subtitle">// reserve your slot for this round.</p>
            <button type="button" className="btn" disabled={busy} onClick={checkIn}>
              [ {busy ? "checking in…" : "check in"} ]
            </button>
          </div>
        ) : (
          <p className="note">// check-in is closed for this round.</p>
        )
      ) : (
        <p className="note">
          // checked in ✓{submitted ? ` · submitted (${mine?.archive_filename || "archive"})` : ""}
        </p>
      )}

      {checkedIn && canSubmit(round.phase) && (
        <form className="form" onSubmit={submit}>
          <p className="subtitle">// upload your work as a single .zip — re-upload overwrites until freeze.</p>
          <label className="field">
            <span>archive (.zip) *</span>
            <input
              type="file"
              accept=".zip,application/zip"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <label className="field">
            <span>README / notes</span>
            <textarea value={readme} onChange={(e) => setReadme(e.target.value)} rows={4} />
          </label>
          <label className="field">
            <span>deployed URL (optional)</span>
            <input
              type="url"
              value={deployed}
              onChange={(e) => setDeployed(e.target.value)}
              placeholder="https://…"
            />
          </label>
          <label className="field">
            <span>attack-surface coverage (optional)</span>
            <select value={coverage} onChange={(e) => setCoverage(e.target.value)}>
              {COVERAGE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="btn" disabled={busy}>
            [ {busy ? "uploading…" : submitted ? "re-upload" : "submit"} ]
          </button>
        </form>
      )}

      {checkedIn && !canSubmit(round.phase) && !submitted && (
        <p className="note">// the build window isn&apos;t open for uploads right now.</p>
      )}

      {ok && <p className="ok-msg">{ok}</p>}
      {err.map((m, i) => (
        <p className="form-error" key={i}>
          {m}
        </p>
      ))}
    </section>
  );
}
