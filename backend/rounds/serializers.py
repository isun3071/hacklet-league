from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from events.models import Event

from .models import Round, Score, Submission
from .services import PROMPT_VISIBLE_PHASES, current_phase


class RoundEventRefSerializer(serializers.Serializer):
    """Minimal event reference embedded in round reads."""

    id = serializers.UUIDField()
    slug = serializers.SlugField()
    name = serializers.CharField()
    chapter_slug = serializers.SerializerMethodField()

    def get_chapter_slug(self, obj):
        return obj.chapter.slug


class RoundSerializer(serializers.ModelSerializer):
    """Read view + the poll payload.

    `status` is the coarse lifecycle (scheduled / completed / cancelled). `phase` is the
    LIVE phase, derived server-side from the clock vs the absolute boundaries — that's the
    authoritative value. `server_time` lets the client correct for its own clock skew when
    rendering the countdown. `prompt_revealed` is gated so it only appears once build starts.
    """

    event = RoundEventRefSerializer(read_only=True)
    phase = serializers.SerializerMethodField()
    server_time = serializers.SerializerMethodField()
    prompt_revealed = serializers.SerializerMethodField()
    checked_in_count = serializers.SerializerMethodField()

    class Meta:
        model = Round
        fields = [
            "id", "event", "round_number", "timing_profile", "status", "phase",
            "server_time", "opening_at", "build_start_at", "build_end_at",
            "phase_schedule", "player_count", "checked_in_count", "prompt_revealed",
            "created_at",
        ]

    def _now(self):
        return self.context.get("now") or timezone.now()

    def get_phase(self, obj):
        return current_phase(obj, self._now())

    def get_server_time(self, obj):
        return self._now().isoformat()

    def get_checked_in_count(self, obj):
        return obj.submissions.count()

    def get_prompt_revealed(self, obj):
        if current_phase(obj, self._now()) in PROMPT_VISIBLE_PHASES:
            return obj.prompt_revealed
        return ""


class RoundWriteSerializer(serializers.ModelSerializer):
    """Fields a chapter manager may set. `event` is write-once. Timeline fields
    (opening_at/build_*/phase_schedule) are server-owned via the `schedule`/`start` actions,
    not set directly here."""

    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = Round
        # round_number is server-assigned (auto-incremented per event in the view), so it's
        # deliberately not a writable field — that also avoids DRF's auto UniqueTogether
        # validator defaulting it to 1 and colliding on the second round.
        fields = ["event", "timing_profile", "player_count", "prompt_revealed"]

    def validate(self, attrs):
        if self.instance and "event" in attrs and attrs["event"].id != self.instance.event_id:
            raise serializers.ValidationError(
                {"event": "A round can't be moved to another event."}
            )
        return attrs


class ScheduleSerializer(serializers.Serializer):
    """Body for the `schedule` action: an opening anchor + optional profile override."""

    opening_at = serializers.DateTimeField()
    timing_profile = serializers.ChoiceField(
        choices=Round.TimingProfile.choices, required=False,
    )


class SubmissionSerializer(serializers.ModelSerializer):
    """Read view of a submission. Never exposes the archive's storage path/URL — clients
    fetch the file via the auth-gated /api/submissions/<id>/download/ endpoint. Identity is
    shown because access is already restricted to the player, managers, and judges."""

    round = serializers.PrimaryKeyRelatedField(read_only=True)
    player_email = serializers.SerializerMethodField()
    player_display = serializers.SerializerMethodField()
    has_archive = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id", "round", "player_email", "player_display", "status", "deployed_url",
            "readme_content", "attack_surface_coverage", "has_archive", "archive_filename",
            "submitted_at", "created_at",
        ]

    def get_player_email(self, obj):
        return obj.player.email

    def get_player_display(self, obj):
        return obj.player.display_name or ""

    def get_has_archive(self, obj):
        return bool(obj.archive)


class SubmitSerializer(serializers.Serializer):
    """Upload body (multipart). The archive is validated cheaply (size + zip magic) but NOT
    extracted — at rest it's an opaque blob; unpacking happens only in the Stage 5 sandbox."""

    archive = serializers.FileField()
    readme_content = serializers.CharField(required=False, allow_blank=True, default="")
    deployed_url = serializers.URLField(required=False, allow_blank=True, default="")
    attack_surface_coverage = serializers.ChoiceField(
        choices=Submission.AttackSurfaceCoverage.choices,
        required=False, allow_blank=True, default="",
    )

    def validate_archive(self, f):
        if f.size > settings.MAX_SUBMISSION_BYTES:
            mb = settings.MAX_SUBMISSION_BYTES // (1024 * 1024)
            raise serializers.ValidationError(f"Archive too large (max {mb} MB).")
        head = f.read(2)
        f.seek(0)
        if head != b"PK":  # every zip variant begins with the "PK" signature
            raise serializers.ValidationError("Upload must be a .zip archive.")
        return f


class ScoreSerializer(serializers.ModelSerializer):
    """Read view of a single judge's score (managers/judges only)."""

    judge_email = serializers.SerializerMethodField()

    class Meta:
        model = Score
        fields = [
            "id", "submission", "judge_participant", "judge_email",
            "score_type", "value", "comments", "submitted_at",
        ]

    def get_judge_email(self, obj):
        jp = obj.judge_participant
        if not jp:
            return ""
        return jp.user.email if jp.user_id else jp.email


class ScoreWriteSerializer(serializers.Serializer):
    """A judge scoring one dimension of a submission. judge_participant is derived from the
    requesting user in the view (never client-supplied)."""

    submission = serializers.PrimaryKeyRelatedField(queryset=Submission.objects.all())
    score_type = serializers.ChoiceField(choices=Score.ScoreType.choices)
    value = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0, max_value=100)
    comments = serializers.CharField(required=False, allow_blank=True, default="")
