"""Round timing logic — the server's single source of truth for phases.

Given a round's `timing_profile` and its `opening_at` anchor, the server computes every
phase boundary as an ABSOLUTE UTC timestamp. The live phase is then *derived* from the
server clock vs those boundaries — it is never a client-settable value, and the client's
clock/timezone is never consulted. See DATA_MODEL.md / format_spec.md / TIER_*_OPERATIONS.md.
"""
from datetime import timedelta

from django.utils.dateparse import parse_datetime

# Upload grace after build end. The buzzer stops the *build*; this window exists so a slow
# or flaky upload does not cost a player their submission (TIER_C §6, TIER_B §5, PITCH.md).
# Nothing may be edited during it — at Tier A/B the network cut enforces that; at Tier C the
# honour system does, the same as every other Tier C rule.
SUBMISSION_GRACE = timedelta(minutes=3)

# Offsets in minutes from opening_at (T+0). `schedule` entries are (phase_schedule key,
# minutes) for the boundaries after code-freeze; keys match DATA_MODEL's phase_schedule.
PHASE_PROFILES = {
    "tier_a": {
        "build_start": 5,
        "build_end": 29,
        "schedule": [
            ("evaluation_end", 47),
            ("pitch_end", 75),
            ("deliberation_end", 93),
            ("awards_end", 107),
            ("zamboni_end", 135),
        ],
    },
    "tier_c_mvr": {
        "build_start": 5,
        "build_end": 29,
        "schedule": [
            ("pitch_write_end", 47),
            ("judging_end", 52),
            ("awards_end", 60),
        ],
    },
    "tier_b": {
        # Tier A's phase shape minus the Zamboni: BYOD has no workstations to reset. Only the
        # build clock (24 min) and the per-player pitch slot are hard; the surrounding phases
        # are planning estimates, and the pitch window scales with field size (8 players ->
        # 28 min, 12 -> 42). Formerly `tier_c_extended`.
        "build_start": 5,
        "build_end": 29,
        "schedule": [
            ("evaluation_end", 47),
            ("pitch_end", 75),
            ("deliberation_end", 93),
            ("awards_end", 107),
        ],
    },
}

# Legacy key: rounds created before the 2026-07-31 tier restructure stored `tier_c_extended`
# for what is now `tier_b`. Same profile, so old rows keep resolving. Not selectable.
PHASE_PROFILES["tier_c_extended"] = PHASE_PROFILES["tier_b"]

# Which phase is active in the interval *ending* at each phase_schedule boundary.
KEY_PHASE = {
    "evaluation_end": "evaluation",
    "pitch_end": "pitching",
    "pitch_write_end": "pitching",
    "judging_end": "judging",
    "deliberation_end": "deliberation",
    "awards_end": "awards",
    "zamboni_end": "completed",  # the Zamboni reset is post-round; players see "completed"
}

PROMPT_VISIBLE_PHASES = {
    "build", "evaluation", "pitching", "deliberation", "judging", "awards", "completed",
}


def submission_deadline(rnd):
    """The last instant an upload is accepted: build end plus the grace window. Returns None
    for an unscheduled round. This is the server's only submission clock — `build_end_at`
    ends the build, this ends the upload."""
    if not rnd.build_end_at:
        return None
    return rnd.build_end_at + SUBMISSION_GRACE


def build_phase_schedule(timing_profile, opening_at):
    """Return (build_start_at, build_end_at, phase_schedule) as absolute UTC, anchored to
    opening_at. phase_schedule maps each key to an ISO-8601 string."""
    spec = PHASE_PROFILES[timing_profile]
    build_start_at = opening_at + timedelta(minutes=spec["build_start"])
    build_end_at = opening_at + timedelta(minutes=spec["build_end"])
    phase_schedule = {
        key: (opening_at + timedelta(minutes=minutes)).isoformat()
        for key, minutes in spec["schedule"]
    }
    return build_start_at, build_end_at, phase_schedule


def current_phase(rnd, now):
    """The live phase of `rnd` at server time `now` — derived purely from stored absolute
    boundaries. Terminal stored statuses (cancelled/completed) win."""
    if rnd.status == rnd.Status.CANCELLED:
        return "cancelled"
    if rnd.status == rnd.Status.COMPLETED:
        return "completed"
    if not rnd.opening_at or now < rnd.opening_at:
        return "scheduled"
    if rnd.build_start_at and now < rnd.build_start_at:
        return "opening"
    if rnd.build_end_at and now < rnd.build_end_at:
        return "build"
    entries = []
    for key, iso in (rnd.phase_schedule or {}).items():
        ts = parse_datetime(iso) if isinstance(iso, str) else iso
        if ts:
            entries.append((ts, key))
    entries.sort()
    for ts, key in entries:
        if now < ts:
            return KEY_PHASE.get(key, "evaluation")
    return "completed"
