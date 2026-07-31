"""
Production settings.

PostgreSQL + Redis-backed Channels + a real Celery worker (see
deliveries/tasks.py and the `worker` service/Procfile entry). Every
credential comes from the environment; nothing is hardcoded. Missing
required variables fail startup immediately with a clear error rather than
silently falling back — that fallback behavior belongs to local.py only.
"""
import os

from django.core.exceptions import ImproperlyConfigured

from logistica_tracking import env_check
from .base import *  # noqa: F401,F403


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"{name} environment variable is required in production.")
    return value


DEBUG = False

SECRET_KEY = _require_env("SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _require_env("DB_NAME"),
        "USER": _require_env("DB_USER"),
        "PASSWORD": _require_env("DB_PASSWORD"),
        "HOST": _require_env("DB_HOST"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

REDIS_URL = _require_env("REDIS_URL")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

# Celery dispatches to a real worker process over the same Redis instance
# used for Channels — no second broker to run. See deliveries/tasks.py.
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = False

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# --- Security hardening -------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Diagnostic only — logs a startup warning if Postgres/Redis are
# unreachable. It never changes what backend is used: production always
# uses Postgres/Redis, this just surfaces a misconfigured host/port fast.
env_check.check_production_dependencies()
