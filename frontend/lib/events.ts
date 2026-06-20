// Display labels + helpers for event enums. Plain constants — safe to import from both
// server and client components.

import type {
  AccessMode,
  EventFormat,
  EventStatus,
  EventTier,
  EventTimer,
  JudgeSpecialization,
  LeagueEvent,
  ParticipantRole,
  ParticipantSource,
  ParticipantStatus,
  PlayerTierRestriction,
} from "@/lib/api";

export const FORMAT_LABEL: Record<EventFormat, string> = {
  vibe: "Vibe",
  unslop: "Unslop",
};

export const TIMER_LABEL: Record<EventTimer, string> = {
  xp: "XP",
  sprint: "Sprint",
  scrum: "Scrum",
  agile: "Agile",
  waterfall: "Waterfall",
};

export const TIMER_MINUTES: Record<EventTimer, string> = {
  xp: "12 min",
  sprint: "24 min",
  scrum: "36 min",
  agile: "48 min",
  waterfall: "72–96 min",
};

// The three distinct "tier" axes the UI must keep apart (see DATA_MODEL.md):
//   eventTier  — the event's SCOPE (chapter / regional / championship)
//   chapter.tier — the HOST chapter's operational tier (A/B/C)
//   playerTier — who may COMPETE (eligibility)
export const EVENT_TIER_LABEL: Record<EventTier, string> = {
  chapter: "Chapter",
  regional: "Regional",
  championship: "Championship",
};

export const PLAYER_TIER_LABEL: Record<PlayerTierRestriction, string> = {
  collegiate: "Collegiate",
  under_25: "Under 25",
  open: "Open",
  any: "Any",
};

export const ACCESS_LABEL: Record<AccessMode, string> = {
  invite_only: "Invite only",
  application: "Open application",
};

export const STATUS_LABEL: Record<EventStatus, string> = {
  scheduled: "Scheduled",
  registration_open: "Registration open",
  registration_closed: "Registration closed",
  in_progress: "In progress",
  completed: "Completed",
  cancelled: "Cancelled",
};

export const ROLE_LABEL: Record<ParticipantRole, string> = {
  player: "Player",
  judge: "Judge",
  audience: "Audience",
};

export const SOURCE_LABEL: Record<ParticipantSource, string> = {
  invited: "Invited",
  applied: "Applied",
  corps: "Corps",
};

export const PARTICIPANT_STATUS_LABEL: Record<ParticipantStatus, string> = {
  pending: "Pending",
  registered: "Registered",
  declined: "Declined",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

export const SPECIALIZATION_LABEL: Record<JudgeSpecialization, string> = {
  tester: "Tester",
  ux_designer: "UX Designer",
  general: "General",
  "": "—",
};

/** The two-axis variant name, e.g. "Vibe Sprint". */
export function variantName(format: EventFormat, timer: EventTimer): string {
  return `${FORMAT_LABEL[format]} ${TIMER_LABEL[timer]}`;
}

/** Deterministic UTC datetime string (avoids SSR/client locale drift). */
export function fmtDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }) + " UTC";
}

export function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    dateStyle: "medium",
    timeZone: "UTC",
  });
}

/** Path to an event's public page. */
export function eventPath(e: Pick<LeagueEvent, "slug"> & { chapter: { slug: string } }): string {
  return `/events/${e.chapter.slug}/${e.slug}`;
}
