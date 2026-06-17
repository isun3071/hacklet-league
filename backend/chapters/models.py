import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Chapter(models.Model):
    """A local operational unit of the league. First-class even at single-chapter MVP."""

    class Tier(models.TextChoices):
        A = "A", "Tier A (Verified)"
        B = "B", "Tier B (Standard)"
        C = "C", "Tier C (Practice)"

    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        SUSPENDED = "suspended", "Suspended"

    class Mode(models.TextChoices):
        SIGNUP = "signup", "Signup"
        ACTIVE = "active", "Active"
        ARCHIVE = "archive", "Archive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location_text = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="chapters_created"
    )
    tier = models.CharField(max_length=1, choices=Tier.choices, default=Tier.C)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.SIGNUP)
    institutional_affiliation = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    website_url = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chapters_verified",
    )
    suspended_reason = models.TextField(blank=True)

    class Meta:
        db_table = "chapters_chapter"
        ordering = ("name",)

    def __str__(self):
        return self.name


class ChapterMembership(models.Model):
    """A user's roles within a chapter. One row per (user, chapter)."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        JUDGE = "judge", "Judge"
        PLAYER = "player", "Player"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="memberships")
    # List of Role values; a user can hold several (e.g. judge + player). See DATA_MODEL.md.
    roles = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    joined_at = models.DateTimeField(default=timezone.now)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships_approved",
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "chapters_membership"
        constraints = [
            models.UniqueConstraint(fields=["user", "chapter"], name="unique_user_chapter"),
        ]

    def __str__(self):
        return f"{self.user} @ {self.chapter}"
