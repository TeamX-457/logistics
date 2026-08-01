"""
Settings shared by every environment. Nothing environment-specific lives
here — no SECRET_KEY, DATABASES, CHANNEL_LAYERS, DEBUG, or CORS setting.
Those are defined in local.py (dev) or production.py and one of the two is
always loaded on top of this module (see settings/local.py, settings/production.py).
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
    "channels",
    "accounts",
    "deliveries",
    "tracking",
    "admin_panel",
    "trips",
    "frontend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "logistica_tracking.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "logistica_tracking.wsgi.application"
ASGI_APPLICATION = "logistica_tracking.asgi.application"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF / JWT --------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {
        "register": "5/hour",
        "login": "10/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Logistica Tracking API",
    "DESCRIPTION": (
        "Real-time delivery tracking API. Covers authentication, delivery "
        "lifecycle, driver GPS ingestion, trip history and admin dispatch.\n\n"
        "Live events (job offers, location updates, delivery confirmation) are "
        "delivered over WebSockets, not polled — see the WebSocket section of "
        "the developer guide."
    ),
    "VERSION": "1.0.0",
    # Keep the schema endpoint itself out of the generated schema.
    "SERVE_INCLUDE_SCHEMA": False,
    "SORT_OPERATIONS": False,
}

# --- Domain-specific tuning knobs --------------------------------------
# Window during which two drivers accepting the same job are treated as a
# simultaneous conflict requiring admin resolution, rather than a clean
# first-come win. See deliveries/tasks.py resolve_accept_conflict.
ACCEPT_CONFLICT_WINDOW_SECONDS = float(os.environ.get("ACCEPT_CONFLICT_WINDOW_SECONDS", "1.0"))

# Minimum spacing between GPS pings persisted to Postgres for trip history.
# Every ping still updates Redis immediately for live tracking.
LOCATION_DB_WRITE_INTERVAL_SECONDS = int(os.environ.get("LOCATION_DB_WRITE_INTERVAL_SECONDS", "60"))

# --- Celery ---------------------------------------------------------------
# Broker/result-backend and eager-mode are set per environment (local.py
# runs tasks synchronously in-process; production.py dispatches to a real
# worker over Redis). These serialization/timezone settings apply either way.
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE

# --- Logging ----------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "deliveries": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "tracking": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "admin_panel": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "logistica_tracking": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
