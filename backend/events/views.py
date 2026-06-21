import secrets

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from chapters.models import Chapter, ChapterStaff

from chapters.permissions import is_chapter_manager, managed_chapter_ids

from .models import Event, EventParticipant
from .serializers import (
    ApplySerializer,
    CorpsJudgeSerializer,
    DecideSerializer,
    EventParticipantSerializer,
    EventSerializer,
    EventWriteSerializer,
    InviteSerializer,
    RespondSerializer,
)

User = get_user_model()


class EventViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Public event directory + chapter-manager event CRUD, plus participant entry points
    (apply / invite / corps-judge assignment / participant listing).

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

    # ---- participants --------------------------------------------------------

    def _require_manager(self, event):
        if not is_chapter_manager(self.request.user, event.chapter):
            raise PermissionDenied("You don't manage this event's chapter.")

    def _require_active_event(self, event):
        if event.status in (Event.Status.COMPLETED, Event.Status.CANCELLED):
            raise ValidationError("This event is closed; you can't add participants.")

    def _participant_response(self, participant, status_code=status.HTTP_200_OK):
        ser = EventParticipantSerializer(
            participant,
            context={**self.get_serializer_context(), "reveal_email": True},
        )
        return Response(ser.data, status=status_code)

    @action(detail=True, methods=["get"])
    def participants(self, request, pk=None):
        """List an event's participants. Public callers see only REGISTERED participants
        (and no emails); chapter managers see everyone — applicants, invitees — with email."""
        event = self.get_object()
        is_mgr = is_chapter_manager(request.user, event.chapter)
        qs = event.participants.select_related("user", "event", "event__chapter").all()
        if not is_mgr:
            qs = qs.filter(status=EventParticipant.Status.REGISTERED)
        ser = EventParticipantSerializer(
            qs, many=True,
            context={**self.get_serializer_context(), "reveal_email": is_mgr},
        )
        return Response(ser.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, pk=None):
        """Self-apply to an application-mode event ("I want to compete/judge/attend").
        Audience attendance is low-stakes and auto-registers; players/judges land in
        PENDING for the organizer to approve."""
        event = self.get_object()
        if event.access_mode != Event.AccessMode.APPLICATION:
            raise PermissionDenied("This event is invite-only.")
        if event.status != Event.Status.REGISTRATION_OPEN:
            raise ValidationError("Registration isn't open for this event.")
        ser = ApplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if EventParticipant.objects.filter(event=event, user=request.user).exists():
            raise ValidationError("You're already a participant in this event.")
        role = ser.validated_data["role"]
        registered = role == EventParticipant.Role.AUDIENCE
        participant = EventParticipant.objects.create(
            event=event,
            user=request.user,
            role=role,
            judge_specialization=ser.validated_data["judge_specialization"],
            source=EventParticipant.Source.APPLIED,
            status=(
                EventParticipant.Status.REGISTERED
                if registered
                else EventParticipant.Status.PENDING
            ),
            responded_at=timezone.now() if registered else None,
        )
        return self._participant_response(participant, status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        """Manager invites someone by account (user_id) or by email (may be unregistered)."""
        event = self.get_object()
        self._require_manager(event)
        self._require_active_event(event)
        ser = InviteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        target_user, email = None, data.get("email", "")
        if data.get("user_id"):
            target_user = User.objects.filter(id=data["user_id"]).first()
            if not target_user:
                raise ValidationError({"user_id": "No such user."})
            email = ""
        elif email:
            # If an account already uses this email, link it; the email column is only for
            # invitees who haven't registered yet.
            target_user = User.objects.filter(email__iexact=email).first()
            if target_user:
                email = ""

        if target_user and EventParticipant.objects.filter(event=event, user=target_user).exists():
            raise ValidationError("That person is already a participant.")
        if email and EventParticipant.objects.filter(event=event, email__iexact=email).exists():
            raise ValidationError("That email is already invited.")

        participant = EventParticipant.objects.create(
            event=event,
            user=target_user,
            email=email,
            role=data["role"],
            judge_specialization=data["judge_specialization"],
            source=EventParticipant.Source.INVITED,
            status=EventParticipant.Status.PENDING,
            invited_by=request.user,
            token=secrets.token_urlsafe(32),
        )
        return self._participant_response(participant, status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="add-corps-judge")
    def add_corps_judge(self, request, pk=None):
        """Assign a standing chapter judge (ChapterStaff with role=judge) to the event.
        Corps judges are pre-vetted, so they're registered directly."""
        event = self.get_object()
        self._require_manager(event)
        self._require_active_event(event)
        ser = CorpsJudgeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        staff = (
            ChapterStaff.objects.filter(
                id=ser.validated_data["chapter_staff_id"], chapter=event.chapter
            )
            .select_related("user")
            .first()
        )
        if not staff:
            raise ValidationError({"chapter_staff_id": "No such staff member in this chapter."})
        if ChapterStaff.Role.JUDGE.value not in staff.roles:
            raise ValidationError({"chapter_staff_id": "That staff member isn't a judge."})
        if EventParticipant.objects.filter(event=event, user=staff.user).exists():
            raise ValidationError("That judge is already assigned to this event.")
        participant = EventParticipant.objects.create(
            event=event,
            user=staff.user,
            role=EventParticipant.Role.JUDGE,
            judge_specialization=ser.validated_data["judge_specialization"],
            source=EventParticipant.Source.CORPS,
            status=EventParticipant.Status.REGISTERED,
            chapter_staff=staff,
            decided_by=request.user,
            responded_at=timezone.now(),
        )
        return self._participant_response(participant, status.HTTP_201_CREATED)


class EventParticipantViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Participant-centric actions: a user's own participations (dashboard), responding to
    an invitation, a manager deciding an application, and withdrawing. All require auth;
    unauthorized access to a specific record returns 404, never leaking existence."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EventParticipantSerializer

    def get_queryset(self):
        return EventParticipant.objects.select_related("user", "event", "event__chapter")

    @staticmethod
    def _is_mine(participant, user):
        return participant.user_id == user.id or (
            participant.user_id is None
            and participant.email
            and participant.email.lower() == user.email.lower()
        )

    def _response(self, participant):
        ser = EventParticipantSerializer(
            participant,
            context={**self.get_serializer_context(), "reveal_email": True},
        )
        return Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        participant = self.get_object()
        if not (
            self._is_mine(participant, request.user)
            or is_chapter_manager(request.user, participant.event.chapter)
        ):
            raise Http404
        return self._response(participant)

    @action(detail=False)
    def mine(self, request):
        """The current user's participations — account-linked rows plus email-only invites
        addressed to their address (so an invite sent before they signed up still shows)."""
        u = request.user
        qs = self.get_queryset().filter(
            Q(user=u) | (Q(user__isnull=True) & Q(email__iexact=u.email))
        )
        ser = EventParticipantSerializer(
            qs, many=True,
            context={**self.get_serializer_context(), "reveal_email": True},
        )
        return Response(ser.data)

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        """Invitee accepts/declines their invitation (and claims an email-only invite)."""
        participant = self.get_object()
        if not self._is_mine(participant, request.user):
            raise Http404
        if participant.source != EventParticipant.Source.INVITED:
            raise ValidationError("Only invitations can be responded to.")
        if participant.status != EventParticipant.Status.PENDING:
            raise ValidationError("This invitation has already been answered.")
        ser = RespondSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if participant.user_id is None:
            if EventParticipant.objects.filter(
                event=participant.event, user=request.user
            ).exists():
                raise ValidationError("You already have a record for this event.")
            participant.user = request.user
            participant.email = ""
        participant.status = (
            EventParticipant.Status.REGISTERED
            if ser.validated_data["action"] == "accept"
            else EventParticipant.Status.DECLINED
        )
        participant.responded_at = timezone.now()
        participant.save(update_fields=["status", "user", "email", "responded_at"])
        return self._response(participant)

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        """Chapter manager approves/rejects a pending application."""
        participant = self.get_object()
        if not is_chapter_manager(request.user, participant.event.chapter):
            raise Http404
        if participant.source != EventParticipant.Source.APPLIED:
            raise ValidationError("Only applications can be decided.")
        if participant.status != EventParticipant.Status.PENDING:
            raise ValidationError("This application has already been decided.")
        ser = DecideSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        participant.status = (
            EventParticipant.Status.REGISTERED
            if ser.validated_data["action"] == "approve"
            else EventParticipant.Status.REJECTED
        )
        participant.decided_by = request.user
        participant.responded_at = timezone.now()
        participant.save(update_fields=["status", "decided_by", "responded_at"])
        return self._response(participant)

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        """A participant withdraws themselves from an event."""
        participant = self.get_object()
        if not self._is_mine(participant, request.user):
            raise Http404
        participant.status = EventParticipant.Status.WITHDRAWN
        participant.responded_at = timezone.now()
        participant.save(update_fields=["status", "responded_at"])
        return self._response(participant)
