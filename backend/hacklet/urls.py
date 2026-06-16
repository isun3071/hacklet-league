from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthz(_request):
    """Liveness probe for uptime monitoring."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/healthz", healthz),
    # django-allauth headless API (browser/session client): /_allauth/browser/v1/...
    path("_allauth/", include("allauth.headless.urls")),
]
