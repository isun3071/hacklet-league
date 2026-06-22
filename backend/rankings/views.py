import uuid

from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from chapters.models import Chapter
from chapters.permissions import is_chapter_manager

from .models import Ranking
from .serializers import RankingSerializer


class RankingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Public, read-only leaderboards (all-time). Two scopes:

      GET /api/rankings/?scope=global              — across Tier A chapters only
      GET /api/rankings/?scope=chapter&chapter=ID  — one chapter's board

    Rankings are public by design (format_spec §7). A chapter board follows the same visibility
    as that chapter's events: public once the chapter is verified, otherwise managers only.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = RankingSerializer

    def get_queryset(self):
        return Ranking.objects.select_related("user").filter(
            period=Ranking.Period.ALL_TIME
        )

    def list(self, request, *args, **kwargs):
        scope = request.query_params.get("scope", Ranking.Scope.GLOBAL)
        qs = self.get_queryset()
        if scope == Ranking.Scope.GLOBAL:
            qs = qs.filter(scope=Ranking.Scope.GLOBAL, scope_reference_id__isnull=True)
        elif scope == Ranking.Scope.CHAPTER:
            chapter = self._resolve_chapter(request)
            qs = qs.filter(scope=Ranking.Scope.CHAPTER, scope_reference_id=chapter.id)
        else:
            raise ValidationError("scope must be 'global' or 'chapter'.")
        qs = qs.order_by("rank", "-rank_points")
        return Response(self.get_serializer(qs, many=True).data)

    def _resolve_chapter(self, request):
        chapter_id = request.query_params.get("chapter")
        if not chapter_id:
            raise ValidationError("scope=chapter requires ?chapter=<id>.")
        try:
            uuid.UUID(str(chapter_id))
        except ValueError:
            raise ValidationError("Invalid chapter id.")
        chapter = Chapter.objects.filter(id=chapter_id).first()
        if not chapter:
            raise ValidationError("Unknown chapter.")
        public = chapter.verification_status == Chapter.VerificationStatus.VERIFIED
        if not (public or is_chapter_manager(request.user, chapter)):
            raise PermissionDenied("This chapter's leaderboard isn't public.")
        return chapter
