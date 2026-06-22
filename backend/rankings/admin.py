from django.contrib import admin

from .models import Ranking


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = (
        "rank", "user", "scope", "period", "season_year", "rank_points", "events_competed",
    )
    list_filter = ("scope", "period", "season_year")
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    readonly_fields = ("updated_at",)
