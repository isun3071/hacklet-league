from rest_framework import serializers

from chapters.models import Chapter

from .models import Event, EventParticipant


class EventChapterSerializer(serializers.Serializer):
    """Minimal chapter reference embedded in event reads (the full chapter lives at
    /api/chapters/<slug>/). `tier` is the host chapter's operational tier (A/B/C) — one of
    the three distinct "tier" axes the UI disambiguates."""

    id = serializers.UUIDField()
    slug = serializers.SlugField()
    name = serializers.CharField()
    tier = serializers.CharField()


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


# ---- participants ----------------------------------------------------------

class EventParticipantSerializer(serializers.ModelSerializer):
    """Read view of an event participant (player / judge / audience).

    `email` is PII: it's revealed only to chapter managers (via the ``reveal_email``
    context flag the view sets) and to the participant themselves. Everyone else — e.g. a
    public schedule page — sees only ``display_name`` + role/status.
    """

    display_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()

    class Meta:
        model = EventParticipant
        fields = [
            "id", "event", "role", "judge_specialization", "source", "status",
            "display_name", "email", "created_at", "responded_at",
        ]

    def get_display_name(self, obj):
        if obj.user_id and obj.user.display_name:
            return obj.user.display_name
        return ""

    def get_email(self, obj):
        if self.context.get("reveal_email"):
            return obj.user.email if obj.user_id else obj.email
        request = self.context.get("request")
        u = getattr(request, "user", None)
        if u and getattr(u, "is_authenticated", False) and obj.user_id == u.id:
            return obj.user.email
        return ""

    def get_event(self, obj):
        return {"id": str(obj.event_id), "slug": obj.event.slug, "name": obj.event.name}


class _RoleSpecSerializer(serializers.Serializer):
    """Shared base: a role + optional judge specialization (cleared unless role=judge)."""

    role = serializers.ChoiceField(choices=EventParticipant.Role.choices)
    judge_specialization = serializers.ChoiceField(
        choices=EventParticipant.JudgeSpecialization.choices,
        required=False, allow_blank=True, default="",
    )

    def validate(self, attrs):
        if attrs.get("role") != EventParticipant.Role.JUDGE:
            attrs["judge_specialization"] = ""
        return attrs


class ApplySerializer(_RoleSpecSerializer):
    """Body for self-application: {role, judge_specialization?}."""


class InviteSerializer(_RoleSpecSerializer):
    """Body for a manager invite: exactly one of email / user_id, plus role."""

    email = serializers.EmailField(required=False, allow_blank=True)
    user_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if bool(attrs.get("email")) == bool(attrs.get("user_id")):
            raise serializers.ValidationError("Provide exactly one of email or user_id.")
        return attrs


class CorpsJudgeSerializer(serializers.Serializer):
    """Body to assign a standing chapter judge to an event."""

    chapter_staff_id = serializers.UUIDField()
    judge_specialization = serializers.ChoiceField(
        choices=EventParticipant.JudgeSpecialization.choices,
        required=False, allow_blank=True, default="",
    )


class RespondSerializer(serializers.Serializer):
    """An invitee answering their invitation."""

    action = serializers.ChoiceField(choices=["accept", "decline"])


class DecideSerializer(serializers.Serializer):
    """A manager ruling on an application."""

    action = serializers.ChoiceField(choices=["approve", "reject"])
