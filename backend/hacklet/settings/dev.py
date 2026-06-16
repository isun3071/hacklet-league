"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Verification / password-reset emails print to the container logs in dev.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
