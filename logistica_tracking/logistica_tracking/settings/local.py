"""
Local development / test settings.

SQLite + Channels' InMemoryChannelLayer + Celery in eager mode — no
Postgres, Redis, broker, or worker process needed to run or test this
project locally. This is intentional, not a degraded fallback: local dev
always uses these backends regardless of whether Postgres/Redis happen to
be installed on the machine, so env_check's reachability probe is never
imported here (see logistica_tracking/env_check.py, only used by production.py).
"""
import os

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

DEBUG = True

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-insecure-secret-key-change-me-before-production",
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# CORS is wide open for local/test convenience (Tailwind test frontend +
# React Native dev clients hitting from arbitrary origins).
CORS_ALLOW_ALL_ORIGINS = True

# Local/test only: no throttling on auth endpoints. The 5/hr register and
# 10/hr login limits from base.py are a real production security
# requirement, but each is a single shared bucket per IP across all three
# login/register pages (admin+driver+client), so normal manual multi-role
# testing on one machine exhausts it almost immediately. Never inherited
# by production.py, which keeps the strict rates.
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"register": None, "login": None}}

# Fast, intentionally insecure hasher first — Django's default PBKDF2
# iteration count makes every create_user()/login() call take multiple
# seconds, which adds up fast across a test suite. New passwords hash with
# MD5 (fast); Django's normal hashers stay listed after it purely so
# accounts created before this setting existed (hashed with PBKDF2) can
# still be verified and log in — without them, login for those older
# accounts fails outright since Django can't find a hasher for their
# stored algorithm. Never inherited by production.py, which uses only the
# default secure PBKDF2 hasher.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# Tasks run synchronously, in-process, the moment they're dispatched — no
# broker or worker required. This is what makes AcceptDeliveryView's
# background conflict resolution (deliveries/tasks.py) deterministic and
# testable locally without running `celery worker`. CELERY_BROKER_URL is
# never actually dialed in eager mode; set only to silence Celery/Kombu's
# "no hostname supplied" log noise from its default AMQP placeholder.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"

# Plain print, not logging: this fires at settings-import time, before
# Django's LOGGING config (see base.py) has been applied via dictConfig, so
# a logger call here would silently produce no output.
print("[logistica_tracking] settings=local database=sqlite3 channel_layer=in-memory celery=eager")
