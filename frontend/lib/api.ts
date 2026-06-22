// Server-side data access for the Django backend.
// SSR fetches go over the internal docker network (backend:8000); the browser
// hits /api/... same-origin through Caddy (used in later client-side features).

import { cookies } from "next/headers";
import type { Ranking, Round } from "@/lib/rounds";

const API_BASE = process.env.INTERNAL_API_URL ?? "http://backend:8000";

// Forward the incoming request's cookies so the backend authenticates the user.
// Without this, SSR fetches are anonymous and a creator can't see their own
// pending (unverified) chapter — the backend only returns it to its owner.
async function ssrHeaders(): Promise<Record<string, string>> {
  const all = (await cookies()).getAll();
  if (!all.length) return {};
  return { cookie: all.map((c) => `${c.name}=${c.value}`).join("; ") };
}

export type Chapter = {
  id: string;
  slug: string;
  name: string;
  description: string;
  location_text: string;
  tier: "A" | "B" | "C";
  mode: string;
  verification_status: string;
  institutional_affiliation: string;
  website_url: string;
  contact_email: string; // owner-only; blank for non-owners
  created_at: string;
};

// Command-center dashboard aggregates per managed chapter (GET /api/chapters/stats/).
export type ChapterStat = {
  chapter_id: string;
  slug: string;
  name: string;
  tier: "A" | "B" | "C";
  verification_status: string;
  events_total: number;
  events_completed: number;
  members_total: number;
  organizers: number;
  corps_judges: number;
  players: number;
  judges: number;
  audience: number;
  participants_total: number;
  rounds_total: number;
  rounds_completed: number;
  ranked_players: number;
};

export async function getChapters(): Promise<Chapter[]> {
  const res = await fetch(`${API_BASE}/api/chapters/`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (!res.ok) throw new Error(`GET /api/chapters/ -> ${res.status}`);
  return res.json();
}

export async function getChapter(slug: string): Promise<Chapter | null> {
  const res = await fetch(`${API_BASE}/api/chapters/${slug}/`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`GET /api/chapters/${slug}/ -> ${res.status}`);
  return res.json();
}

// ---- events ----------------------------------------------------------------
// Named LeagueEvent (not Event) to avoid shadowing the DOM Event type in client code.

export type EventTier = "chapter" | "regional" | "championship";
export type EventFormat = "vibe" | "unslop";
export type EventTimer = "xp" | "sprint" | "scrum" | "agile" | "waterfall";
export type AccessMode = "invite_only" | "application";
export type EventStatus =
  | "scheduled"
  | "registration_open"
  | "registration_closed"
  | "in_progress"
  | "completed"
  | "cancelled";
export type PlayerTierRestriction = "collegiate" | "under_25" | "open" | "any";

export type EventChapterRef = {
  id: string;
  slug: string;
  name: string;
  tier: "A" | "B" | "C";
};

export type LeagueEvent = {
  id: string;
  chapter: EventChapterRef;
  slug: string;
  name: string;
  description: string;
  event_tier: EventTier;
  format: EventFormat;
  timer: EventTimer;
  access_mode: AccessMode;
  status: EventStatus;
  scheduled_start: string;
  scheduled_end: string;
  actual_start: string | null;
  actual_end: string | null;
  player_tier_restriction: PlayerTierRestriction;
  created_at: string;
};

export type ParticipantRole = "player" | "judge" | "audience";
export type JudgeSpecialization = "tester" | "ux_designer" | "general" | "";
export type ParticipantSource = "invited" | "applied" | "corps";
export type ParticipantStatus =
  | "pending"
  | "registered"
  | "declined"
  | "rejected"
  | "withdrawn";

export type Participant = {
  id: string;
  event: { id: string; slug: string; name: string; chapter_slug: string };
  role: ParticipantRole;
  judge_specialization: JudgeSpecialization;
  source: ParticipantSource;
  status: ParticipantStatus;
  display_name: string;
  email: string; // managers + self only; "" otherwise
  created_at: string;
  responded_at: string | null;
};

export async function getEvents(chapterSlug?: string): Promise<LeagueEvent[]> {
  const qs = chapterSlug ? `?chapter=${encodeURIComponent(chapterSlug)}` : "";
  const res = await fetch(`${API_BASE}/api/events/${qs}`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (!res.ok) throw new Error(`GET /api/events/ -> ${res.status}`);
  return res.json();
}

export async function getEvent(
  chapterSlug: string,
  eventSlug: string,
): Promise<LeagueEvent | null> {
  // Event slugs are unique only per chapter, so resolve via the filtered list.
  const res = await fetch(
    `${API_BASE}/api/events/?chapter=${encodeURIComponent(chapterSlug)}&slug=${encodeURIComponent(eventSlug)}`,
    { cache: "no-store", headers: await ssrHeaders() },
  );
  if (!res.ok) throw new Error(`GET /api/events/ -> ${res.status}`);
  const rows: LeagueEvent[] = await res.json();
  return rows[0] ?? null;
}

export type ChapterRole = "owner" | "organizer" | "judge";

export type ChapterStaffRow = {
  id: string;
  chapter_slug: string;
  user_id: string;
  email: string;
  display_name: string;
  roles: ChapterRole[];
  status: "pending" | "active" | "suspended";
  joined_at: string;
  notes: string;
};

export async function getEventParticipants(eventId: string): Promise<Participant[]> {
  const res = await fetch(`${API_BASE}/api/events/${eventId}/participants/`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (!res.ok) throw new Error(`GET /api/events/${eventId}/participants/ -> ${res.status}`);
  return res.json();
}

// ---- rounds + rankings (Stage 3) -------------------------------------------
// Types + display helpers live in lib/rounds.ts (client-safe); these fetchers are server-only.

export async function getRounds(eventId: string): Promise<Round[]> {
  const res = await fetch(`${API_BASE}/api/rounds/?event=${encodeURIComponent(eventId)}`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (!res.ok) throw new Error(`GET /api/rounds/ -> ${res.status}`);
  return res.json();
}

export async function getRound(roundId: string): Promise<Round | null> {
  const res = await fetch(`${API_BASE}/api/rounds/${roundId}/`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`GET /api/rounds/${roundId}/ -> ${res.status}`);
  return res.json();
}

/** Resolve a round by its human-facing number within an event. */
export async function getRoundByNumber(
  eventId: string,
  roundNumber: number,
): Promise<Round | null> {
  const rounds = await getRounds(eventId);
  return rounds.find((r) => r.round_number === roundNumber) ?? null;
}

export async function getRankings(
  scope: "global" | "chapter",
  chapterId?: string,
): Promise<Ranking[]> {
  const qs =
    scope === "chapter" && chapterId
      ? `?scope=chapter&chapter=${encodeURIComponent(chapterId)}`
      : "?scope=global";
  const res = await fetch(`${API_BASE}/api/rankings/${qs}`, {
    cache: "no-store",
    headers: await ssrHeaders(),
  });
  if (!res.ok) return []; // unverified-chapter / no-board -> empty, not a hard error
  return res.json();
}
