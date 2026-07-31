"""
Celery application for Logistica Tracking.

Used to resolve accept-conflict windows in the background (see
deliveries/tasks.py) without blocking the HTTP request thread that handles
POST /api/deliveries/<id>/accept/. In local/test settings
CELERY_TASK_ALWAYS_EAGER=True makes every task run synchronously in-process,
so no broker or worker is needed for local dev. In production, tasks are
dispatched to a real worker process over Redis (CELERY_BROKER_URL), started
as a separate process (see Procfile / docker-compose.yml `worker` service).
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistica_tracking.settings.local")

app = Celery("logistica_tracking")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
