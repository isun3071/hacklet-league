from rest_framework import serializers

from .models import Ranking


class RankingSerializer(serializers.ModelSerializer):
    """A public leaderboard row. Exposes the placing player's id + display name (rankings are
    publicly visible by design — format_spec §7) but no private account fields."""

    user_id = serializers.UUIDField(read_only=True)
    player_display = serializers.SerializerMethodField()

    class Meta:
        model = Ranking
        fields = [
            "rank", "user_id", "player_display", "scope", "scope_reference_id",
            "period", "season_year", "rank_points", "events_competed",
            "last_event_at", "updated_at",
        ]

    def get_player_display(self, obj):
        return obj.user.display_name or ""
