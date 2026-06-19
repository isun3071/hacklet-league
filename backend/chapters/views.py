from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Chapter, ChapterMembership
from .serializers import ChapterSerializer, ChapterWriteSerializer


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
        ChapterMembership.objects.create(
            user=self.request.user,
            chapter=chapter,
            roles=[ChapterMembership.Role.OWNER],
            status=ChapterMembership.Status.ACTIVE,
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
