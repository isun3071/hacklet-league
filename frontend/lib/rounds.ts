// Round mechanics: types + display helpers (Stage 3). CLIENT-SAFE — no server-only imports,
// so both server and client components can import the labels/helpers below. The SSR fetchers
// (which need next/headers) live in lib/api.ts; the browser polls /api/... via lib/http.ts.
// Mirrors backend rounds/serializers.py + rankings.

// ---- types -----------------------------------------------------------------

export type TimingProfile = "tier_a" | "tier_c_mvr" | "tier_c_extended";

// status = coarse lifecycle; phase = live, clock-derived value (the authoritative one).
export type RoundStatus =
  | "scheduled"
  | "completed"
  | "cancelled"
  | "opening"
  | "build"
  | "evaluation"
  | "pitching"
  | "deliberation"
  | "judging"
  | "awards";

export type RoundPhase =
  | "scheduled"
  | "opening"
  | "build"
  | "evaluation"
  | "pitching"
  | "deliberation"
  | "judging"
  | "awards"
  | "completed"
  | "cancelled";

export type RoundEventRef = {
  id: string;
  slug: string;
  name: string;
  chapter_slug: string;
};

export type Round = {
  id: string;
  event: RoundEventRef;
  round_number: number;
  timing_profile: TimingProfile;
  status: RoundStatus;
  phase: RoundPhase;
  server_time: string; // ISO; lets the client correct for clock skew
  opening_at: string | null;
  build_start_at: string | null;
  build_end_at: string | null;
  phase_schedule: Record<string, string>;
  player_count: number;
  checked_in_count: number;
  prompt_revealed: string; // "" until the prompt is visible for the current phase
  created_at: string;
};

export type SubmissionStatus =
  | "in_progress"
  | "submitted"
  | "submitted_deployed"
  | "submitted_failed"
  | "dnf";

export type Submission = {
  id: string;
  round: string;
  player_email: string;
  player_display: string;
  status: SubmissionStatus;
  deployed_url: string;
  readme_content: string;
  attack_surface_coverage: string;
  has_archive: boolean;
  archive_filename: string;
  submitted_at: string | null;
  created_at: string;
};

export type ScoreType =
  | "pitch_quality"
  | "cross_examination"
  | "creative_coherence"
  | "ux_quality"
  | "technical_execution"
  | "documentation";

export type Score = {
  id: string;
  submission: string;
  judge_participant: string;
  judge_email: string;
  score_type: ScoreType;
  value: string;
  comments: string;
  submitted_at: string;
};

export type Standing = {
  submission_id: string;
  player_id: string;
  player_display: string;
  engineering_score: number;
  communication_score: number;
  dimension_averages: Partial<Record<ScoreType, number>>;
  engineering_rank: number;
  communication_rank: number;
  rank_sum: number;
  overall_rank: number;
};

export type RoundResults = {
  round_id: string;
  revealed: boolean;
  standings: Standing[];
  awards: {
    most_resilient: string[];
    best_communicator: string[];
    best_overall: string[];
  };
};

export type Ranking = {
  rank: number;
  user_id: string;
  player_display: string;
  scope: "global" | "chapter" | "regional";
  scope_reference_id: string | null;
  period: string;
  season_year: number | null;
  rank_points: string;
  events_competed: number;
  last_event_at: string | null;
  updated_at: string;
};

// ---- display labels --------------------------------------------------------

export const TIMING_PROFILE_LABEL: Record<TimingProfile, string> = {
  tier_a: "Tier A (135 min)",
  tier_c_mvr: "Tier C · MVR (60 min)",
  tier_c_extended: "Tier C · Extended",
};

export const PHASE_LABEL: Record<RoundPhase, string> = {
  scheduled: "Scheduled",
  opening: "Opening",
  build: "Build",
  evaluation: "Evaluation",
  pitching: "Pitching",
  deliberation: "Deliberation",
  judging: "Judging",
  awards: "Awards",
  completed: "Completed",
  cancelled: "Cancelled",
};

// Short human cue for what each phase means to a competitor.
export const PHASE_BLURB: Record<RoundPhase, string> = {
  scheduled: "not started yet — check in and wait for opening.",
  opening: "round is opening; the prompt drops when build begins.",
  build: "build window is live — code, then upload before freeze.",
  evaluation: "code freeze — submissions are locked and being evaluated.",
  pitching: "players are pitching their work to the judges.",
  deliberation: "judges are deliberating.",
  judging: "judges are scoring.",
  awards: "results are in.",
  completed: "this round is complete.",
  cancelled: "this round was cancelled.",
};

export const SCORE_DIMENSIONS: { key: ScoreType; label: string; axis: "eng" | "comm" }[] = [
  { key: "technical_execution", label: "Technical execution", axis: "eng" },
  { key: "creative_coherence", label: "Creative coherence", axis: "eng" },
  { key: "ux_quality", label: "UX quality", axis: "eng" },
  { key: "documentation", label: "Documentation", axis: "eng" },
  { key: "pitch_quality", label: "Pitch quality", axis: "comm" },
  { key: "cross_examination", label: "Cross-examination", axis: "comm" },
];

export const SCORE_LABEL: Record<ScoreType, string> = Object.fromEntries(
  SCORE_DIMENSIONS.map((d) => [d.key, d.label]),
) as Record<ScoreType, string>;

/** Phases where a player may still upload (build window, before freeze). */
export function canSubmit(phase: RoundPhase): boolean {
  return phase === "build";
}

/** Phases where check-in is still open. */
export function canCheckIn(phase: RoundPhase): boolean {
  return phase === "scheduled" || phase === "opening" || phase === "build";
}
