"""Rename ChapterMembership -> ChapterStaff.

Chapters are event hosts, not membership societies: the org/judge-corps team is now
ChapterStaff, and players relate to events via events.EventParticipant (not chapters).
This is a state + table rename — the few existing owner rows are preserved. The Role
enum change (admin->organizer, drop player) needs no DB op: roles is a JSONField with
no DB-level choices, and existing data is only ["owner"]. See DATA_MODEL.md.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chapters", "0003_chapter_default_pending"),
    ]

    operations = [
        migrations.RenameModel(old_name="ChapterMembership", new_name="ChapterStaff"),
        migrations.AlterModelTable(name="chapterstaff", table="chapters_staff"),
    ]
