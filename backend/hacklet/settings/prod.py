"""Production settings. Used once we go public (behind Caddy/TLS)."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False
# The Next.js SSR layer fetches the API over the docker network as http://backend:8000,
# so Django sees "Host: backend". That name isn't externally routable, so allowing it is
# safe — without it, every server-rendered page that calls the API 400s (DisallowedHost).
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["hackletleague.com"]) + ["backend", "localhost"]

# Behind Caddy, which terminates TLS and forwards X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://hackletleague.com"])
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Transactional email — three paths, in priority order:
#   1. RESEND_API_KEY set  -> Resend HTTP API over 443 (recommended). Survives ISPs
#      that block SMTP ports, and uses Resend's sending reputation (good for a box on
#      a residential IP, where direct SMTP deliverability is poor).
#   2. EMAIL_HOST set       -> generic SMTP (any provider).
#   3. neither              -> printed to the container logs, so it's never silent.
RESEND_API_KEY = env("RESEND_API_KEY", default="")
EMAIL_HOST = env("EMAIL_HOST", default="")
if RESEND_API_KEY:
    EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
    ANYMAIL = {"RESEND_API_KEY": RESEND_API_KEY}
elif EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
