from rest_framework import serializers

from chapters.models import Chapter

from .models import Event


class EventChapterSerializer(serializers.Serializer):
    """Minimal chapter reference embedded in event reads (the full chapter lives at
    /api/chapters/<slug>/)."""

    id = serializers.UUIDField()
    slug = serializers.SlugField()
    name = serializers.CharField()


class EventSerializer(serializers.ModelSerializer):
    """Read view of an event (public schedule pages + the manager dashboard).

    Note the three distinct "tier"-ish fields the UI must keep apart (see DATA_MODEL.md):
      - event_tier             — the event's scope (chapter / regional / championship)
      - chapter.tier           — the host chapter's operational tier (A/B/C), via `chapter`
      - player_tier_restriction — who may compete (collegiate / under_25 / open / any)
    """

    chapter = EventChapterSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "chapter", "slug", "name", "description",
            "event_tier", "format", "timer", "access_mode", "status",
            "scheduled_start", "scheduled_end", "actual_start", "actual_end",
            "player_tier_restriction", "created_at",
        ]


class EventWriteSerializer(serializers.ModelSerializer):
    """Fields a chapter manager may set. The server owns slug + created_by. `chapter` is
    write-once (an event can't be moved between chapters)."""

    chapter = serializers.SlugRelatedField(slug_field="slug", queryset=Chapter.objects.all())

    class Meta:
        model = Event
        fields = [
            "chapter", "name", "description", "event_tier", "format", "timer",
            "access_mode", "scheduled_start", "scheduled_end",
            "player_tier_restriction", "status",
        ]

    def validate(self, attrs):
        start = attrs.get("scheduled_start") or getattr(self.instance, "scheduled_start", None)
        end = attrs.get("scheduled_end") or getattr(self.instance, "scheduled_end", None)
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"scheduled_end": "Must be after scheduled_start."}
            )
        if (
            self.instance
            and "chapter" in attrs
            and attrs["chapter"].id != self.instance.chapter_id
        ):
            raise serializers.ValidationError(
                {"chapter": "An event can't be moved to another chapter."}
            )
        return attrs
