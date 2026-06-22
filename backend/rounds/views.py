from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from chapters.models import Chapter
from chapters.permissions import is_chapter_manager, managed_chapter_ids
from events.models import EventParticipant
from rankings.services import recompute_rankings

from .models import Round, Score, Submission
from .scoring import compute_round_results
from .serializers import (
    RoundSerializer,
    RoundWriteSerializer,
    ScheduleSerializer,
    ScoreSerializer,
    ScoreWriteSerializer,
    SubmissionSerializer,
    SubmitSerializer,
)
from .services import build_phase_schedule, current_phase


def _is_registered_player(user, event):
    if not (user and user.is_authenticated):
        return False
    return EventParticipant.objects.filter(
        event=event, user=user,
        role=EventParticipant.Role.PLAYER, status=EventParticipant.Status.REGISTERED,
    ).exists()


def _is_event_judge(user, event):
    if not (user and user.is_authenticated):
        return False
    return EventParticipant.objects.filter(
        event=event, user=user,
        role=EventParticipant.Role.JUDGE, status=EventParticipant.Status.REGISTERED,
    ).exists()


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
    @transaction.atomic
    def complete(self, request, pk=None):
        """Finalize the round. Results are now revealed publicly and the chapter + global
        leaderboards are recomputed to fold in this round's placements."""
        rnd = self.get_object()
        self._require_manager(rnd)
        rnd.status = Round.Status.COMPLETED
        rnd.save(update_fields=["status"])
        recompute_rankings(rnd.event.chapter)
        return self._read(rnd)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        """Void the round. Leaderboards are recomputed so a previously-completed round that's
        now cancelled is dropped from the standings."""
        rnd = self.get_object()
        self._require_manager(rnd)
        rnd.status = Round.Status.CANCELLED
        rnd.save(update_fields=["status"])
        recompute_rankings(rnd.event.chapter)
        return self._read(rnd)

    @action(
        detail=True, methods=["post"], url_path="check-in",
        permission_classes=[permissions.IsAuthenticated],
    )
    def check_in(self, request, pk=None):
        """A registered player checks into a round — reserves their submission slot
        (in_progress). Closes at code-freeze (server clock)."""
        rnd = self.get_object()
        if not _is_registered_player(request.user, rnd.event):
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

    @action(
        detail=True, methods=["post"], url_path="submit",
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def submit(self, request, pk=None):
        """A registered player uploads their zip. SERVER-AUTHORITATIVE FREEZE: the server
        compares its own clock to build_end_at and rejects anything past it — the client's
        clock/timezone is never consulted. Re-uploading before freeze overwrites."""
        rnd = self.get_object()
        if not _is_registered_player(request.user, rnd.event):
            raise PermissionDenied("You're not a registered player for this event.")
        if rnd.status in (Round.Status.CANCELLED, Round.Status.COMPLETED):
            raise ValidationError("This round is closed.")
        if not rnd.build_end_at:
            raise ValidationError("This round hasn't been scheduled yet.")
        if timezone.now() > rnd.build_end_at:
            raise ValidationError("Code freeze has passed — submissions are closed.")

        ser = SubmitSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        upload = data["archive"]

        submission, _ = Submission.objects.get_or_create(
            round=rnd, player=request.user,
            defaults={"status": Submission.Status.IN_PROGRESS},
        )
        if submission.archive:  # replace any prior upload
            submission.archive.delete(save=False)
        submission.archive_filename = (getattr(upload, "name", "") or "submission.zip")[:255]
        submission.archive.save("submission.zip", upload, save=False)
        submission.readme_content = data.get("readme_content", "")
        submission.deployed_url = data.get("deployed_url", "")
        submission.attack_surface_coverage = data.get("attack_surface_coverage", "")
        submission.status = Submission.Status.SUBMITTED
        submission.submitted_at = timezone.now()
        submission.save()
        return Response(
            SubmissionSerializer(submission, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True)
    def results(self, request, pk=None):
        """Computed standings + categorical awards. Managers/judges can see them anytime;
        the public only once the round reaches awards/completed (results are revealed)."""
        rnd = self.get_object()
        is_staff = is_chapter_manager(request.user, rnd.event.chapter) or _is_event_judge(
            request.user, rnd.event
        )
        revealed = current_phase(rnd, timezone.now()) in ("awards", "completed")
        if not (is_staff or revealed):
            raise PermissionDenied("Results aren't public until the round reaches awards.")
        data = compute_round_results(rnd)
        data["revealed"] = revealed
        return Response(data)


class SubmissionViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read + download submissions. Access is restricted to the submitting player, the
    chapter's managers, and the event's registered judges — submissions are never public.
    Unauthorized access to a specific record returns 404 (no existence leak)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        return Submission.objects.select_related(
            "round", "round__event", "round__event__chapter", "player"
        )

    def _can_access(self, submission, user):
        event = submission.round.event
        return (
            submission.player_id == user.id
            or is_chapter_manager(user, event.chapter)
            or _is_event_judge(user, event)
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        round_id = request.query_params.get("round")
        if round_id:
            qs = qs.filter(round_id=round_id)
            rnd = (
                Round.objects.select_related("event__chapter").filter(id=round_id).first()
            )
            staff_view = rnd and (
                is_chapter_manager(request.user, rnd.event.chapter)
                or _is_event_judge(request.user, rnd.event)
            )
            if not staff_view:
                qs = qs.filter(player=request.user)  # players see only their own
        else:
            qs = qs.filter(player=request.user)
        ser = SubmissionSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        submission = self.get_object()
        if not self._can_access(submission, request.user):
            raise Http404
        ser = SubmissionSerializer(submission, context=self.get_serializer_context())
        return Response(ser.data)

    @action(detail=False)
    def mine(self, request):
        qs = self.get_queryset().filter(player=request.user)
        ser = SubmissionSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(ser.data)

    @action(detail=True)
    def download(self, request, pk=None):
        submission = self.get_object()
        if not self._can_access(submission, request.user):
            raise Http404
        if not submission.archive:
            raise Http404
        return FileResponse(
            submission.archive.open("rb"),
            as_attachment=True,
            filename=submission.archive_filename or "submission.zip",
        )


class ScoreViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Judges record scores per submission per dimension; managers + judges read them.
    judge_participant is derived from the requesting user, never client-supplied. Players
    can't access raw scores (results are surfaced via the round's `results` action)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScoreSerializer

    def get_queryset(self):
        return Score.objects.select_related(
            "submission", "submission__round", "judge_participant", "judge_participant__user"
        )

    def create(self, request, *args, **kwargs):
        write = ScoreWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        submission = write.validated_data["submission"]
        event = submission.round.event
        judge = EventParticipant.objects.filter(
            event=event, user=request.user,
            role=EventParticipant.Role.JUDGE, status=EventParticipant.Status.REGISTERED,
        ).first()
        if not judge:
            raise PermissionDenied("Only registered judges for this event can score.")
        if submission.round.status in (Round.Status.CANCELLED, Round.Status.COMPLETED):
            raise ValidationError("Scoring is closed for this round.")
        score, _ = Score.objects.update_or_create(
            submission=submission,
            judge_participant=judge,
            score_type=write.validated_data["score_type"],
            defaults={
                "value": write.validated_data["value"],
                "comments": write.validated_data.get("comments", ""),
            },
        )
        return Response(ScoreSerializer(score).data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        submission_id = request.query_params.get("submission")
        round_id = request.query_params.get("round")
        if submission_id:
            sub = (
                Submission.objects.select_related("round__event__chapter")
                .filter(id=submission_id).first()
            )
            if not sub:
                raise Http404
            event = sub.round.event
            qs = self.get_queryset().filter(submission_id=submission_id)
        elif round_id:
            rnd = Round.objects.select_related("event__chapter").filter(id=round_id).first()
            if not rnd:
                raise Http404
            event = rnd.event
            qs = self.get_queryset().filter(submission__round_id=round_id)
        else:
            raise ValidationError("Provide ?submission=<id> or ?round=<id>.")
        if not (
            is_chapter_manager(request.user, event.chapter)
            or _is_event_judge(request.user, event)
        ):
            raise PermissionDenied("Only managers and judges can view scores.")
        return Response(ScoreSerializer(qs, many=True).data)
