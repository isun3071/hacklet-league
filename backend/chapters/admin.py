from django.contrib import admin

from .models import Chapter, ChapterMembership


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "tier", "verification_status", "mode", "created_by", "created_at")
    list_filter = ("tier", "verification_status", "mode")
    search_fields = ("name", "slug", "location_text")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)
    autocomplete_fields = ("created_by", "verified_by")


@admin.register(ChapterMembership)
class ChapterMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "chapter", "status", "joined_at")
    list_filter = ("status",)
    search_fields = ("user__email", "chapter__name")
    autocomplete_fields = ("user", "chapter", "approved_by")
