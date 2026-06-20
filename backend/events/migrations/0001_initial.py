import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("chapters", "0004_rename_chaptermembership_to_chapterstaff"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("slug", models.SlugField(max_length=80)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("event_tier", models.CharField(choices=[("chapter", "Chapter"), ("regional", "Regional"), ("championship", "Championship")], default="chapter", max_length=20)),
                ("format", models.CharField(choices=[("vibe", "Vibe"), ("unslop", "Unslop")], default="vibe", max_length=20)),
                ("timer", models.CharField(choices=[("xp", "XP (12 min)"), ("sprint", "Sprint (24 min)"), ("scrum", "Scrum (36 min)"), ("agile", "Agile (48 min)"), ("waterfall", "Waterfall (72-96 min)")], default="sprint", max_length=20)),
                ("access_mode", models.CharField(choices=[("invite_only", "Invite only"), ("application", "Application")], default="application", max_length=20)),
                ("status", models.CharField(choices=[("scheduled", "Scheduled"), ("registration_open", "Registration open"), ("registration_closed", "Registration closed"), ("in_progress", "In progress"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="scheduled", max_length=20)),
                ("scheduled_start", models.DateTimeField()),
                ("scheduled_end", models.DateTimeField()),
                ("actual_start", models.DateTimeField(blank=True, null=True)),
                ("actual_end", models.DateTimeField(blank=True, null=True)),
                ("player_tier_restriction", models.CharField(choices=[("collegiate", "Collegiate"), ("under_25", "Under 25"), ("open", "Open"), ("any", "Any")], default="any", max_length=20)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("chapter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="chapters.chapter")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="events_created", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "events_event",
                "ordering": ("-scheduled_start",),
                "constraints": [
                    models.UniqueConstraint(fields=("chapter", "slug"), name="unique_chapter_event_slug"),
                ],
            },
        ),
        migrations.CreateModel(
            name="EventParticipant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("role", models.CharField(choices=[("player", "Player"), ("judge", "Judge"), ("audience", "Audience")], max_length=20)),
                ("judge_specialization", models.CharField(blank=True, choices=[("tester", "Tester"), ("ux_designer", "UX Designer"), ("general", "General")], max_length=20)),
                ("source", models.CharField(choices=[("invited", "Invited"), ("applied", "Applied"), ("corps", "Corps")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("registered", "Registered"), ("declined", "Declined"), ("rejected", "Rejected"), ("withdrawn", "Withdrawn")], default="pending", max_length=20)),
                ("token", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="events.event")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="event_participations", to=settings.AUTH_USER_MODEL)),
                ("chapter_staff", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="corps_assignments", to="chapters.chapterstaff")),
                ("invited_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="event_invites_sent", to=settings.AUTH_USER_MODEL)),
                ("decided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="event_decisions_made", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "events_participant",
                "ordering": ("created_at",),
                "constraints": [
                    models.UniqueConstraint(fields=("event", "user"), condition=models.Q(user__isnull=False), name="unique_event_user"),
                    models.UniqueConstraint(fields=("event", "email"), condition=~models.Q(email=""), name="unique_event_email"),
                ],
            },
        ),
    ]
