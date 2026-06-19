from rest_framework import serializers

from .models import Chapter


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
