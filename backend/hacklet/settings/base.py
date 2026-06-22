"""Base settings shared across environments. See dev.py / prod.py for overrides."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# The Django admin is mounted at this (secret, env-set) path in production; Caddy
# additionally restricts that path to the Tailscale tailnet, so the public internet
# can't even discover it. Bare slug, no slashes; defaults to "admin" for local dev.
# See DEPLOY.md "Securing the admin portal".
ADMIN_PATH = env("ADMIN_PATH", default="admin").strip("/")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.headless",
    "users",
    "chapters",
    "events",
    "rounds",
    "rankings",
    "newsletter",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "hacklet.urls"
WSGI_APPLICATION = "hacklet.wsgi.application"
ASGI_APPLICATION = "hacklet.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://hacklet:hacklet@db:5432/hacklet"),
}

AUTH_USER_MODEL = "users.User"
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# django-allauth — email-based login, session auth, no usernames (claude.md: sessions, not JWTs)
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True

# Social login (Google). The OAuth app is configured here from env vars — no SocialApp
# DB row needed. The OAuth2 callback is served by allauth.urls at
# /accounts/google/login/callback/ (mounted in urls.py); register that exact URL in
# the Google Cloud console. Leaving the env vars blank disables the provider gracefully.
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_OAUTH_CLIENT_ID", default=""),
            "secret": env("GOOGLE_OAUTH_SECRET", default=""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}
# Google verifies email ownership, so a Google login whose email matches an existing
# verified account logs into it (no duplicate account, no extra verification step).
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True

# Headless API for the Next.js SPA (browser/session client). Frontend routes are
# placeholders until the frontend increment wires them.
HEADLESS_ONLY = True
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": "/auth/verify-email/{key}",
    "account_reset_password": "/auth/password/reset",
    "account_reset_password_from_key": "/auth/password/reset/key/{key}",
    "account_signup": "/auth/signup",
    # Where allauth sends the browser if a social login fails (state lost, user
    # cancels, provider error) — without this it strands them on the backend callback.
    "socialaccount_login_error": "/auth/login?error=social",
}

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="HackLet League <no-reply@hackletleague.com>")

# Newsletter (Buttondown). The API key is secret — only the backend proxy view uses it,
# never the browser. Distinct from transactional email (Resend) above. See claude.md.
BUTTONDOWN_API_KEY = env("BUTTONDOWN_API_KEY", default="")
BUTTONDOWN_API_URL = env("BUTTONDOWN_API_URL", default="https://api.buttondown.com/v1")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    # Only views that opt in (e.g. the public newsletter endpoint) are throttled.
    "DEFAULT_THROTTLE_RATES": {"newsletter": "30/hour"},
}
