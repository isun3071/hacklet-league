from django.contrib import admin

from .models import Round, Score, Submission


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = (
        "event", "round_number", "timing_profile", "status", "build_end_at", "player_count",
    )
    list_filter = ("timing_profile", "status")
    search_fields = ("event__name",)
    autocomplete_fields = ("event",)
    readonly_fields = ("created_at",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("player", "round", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("player__email", "round__event__name", "git_repo_reference")
    autocomplete_fields = ("round",)
    raw_id_fields = ("player",)
    readonly_fields = ("created_at",)


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("submission", "judge_participant", "score_type", "value", "submitted_at")
    list_filter = ("score_type",)
    search_fields = ("submission__player__email",)
    autocomplete_fields = ("submission", "judge_participant")
    readonly_fields = ("submitted_at",)
