import uuid

from django.conf import settings
from django.db import models


class Ranking(models.Model):
    """A computed leaderboard position for a user within a scope + period. Recomputed after
    events complete (Stage 3 increment 5). Global rankings count Tier A chapter events only,
    for credentialing integrity. See DATA_MODEL.md."""

    class Scope(models.TextChoices):
        GLOBAL = "global", "Global"
        CHAPTER = "chapter", "Chapter"
        REGIONAL = "regional", "Regional"

    class Period(models.TextChoices):
        CURRENT_SEASON = "current_season", "Current season"
        PERSISTENT = "persistent", "Persistent"
        ALL_TIME = "all_time", "All time"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rankings"
    )
    scope = models.CharField(max_length=20, choices=Scope.choices)
    # chapter_id when scope=chapter, region_id when scope=regional, null when global.
    scope_reference_id = models.UUIDField(null=True, blank=True)
    period = models.CharField(max_length=20, choices=Period.choices)
    season_year = models.PositiveIntegerField(null=True, blank=True)
    rank = models.PositiveIntegerField()
    rank_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    events_competed = models.PositiveIntegerField(default=0)
    last_event_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rankings_ranking"
        ordering = ("scope", "period", "rank")
        constraints = [
            # One row per ranking "slot". NULLs in scope_reference_id/season_year are
            # distinct under SQL, so the computation step (increment 5) upserts to stay
            # idempotent for global/all-time slots where those are null.
            models.UniqueConstraint(
                fields=["user", "scope", "scope_reference_id", "period", "season_year"],
                name="unique_ranking_slot",
            ),
        ]

    def __str__(self):
        return f"#{self.rank} {self.user} ({self.scope}/{self.period})"
