from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from chapters.models import Chapter

from .models import Event
from .permissions import is_chapter_manager, managed_chapter_ids
from .serializers import EventSerializer, EventWriteSerializer


class EventViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Public event directory + chapter-manager event CRUD.

    Reads (list/retrieve) show events of VERIFIED chapters to everyone, plus a manager's
    own chapters' events (any chapter status) so they can plan before verification. Writes
    are scoped to chapters the user actively owns/organizes — non-managers get 404 (not
    403) on a specific event and can't probe existence. Lookup is by event UUID (event
    slugs are unique only per chapter); filter the list by `?chapter=<slug>` (and
    optionally `&slug=<event-slug>`) to resolve a chapter's events. See BUILD_ROADMAP
    Stage 2.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Event.objects.select_related("chapter")
        user = self.request.user
        if self.action in ("update", "partial_update", "destroy"):
            if not user.is_authenticated:
                return qs.none()
            return qs.filter(chapter_id__in=managed_chapter_ids(user))

        visible = Q(chapter__verification_status=Chapter.VerificationStatus.VERIFIED)
        if user.is_authenticated:
            visible |= Q(chapter_id__in=managed_chapter_ids(user))
        qs = qs.filter(visible)
        if self.action == "list":
            chapter_slug = self.request.query_params.get("chapter")
            if chapter_slug:
                qs = qs.filter(chapter__slug=chapter_slug)
            event_slug = self.request.query_params.get("slug")
            if event_slug:
                qs = qs.filter(slug=event_slug)
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EventWriteSerializer
        return EventSerializer

    def create(self, request, *args, **kwargs):
        write = self.get_serializer(data=request.data)
        write.is_valid(raise_exception=True)
        if not is_chapter_manager(request.user, write.validated_data["chapter"]):
            raise PermissionDenied("You don't manage this chapter.")
        self.perform_create(write)
        read = EventSerializer(write.instance, context=self.get_serializer_context())
        return Response(read.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def perform_create(self, serializer):
        chapter = serializer.validated_data["chapter"]
        serializer.save(
            created_by=self.request.user,
            slug=self._unique_slug(chapter, serializer.validated_data["name"]),
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()  # scoped queryset -> 404 for non-managers
        write = self.get_serializer(instance, data=request.data, partial=partial)
        write.is_valid(raise_exception=True)
        self.perform_update(write)
        read = EventSerializer(instance, context=self.get_serializer_context())
        return Response(read.data)

    @staticmethod
    def _unique_slug(chapter, name):
        base = slugify(name) or "event"
        slug, i = base, 2
        while Event.objects.filter(chapter=chapter, slug=slug).exists():
            slug, i = f"{base}-{i}", i + 1
        return slug

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        """Events for chapters the user manages (their dashboard), any chapter status."""
        qs = Event.objects.select_related("chapter").filter(
            chapter_id__in=managed_chapter_ids(request.user)
        )
        data = EventSerializer(qs, many=True, context=self.get_serializer_context()).data
        return Response(data)
