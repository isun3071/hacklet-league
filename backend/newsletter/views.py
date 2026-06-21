"""Newsletter signup — a thin server-side proxy to the Buttondown API.

The Buttondown API key is a secret, so the browser never sees it: the SPA POSTs an email
here, and this view forwards it to Buttondown. Double opt-in is Buttondown's default (we
omit `type`), so Buttondown emails the subscriber a confirmation link — which is exactly
the flow we want (consent + list hygiene). See claude.md / DEPLOY.md.
"""
import logging

import requests
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class NewsletterThrottle(AnonRateThrottle):
    # Rate set in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["newsletter"].
    # Curbs using our endpoint to relay Buttondown confirmation emails to arbitrary addresses.
    scope = "newsletter"


class NewsletterSubscribeView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [NewsletterThrottle]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        try:
            validate_email(email)
        except DjangoValidationError:
            return Response(
                {"detail": "Enter a valid email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not settings.BUTTONDOWN_API_KEY:
            logger.error("Newsletter signup hit but BUTTONDOWN_API_KEY is not configured.")
            return Response(
                {"detail": "Newsletter signup is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            resp = requests.post(
                f"{settings.BUTTONDOWN_API_URL.rstrip('/')}/subscribers",
                headers={"Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"},
                json={"email_address": email},
                timeout=10,
            )
        except requests.RequestException:
            logger.exception("Buttondown subscribe request failed")
            return Response(
                {"detail": "Could not reach the newsletter service. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if resp.status_code in (200, 201):
            return Response(
                {"detail": "Almost there — check your email to confirm your subscription."},
                status=status.HTTP_201_CREATED,
            )

        # Buttondown rejects an existing subscriber; surface that as a friendly success.
        if resp.status_code in (400, 409) and "already" in resp.text.lower():
            return Response(
                {"detail": "You're already on the list. 🎉"},
                status=status.HTTP_200_OK,
            )

        logger.warning("Buttondown subscribe failed (%s): %s", resp.status_code, resp.text[:300])
        return Response(
            {"detail": "Could not sign you up right now. Please try again."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
