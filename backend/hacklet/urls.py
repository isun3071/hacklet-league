from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chapters.views import ChapterViewSet
from users.views import MeView


def healthz(_request):
    """Liveness probe for uptime monitoring."""
    return JsonResponse({"status": "ok"})


router = DefaultRouter()
router.register(r"chapters", ChapterViewSet, basename="chapter")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/healthz", healthz),
    path("api/me/", MeView.as_view()),
    path("api/", include(router.urls)),
    # django-allauth headless API (browser/session client): /_allauth/browser/v1/...
    path("_allauth/", include("allauth.headless.urls")),
]
