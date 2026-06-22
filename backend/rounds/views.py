from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from chapters.models import Chapter
from chapters.permissions import is_chapter_manager, managed_chapter_ids
from events.models import EventParticipant

from .models import Round, Submission
from .serializers import RoundSerializer, RoundWriteSerializer, ScheduleSerializer
from .services import build_phase_schedule


class RoundViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Rounds within an event. Reads (incl. the poll payload) are public for verified-chapter
    events; writes + lifecycle actions are chapter-manager-only. The live phase is computed
    server-side (see services.current_phase); GET /api/rounds/<id>/ is the poll endpoint.
    Filter the list with ?event=<event_id>. See BUILD_ROADMAP Stage 3.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Round.objects.select_related("event", "event__chapter")
        user = self.request.user
        if self.action in ("update", "partial_update", "destroy"):
            if not user.is_authenticated:
                return qs.none()
            return qs.filter(event__chapter_id__in=managed_chapter_ids(user))
        visible = Q(event__chapter__verification_status=Chapter.VerificationStatus.VERIFIED)
        if user.is_authenticated:
            visible |= Q(event__chapter_id__in=managed_chapter_ids(user))
        qs = qs.filter(visible)
        if self.action == "list":
            event_id = self.request.query_params.get("event")
            if event_id:
                qs = qs.filter(event_id=event_id)
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RoundWriteSerializer
        return RoundSerializer

    def get_serializer_context(self):
        # One `now` per request so phase + server_time + prompt gating are consistent.
        ctx = super().get_serializer_context()
        ctx.setdefault("now", timezone.now())
        return ctx

    def _require_manager(self, rnd):
        if not is_chapter_manager(self.request.user, rnd.event.chapter):
            raise PermissionDenied("You don't manage this event's chapter.")

    def _read(self, rnd, status_code=status.HTTP_200_OK):
        return Response(
            RoundSerializer(rnd, context=self.get_serializer_context()).data,
            status=status_code,
        )

    def create(self, request, *args, **kwargs):
        write = self.get_serializer(data=request.data)
        write.is_valid(raise_exception=True)
        event = write.validated_data["event"]
        if not is_chapter_manager(request.user, event.chapter):
            raise PermissionDenied("You don't manage this event's chapter.")
        self.perform_create(write)
        return self._read(write.instance, status.HTTP_201_CREATED)

    @transaction.atomic
    def perform_create(self, serializer):
        event = serializer.validated_data["event"]
        round_number = serializer.validated_data.get("round_number")
        if not round_number:
            last = Round.objects.filter(event=event).order_by("-round_number").first()
            round_number = (last.round_number + 1) if last else 1
        serializer.save(round_number=round_number)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()  # manager-scoped queryset -> 404 for non-managers
        write = self.get_serializer(instance, data=request.data, partial=partial)
        write.is_valid(raise_exception=True)
        self.perform_update(write)
        return self._read(instance)

    # ---- lifecycle (server-authoritative) -----------------------------------

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        """Set the opening anchor; the server derives build_start/build_end/phase_schedule
        as absolute UTC. The round then goes live by the clock when it reaches opening_at."""
        rnd = self.get_object()
        self._require_manager(rnd)
        ser = ScheduleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        profile = ser.validated_data.get("timing_profile") or rnd.timing_profile
        opening_at = ser.validated_data["opening_at"]
        rnd.timing_profile = profile
        rnd.opening_at = opening_at
        rnd.build_start_at, rnd.build_end_at, rnd.phase_schedule = build_phase_schedule(
            profile, opening_at
        )
        rnd.status = Round.Status.SCHEDULED
        rnd.save()
        return self._read(rnd)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Begin the round now — anchors opening_at to the server clock and computes the
        schedule from this instant, so it's immediately live."""
        rnd = self.get_object()
        self._require_manager(rnd)
        now = timezone.now()
        rnd.opening_at = now
        rnd.build_start_at, rnd.build_end_at, rnd.phase_schedule = build_phase_schedule(
            rnd.timing_profile, now
        )
        rnd.status = Round.Status.SCHEDULED
        rnd.save()
        return self._read(rnd)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        rnd = self.get_object()
        self._require_manager(rnd)
        rnd.status = Round.Status.COMPLETED
        rnd.save(update_fields=["status"])
        return self._read(rnd)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        rnd = self.get_object()
        self._require_manager(rnd)
        rnd.status = Round.Status.CANCELLED
        rnd.save(update_fields=["status"])
        return self._read(rnd)

    @action(
        detail=True, methods=["post"], url_path="check-in",
        permission_classes=[permissions.IsAuthenticated],
    )
    def check_in(self, request, pk=None):
        """A registered player checks into a round — reserves their submission slot
        (in_progress). Closes at code-freeze (server clock)."""
        rnd = self.get_object()
        is_player = EventParticipant.objects.filter(
            event=rnd.event,
            user=request.user,
            role=EventParticipant.Role.PLAYER,
            status=EventParticipant.Status.REGISTERED,
        ).exists()
        if not is_player:
            raise PermissionDenied("You're not a registered player for this event.")
        if rnd.status in (Round.Status.COMPLETED, Round.Status.CANCELLED):
            raise ValidationError("This round is closed.")
        if rnd.build_end_at and timezone.now() >= rnd.build_end_at:
            raise ValidationError("Check-in has closed for this round.")
        submission, created = Submission.objects.get_or_create(
            round=rnd,
            player=request.user,
            defaults={"status": Submission.Status.IN_PROGRESS},
        )
        return Response(
            {"checked_in": True, "submission_id": str(submission.id), "created": created},
            status=status.HTTP_200_OK,
        )
