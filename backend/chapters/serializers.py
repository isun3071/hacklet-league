from rest_framework import serializers

from .models import Chapter, ChapterStaff


class ChapterSerializer(serializers.ModelSerializer):
    """Read view of a chapter (directory + detail pages). `contact_email` is exposed
    only to the chapter's creator — so they can edit it — and blank for everyone else."""

    contact_email = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = [
            "id", "slug", "name", "description", "location_text", "tier", "mode",
            "verification_status", "institutional_affiliation", "website_url",
            "contact_email", "created_at",
        ]

    def get_contact_email(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and obj.created_by_id == user.id:
            return obj.contact_email
        return ""


class ChapterWriteSerializer(serializers.ModelSerializer):
    """Fields a user may set when creating or editing a chapter. The server owns the
    rest (slug, created_by, verification_status, mode) — never client-writable."""

    class Meta:
        model = Chapter
        fields = [
            "name", "description", "location_text", "tier",
            "institutional_affiliation", "contact_email", "website_url",
        ]


# ---- staff -----------------------------------------------------------------

class ChapterStaffSerializer(serializers.ModelSerializer):
    """Read view of a chapter staff member (org team + judge corps)."""

    user_id = serializers.UUIDField(read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)
    chapter_slug = serializers.SlugField(source="chapter.slug", read_only=True)

    class Meta:
        model = ChapterStaff
        fields = [
            "id", "chapter_slug", "user_id", "email", "display_name",
            "roles", "status", "joined_at", "notes",
        ]


class ChapterStaffWriteSerializer(serializers.Serializer):
    """Add a staff member to a chapter. Identify by user_id or email — but unlike an event
    invite, staff must be an EXISTING account (ChapterStaff.user is required)."""

    chapter = serializers.SlugRelatedField(slug_field="slug", queryset=Chapter.objects.all())
    user_id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=ChapterStaff.Role.choices), allow_empty=False
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if bool(attrs.get("user_id")) == bool(attrs.get("email")):
            raise serializers.ValidationError("Provide exactly one of user_id or email.")
        return attrs


class ChapterStaffUpdateSerializer(serializers.ModelSerializer):
    """Update an existing staff row's roles / status / notes."""

    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=ChapterStaff.Role.choices),
        allow_empty=False, required=False,
    )

    class Meta:
        model = ChapterStaff
        fields = ["roles", "status", "notes"]
