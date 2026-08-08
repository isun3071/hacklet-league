import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Round(models.Model):
    """One round within an event — the unit that actually runs (timer + phases). Multiple
    rounds per event.

    Phase boundaries are stored as ABSOLUTE UTC timestamps (build_end_at + phase_schedule)
    so the server is the sole time authority: clients only render a countdown from them, and
    the server enforces the code-freeze (now <= build_end_at) against its own clock — client
    time is never trusted. The status enum is a superset; the active subset depends on
    timing_profile. Transitions are server-authoritative. See DATA_MODEL.md / format_spec.md.
    """

    class TimingProfile(models.TextChoices):
        # The ladder grades on JUDGING RIGOR, not on who hosts the AI:
        #   tier_c_mvr — PITCH.md, LLM-judged, one hour, scales to 100+
        #   tier_b     — live pitch + cross-examination with human judges, BYOD substrate
        #   tier_a     — the above plus controlled workstations and enforced substrate parity
        # tier_b is the profile formerly called tier_c_extended (same phase shape: Tier A's
        # minus the Zamboni, since BYOD has no workstations to reset). The legacy key still
        # resolves in services.PHASE_PROFILES so any round already carrying it renders.
        TIER_A = "tier_a", "Tier A"
        TIER_B = "tier_b", "Tier B (live judging, BYOD)"
        TIER_C_MVR = "tier_c_mvr", "Tier C MVR"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        OPENING = "opening", "Opening"
        BUILD = "build", "Build"
        EVALUATION = "evaluation", "Evaluation"
        PITCHING = "pitching", "Pitching"
        DELIBERATION = "deliberation", "Deliberation"
        JUDGING = "judging", "Judging"
        AWARDS = "awards", "Awards"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="rounds")
    round_number = models.PositiveIntegerField(default=1)
    timing_profile = models.CharField(
        max_length=20, choices=TimingProfile.choices, default=TimingProfile.TIER_C_MVR
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    opening_at = models.DateTimeField(null=True, blank=True)
    build_start_at = models.DateTimeField(null=True, blank=True)
    # The code-freeze instant (absolute UTC). Server-authoritative; submissions after this
    # are rejected by the server's own clock regardless of what the client believes.
    build_end_at = models.DateTimeField(null=True, blank=True)
    # Absolute UTC timestamps for the remaining phase boundaries; keys depend on
    # timing_profile (e.g. tier_c_mvr -> pitch_write_end/judging_end/awards_end).
    phase_schedule = models.JSONField(default=dict, blank=True)
    player_count = models.PositiveIntegerField(default=0)
    prompt_revealed = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "rounds_round"
        ordering = ("event", "round_number")
        constraints = [
            models.UniqueConstraint(
                fields=["event", "round_number"], name="unique_event_round_number"
            ),
        ]

    def __str__(self):
        return f"{self.event} — round {self.round_number}"


def submission_upload_path(instance, filename):
    """Private, per-event/round/player path. The on-disk name is forced to submission.zip
    (the player's original name is kept in archive_filename) so untrusted filenames never
    touch the filesystem. Mirrors the Stage 5/7 submissions/$EVENT/$ROUND/$PLAYER/ layout."""
    return f"submissions/{instance.round.event_id}/{instance.round_id}/{instance.player_id}/submission.zip"


class Submission(models.Model):
    """A player's submission for a round: a PUBLIC git repository, cloned and pinned to a commit
    SHA at submit time (fetch-on-submit) and frozen when the upload window closes. The platform
    only clones the bytes onto league storage; it never builds or runs submission code (that is the
    fuzzer's sandbox). The fuzzer grades the pinned commit and never pulls past it, so changes
    pushed after the buzzer are not reflected. The legacy zip path (archive/archive_filename) is
    retired but kept blank/dormant. See DATA_MODEL.md."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        SUBMITTED = "submitted", "Submitted"
        SUBMITTED_DEPLOYED = "submitted_deployed", "Submitted (deployed)"
        SUBMITTED_FAILED = "submitted_failed", "Submitted (deploy failed)"
        DNF = "dnf", "Did not finish"

    class AttackSurfaceCoverage(models.TextChoices):
        NARROW = "narrow", "Narrow"
        MODERATE = "moderate", "Moderate"
        BROAD = "broad", "Broad"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="submissions")
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    # Uploaded zip, stored on private storage (MEDIA_ROOT); served only via an auth-gated
    # download endpoint, never publicly. archive_filename keeps the player's original name.
    # max_length must fit the per-event/round/player path (three UUIDs deep ~ 140 chars);
    # the FileField default of 100 is too short and storage raises SuspiciousFileOperation.
    archive = models.FileField(upload_to=submission_upload_path, blank=True, max_length=255)
    archive_filename = models.CharField(max_length=255, blank=True)
    # The submission is a PUBLIC git repo, cloned and SHA-pinned at submit time (fetch-on-submit).
    # repo_url is the player-supplied HTTPS clone URL; commit_sha is the default-branch HEAD resolved
    # and fetched onto league storage when the player submits, frozen when the upload window closes.
    # The fuzzer builds this exact commit and never pulls past it. (archive/archive_filename above are
    # the retired zip path, kept blank/dormant to avoid a destructive migration.)
    repo_url = models.URLField(blank=True)
    commit_sha = models.CharField(max_length=64, blank=True)  # 40-char SHA-1 today; room for SHA-256
    deployed_url = models.URLField(blank=True)
    readme_content = models.TextField(blank=True)
    token_budget_used = models.PositiveIntegerField(default=0)
    fuzz_budget_used = models.PositiveIntegerField(default=0)
    attack_surface_coverage = models.CharField(
        max_length=20, choices=AttackSurfaceCoverage.choices, blank=True
    )
    # The authoritative objective axis: the fuzz runner's damped slop total ([0, +inf), lower is
    # better). NULL until the submission is graded (import_fuzz_results). This is the runner's
    # own aggregate, NOT a naive sum of FuzzResult penalties — the runner already applied its
    # variant-group / diminishing / per-bundle dampers, so ranking reads this field, not a re-sum.
    slop_score = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "rounds_submission"
        ordering = ("round", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["round", "player"], name="unique_round_player_submission"
            ),
        ]

    def __str__(self):
        return f"{self.player} — {self.round}"


class Score(models.Model):
    """A single judge's score on one dimension of a submission. Judges are EventParticipants
    with role=judge (judge_participant). In Stage 3 every score is entered by hand — the fuzz
    runner that produces the automated Slop Score arrives in Stage 5. See format_spec.md §4."""

    class ScoreType(models.TextChoices):
        PITCH_QUALITY = "pitch_quality", "Pitch quality"
        CROSS_EXAMINATION = "cross_examination", "Cross-examination"
        CREATIVE_COHERENCE = "creative_coherence", "Creative coherence"
        UX_QUALITY = "ux_quality", "UX quality"
        TECHNICAL_EXECUTION = "technical_execution", "Technical execution"
        DOCUMENTATION = "documentation", "Documentation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="scores")
    judge_participant = models.ForeignKey(
        "events.EventParticipant", on_delete=models.CASCADE, related_name="scores_given"
    )
    score_type = models.CharField(max_length=30, choices=ScoreType.choices)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "rounds_score"
        ordering = ("submission", "score_type")
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "judge_participant", "score_type"],
                name="unique_submission_judge_scoretype",
            ),
        ]

    def __str__(self):
        return f"{self.score_type} {self.value} — {self.submission}"


class FuzzResult(models.Model):
    """One fuzz finding against a submission, imported from the runner's grade record
    (`manage.py import_fuzz_results`). Deduction-only per format_spec §4.2: a fired probe carries
    a non-negative `penalty_contributed`; `clean` / `not_applicable` carry 0.

    The authoritative ranked number is `Submission.slop_score` (the runner's damped total). These
    rows are the itemized findings — for the player's slop report and for the tester judge's
    contest mechanic. `probe_id` is the runner catalog's string id (e.g. "sec-sqli-001") rather
    than an FK to a FuzzTest table, which is not built at the manual-bridge stage; the FuzzTest
    catalog becomes a platform table in the full Stage 5 pipeline (DATA_MODEL.md FuzzResult).
    """

    class Outcome(models.TextChoices):
        SLOP_DETECTED = "slop_detected", "Slop detected"
        CLEAN = "clean", "Clean"
        NOT_APPLICABLE = "not_applicable", "Not applicable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="fuzz_results"
    )
    probe_id = models.CharField(max_length=100)
    bundle = models.CharField(max_length=20, blank=True)  # security / qa / performance
    category = models.CharField(max_length=80, blank=True)
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    penalty_contributed = models.PositiveIntegerField(default=0)
    evidence = models.JSONField(default=dict, blank=True)
    # Contest (format_spec §4.2): the tester judge disputes a finding at deliberation. Records
    # only — changes no score, and never amends this round. Reviewed between events into catalog
    # changes going forward.
    contested_by = models.ForeignKey(
        "events.EventParticipant", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="contested_findings",
    )
    contested_reason = models.TextField(blank=True)
    contested_at = models.DateTimeField(null=True, blank=True)
    ran_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "rounds_fuzzresult"
        ordering = ("submission", "bundle", "probe_id")
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "probe_id"], name="unique_submission_probe"
            ),
        ]

    def __str__(self):
        return f"{self.probe_id} {self.outcome} (+{self.penalty_contributed}) — {self.submission}"
