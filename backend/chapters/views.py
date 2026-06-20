from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Chapter, ChapterStaff
from .permissions import is_chapter_manager, is_chapter_owner
from .serializers import (
    ChapterSerializer,
    ChapterStaffSerializer,
    ChapterStaffUpdateSerializer,
    ChapterStaffWriteSerializer,
    ChapterWriteSerializer,
)

User = get_user_model()


class ChapterViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Public chapter directory + authenticated chapter CRUD.

    Listing shows only approved (verified) chapters. A creator can retrieve, edit,
    and delete their own chapters (any status); non-owners can't — write actions are
    scoped to the owner's chapters, so others get 404 (not 403) and can't probe
    existence. Approval/suspension happen in Django admin (superadmin sets
    verification_status); see BUILD_ROADMAP Stage 1.
    """

    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Chapter.objects.all()
        if self.action == "list":
            return qs.filter(verification_status=Chapter.VerificationStatus.VERIFIED)
        if self.action == "retrieve":
            visible = Q(verification_status=Chapter.VerificationStatus.VERIFIED)
            if self.request.user.is_authenticated:
                visible |= Q(created_by=self.request.user)
            return qs.filter(visible)
        if self.action in ("update", "partial_update", "destroy"):
            # Only the creator may edit/delete. Scoping the queryset (rather than
            # raising 403) means a non-owner gets a 404 and can't probe existence.
            if not self.request.user.is_authenticated:
                return qs.none()
            return qs.filter(created_by=self.request.user)
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ChapterWriteSerializer
        return ChapterSerializer

    def create(self, request, *args, **kwargs):
        write = self.get_serializer(data=request.data)
        write.is_valid(raise_exception=True)
        self.perform_create(write)
        read = ChapterSerializer(write.instance, context=self.get_serializer_context())
        return Response(read.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def perform_create(self, serializer):
        chapter = serializer.save(
            created_by=self.request.user,
            slug=self._unique_slug(serializer.validated_data["name"]),
            verification_status=Chapter.VerificationStatus.PENDING,
            mode=Chapter.Mode.SIGNUP,
        )
        ChapterStaff.objects.create(
            user=self.request.user,
            chapter=chapter,
            roles=[ChapterStaff.Role.OWNER],
            status=ChapterStaff.Status.ACTIVE,
        )

    @staticmethod
    def _unique_slug(name):
        base = slugify(name) or "chapter"
        slug, i = base, 2
        while Chapter.objects.filter(slug=slug).exists():
            slug, i = f"{base}-{i}", i + 1
        return slug

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        """Chapters the current user created, any status (for their dashboard)."""
        qs = Chapter.objects.filter(created_by=request.user)
        return Response(self.get_serializer(qs, many=True).data)


class ChapterStaffViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Manage a chapter's run-team (owners / organizers / judge corps).

    Everything here is for chapter managers (active owner/organizer). Two roles are
    privileged: only an OWNER may grant/revoke the owner role or modify an owner row, and
    a chapter can never be left without an active owner. Listing requires `?chapter=<slug>`
    and returns that chapter's staff to its managers only. See BUILD_ROADMAP Stage 2.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChapterStaff.objects.select_related("user", "chapter")

    def _serialize(self, staff, status_code=status.HTTP_200_OK):
        ser = ChapterStaffSerializer(staff, context=self.get_serializer_context())
        return Response(ser.data, status=status_code)

    @staticmethod
    def _active_owner_count(chapter):
        owner = ChapterStaff.Role.OWNER.value
        return sum(
            1
            for s in ChapterStaff.objects.filter(
                chapter=chapter, status=ChapterStaff.Status.ACTIVE
            ).only("roles")
            if owner in s.roles
        )

    def list(self, request, *args, **kwargs):
        chapter_slug = request.query_params.get("chapter")
        if not chapter_slug:
            raise ValidationError({"chapter": "Provide ?chapter=<slug>."})
        chapter = get_object_or_404(Chapter, slug=chapter_slug)
        if not is_chapter_manager(request.user, chapter):
            raise PermissionDenied("You don't manage this chapter.")
        qs = self.get_queryset().filter(chapter=chapter)
        ser = ChapterStaffSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        staff = self.get_object()
        if not (
            staff.user_id == request.user.id
            or is_chapter_manager(request.user, staff.chapter)
        ):
            raise Http404
        return self._serialize(staff)

    def create(self, request, *args, **kwargs):
        write = ChapterStaffWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        data = write.validated_data
        chapter = data["chapter"]
        if not is_chapter_manager(request.user, chapter):
            raise PermissionDenied("You don't manage this chapter.")
        if ChapterStaff.Role.OWNER.value in data["roles"] and not is_chapter_owner(
            request.user, chapter
        ):
            raise PermissionDenied("Only an owner can grant the owner role.")

        if data.get("user_id"):
            target = User.objects.filter(id=data["user_id"]).first()
        else:
            target = User.objects.filter(email__iexact=data["email"]).first()
        if not target:
            raise ValidationError("No account found for that person — they must sign up first.")
        if ChapterStaff.objects.filter(chapter=chapter, user=target).exists():
            raise ValidationError("That person is already staff on this chapter.")

        staff = ChapterStaff.objects.create(
            chapter=chapter,
            user=target,
            roles=data["roles"],
            status=ChapterStaff.Status.ACTIVE,
            approved_by=request.user,
            notes=data["notes"],
        )
        return self._serialize(staff, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        staff = self.get_object()
        if not is_chapter_manager(request.user, staff.chapter):
            raise Http404
        ser = ChapterStaffUpdateSerializer(staff, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        owner = ChapterStaff.Role.OWNER.value
        new_roles = ser.validated_data.get("roles", staff.roles)
        new_status = ser.validated_data.get("status", staff.status)

        # Touching an owner row (or granting owner) is owner-only.
        if (owner in staff.roles or owner in new_roles) and not is_chapter_owner(
            request.user, staff.chapter
        ):
            raise PermissionDenied("Only an owner can change an owner.")
        # Never strip the chapter's last active owner.
        stays_active_owner = owner in new_roles and new_status == ChapterStaff.Status.ACTIVE
        if (
            owner in staff.roles
            and staff.status == ChapterStaff.Status.ACTIVE
            and not stays_active_owner
            and self._active_owner_count(staff.chapter) <= 1
        ):
            raise ValidationError("A chapter must keep at least one active owner.")
        ser.save()
        return self._serialize(staff)

    def destroy(self, request, *args, **kwargs):
        staff = self.get_object()
        if not is_chapter_manager(request.user, staff.chapter):
            raise Http404
        owner = ChapterStaff.Role.OWNER.value
        if owner in staff.roles and not is_chapter_owner(request.user, staff.chapter):
            raise PermissionDenied("Only an owner can remove an owner.")
        if (
            owner in staff.roles
            and staff.status == ChapterStaff.Status.ACTIVE
            and self._active_owner_count(staff.chapter) <= 1
        ):
            raise ValidationError("A chapter must keep at least one active owner.")
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def mine(self, request):
        """The current user's own staff rows — chapters they help run (dashboard)."""
        qs = self.get_queryset().filter(user=request.user)
        ser = ChapterStaffSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(ser.data)
