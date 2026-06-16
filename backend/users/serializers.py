from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    """The current user's own profile. Email + verification are read-only here
    (email changes go through allauth's verified-email flow)."""

    class Meta:
        model = User
        fields = ["id", "email", "display_name", "profile_data", "verified_email", "created_at"]
        read_only_fields = ["id", "email", "verified_email", "created_at"]
