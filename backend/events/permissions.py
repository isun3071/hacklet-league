"""Permission helpers for the events API.

Managing a chapter's events (and, later, its participants) is scoped to the chapter's
run-team: a user may manage a chapter only if they are ACTIVE ChapterStaff there with an
owner or organizer role. Corps judges (role=judge) are staff but NOT managers. See
DATA_MODEL.md and BUILD_ROADMAP Stage 2 ("basic role permissions").
"""
from chapters.models import ChapterStaff

# ChapterStaff.roles is a JSON list of these string values.
MANAGER_ROLES = {ChapterStaff.Role.OWNER.value, ChapterStaff.Role.ORGANIZER.value}


def is_chapter_manager(user, chapter):
    """True if ``user`` is an active owner/organizer of ``chapter``."""
    if not (user and user.is_authenticated):
        return False
    staff = ChapterStaff.objects.filter(
        user=user, chapter=chapter, status=ChapterStaff.Status.ACTIVE
    ).first()
    return bool(staff and MANAGER_ROLES.intersection(staff.roles))


def managed_chapter_ids(user):
    """IDs of chapters ``user`` actively owns/organizes — for queryset scoping."""
    if not (user and user.is_authenticated):
        return []
    return [
        s.chapter_id
        for s in ChapterStaff.objects.filter(
            user=user, status=ChapterStaff.Status.ACTIVE
        ).only("chapter_id", "roles")
        if MANAGER_ROLES.intersection(s.roles)
    ]
