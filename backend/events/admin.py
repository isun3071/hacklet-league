from django.contrib import admin

from .models import Event, EventParticipant


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name", "chapter", "event_tier", "format", "timer",
        "access_mode", "status", "scheduled_start",
    )
    list_filter = ("event_tier", "format", "timer", "access_mode", "status")
    search_fields = ("name", "slug", "chapter__name")
    autocomplete_fields = ("chapter", "created_by")
    readonly_fields = ("created_at",)


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ("__str__", "event", "role", "source", "status", "judge_specialization")
    list_filter = ("role", "source", "status")
    search_fields = ("user__email", "email", "event__name")
    autocomplete_fields = ("event", "user", "chapter_staff", "invited_by", "decided_by")
    readonly_fields = ("created_at",)
