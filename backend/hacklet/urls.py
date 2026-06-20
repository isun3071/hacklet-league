from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.routers import DefaultRouter

from chapters.views import ChapterViewSet
from users.views import MeView


def healthz(_request):
    """Liveness probe for uptime monitoring."""
    return JsonResponse({"status": "ok"})


@ensure_csrf_cookie
def csrf(_request):
    """Sets the csrftoken cookie so the SPA can send X-CSRFToken on writes."""
    return JsonResponse({"detail": "ok"})


router = DefaultRouter()
router.register(r"chapters", ChapterViewSet, basename="chapter")

urlpatterns = [
    # Mounted at a secret, env-set slug in prod; Caddy gates that path to the tailnet.
    path(f"{settings.ADMIN_PATH}/", admin.site.urls),
    path("api/healthz", healthz),
    path("api/csrf/", csrf),
    path("api/me/", MeView.as_view()),
    path("api/", include(router.urls)),
    # django-allauth. The headless API drives the SPA; the regular allauth URLs are
    # mounted because (even with HEADLESS_ONLY) they serve the social provider OAuth
    # callbacks — e.g. /accounts/google/login/callback/, the URI registered with Google.
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
]
