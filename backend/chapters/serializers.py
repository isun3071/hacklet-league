from rest_framework import serializers

from .models import Chapter


class ChapterSerializer(serializers.ModelSerializer):
    """Public, read-only view of a chapter (directory + detail pages)."""

    class Meta:
        model = Chapter
        fields = [
            "id", "slug", "name", "description", "location_text", "tier", "mode",
            "verification_status", "institutional_affiliation", "website_url", "created_at",
        ]
        read_only_fields = fields


class ChapterCreateSerializer(serializers.ModelSerializer):
    """Fields a user supplies when applying to create a chapter. Server sets the
    rest (slug, created_by, verification_status, mode) in the view."""

    class Meta:
        model = Chapter
        fields = [
            "name", "description", "location_text", "tier",
            "institutional_affiliation", "contact_email", "website_url",
        ]
