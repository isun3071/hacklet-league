import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Event(models.Model):
    """A bounded competitive gathering operated by a chapter. Stage 2 builds the
    organizational structure only — no rounds run yet. The (format, timer) pair names
    the variant (e.g. vibe + sprint = HackLet Vibe Sprint). See DATA_MODEL.md."""

    class EventTier(models.TextChoices):
        CHAPTER = "chapter", "Chapter"
        REGIONAL = "regional", "Regional"
        CHAMPIONSHIP = "championship", "Championship"

    class Format(models.TextChoices):
        VIBE = "vibe", "Vibe"
        UNSLOP = "unslop", "Unslop"

    class Timer(models.TextChoices):
        XP = "xp", "XP (12 min)"
        SPRINT = "sprint", "Sprint (24 min)"
        SCRUM = "scrum", "Scrum (36 min)"
        AGILE = "agile", "Agile (48 min)"
        WATERFALL = "waterfall", "Waterfall (72-96 min)"

    class AccessMode(models.TextChoices):
        INVITE_ONLY = "invite_only", "Invite only"
        APPLICATION = "application", "Application"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        REGISTRATION_OPEN = "registration_open", "Registration open"
        REGISTRATION_CLOSED = "registration_closed", "Registration closed"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PlayerTierRestriction(models.TextChoices):
        COLLEGIATE = "collegiate", "Collegiate"
        UNDER_25 = "under_25", "Under 25"
        OPEN = "open", "Open"
        ANY = "any", "Any"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(
        "chapters.Chapter", on_delete=models.CASCADE, related_name="events"
    )
    slug = models.SlugField(max_length=80)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_tier = models.CharField(
        max_length=20, choices=EventTier.choices, default=EventTier.CHAPTER
    )
    format = models.CharField(max_length=20, choices=Format.choices, default=Format.VIBE)
    timer = models.CharField(max_length=20, choices=Timer.choices, default=Timer.SPRINT)
    access_mode = models.CharField(
        max_length=20, choices=AccessMode.choices, default=AccessMode.APPLICATION
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    player_tier_restriction = models.CharField(
        max_length=20,
        choices=PlayerTierRestriction.choices,
        default=PlayerTierRestriction.ANY,
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="events_created"
    )

    class Meta:
        db_table = "events_event"
        ordering = ("-scheduled_start",)
        constraints = [
            models.UniqueConstraint(fields=["chapter", "slug"], name="unique_chapter_event_slug"),
        ]

    def __str__(self):
        return self.name


class EventParticipant(models.Model):
    """Anyone associated with an event as a person — player, judge, or audience —
    however they joined (invited, applied/RSVP'd, or pulled from the chapter judge
    corps). Replaces the old JudgeAssignment: a judge is a participant with role=judge.
    See DATA_MODEL.md."""

    class Role(models.TextChoices):
        PLAYER = "player", "Player"
        JUDGE = "judge", "Judge"
        AUDIENCE = "audience", "Audience"

    class JudgeSpecialization(models.TextChoices):
        TESTER = "tester", "Tester"
        UX_DESIGNER = "ux_designer", "UX Designer"
        GENERAL = "general", "General"

    class Source(models.TextChoices):
        INVITED = "invited", "Invited"
        APPLIED = "applied", "Applied"
        CORPS = "corps", "Corps"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REGISTERED = "registered", "Registered"
        DECLINED = "declined", "Declined"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    # user is null until an emailed invite is claimed; email carries the invite meanwhile.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_participations",
    )
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    judge_specialization = models.CharField(
        max_length=20, choices=JudgeSpecialization.choices, blank=True
    )
    source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Set when this participant is a corps judge drawn from the chapter's standing corps.
    chapter_staff = models.ForeignKey(
        "chapters.ChapterStaff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corps_assignments",
    )
    token = models.CharField(max_length=64, blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_invites_sent",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_decisions_made",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "events_participant"
        ordering = ("created_at",)
        constraints = [
            # one row per known user per event, and per invited email per event
            models.UniqueConstraint(
                fields=["event", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_event_user",
            ),
            models.UniqueConstraint(
                fields=["event", "email"],
                condition=~models.Q(email=""),
                name="unique_event_email",
            ),
        ]

    def __str__(self):
        who = self.user or self.email or "?"
        return f"{who} — {self.role} @ {self.event}"
