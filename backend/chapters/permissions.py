"""Chapter role helpers, shared by the chapters and events APIs.

A chapter's run-team is its ChapterStaff: owners + organizers manage the chapter (events,
staff), and judges form the corps. "Manager" = active owner OR organizer; "owner" is the
stricter role that alone may grant/revoke ownership. See DATA_MODEL.md and BUILD_ROADMAP
Stage 2 ("basic role permissions").
"""
from .models import ChapterStaff

# ChapterStaff.roles is a JSON list of these string values.
MANAGER_ROLES = {ChapterStaff.Role.OWNER.value, ChapterStaff.Role.ORGANIZER.value}


def _active_staff(user, chapter):
    if not (user and user.is_authenticated):
        return None
    return ChapterStaff.objects.filter(
        user=user, chapter=chapter, status=ChapterStaff.Status.ACTIVE
    ).first()


def is_chapter_manager(user, chapter):
    """True if ``user`` is an active owner/organizer of ``chapter``."""
    staff = _active_staff(user, chapter)
    return bool(staff and MANAGER_ROLES.intersection(staff.roles))


def is_chapter_owner(user, chapter):
    """True if ``user`` is an active owner of ``chapter`` (can manage ownership itself)."""
    staff = _active_staff(user, chapter)
    return bool(staff and ChapterStaff.Role.OWNER.value in staff.roles)


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
