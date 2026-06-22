from django.utils import timezone
from rest_framework import serializers

from events.models import Event

from .models import Round
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
