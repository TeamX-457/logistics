"""
Production-only reachability diagnostics.

local.py never imports this module — local dev always runs the SQLite /
in-memory-Channels / eager-Celery stack regardless of what's installed on
the machine, and that is intentional, not an error to detect. production.py
calls check_production_dependencies() once at settings-import time purely
to log a startup warning if Postgres/Redis look unreachable; it never
changes what backend is used (production always uses Postgres/Redis).
"""
import logging
import os
import socket
from urllib.parse import urlparse

logger = logging.getLogger("logistica_tracking")


def _port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_production_dependencies() -> None:
    db_host = os.environ.get("DB_HOST", "")
    db_port = int(os.environ.get("DB_PORT", "5432"))
    if db_host and not _port_open(db_host, db_port):
        logger.warning("Postgres at %s:%s is not reachable at startup.", db_host, db_port)

    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        parsed = urlparse(redis_url)
        redis_host = parsed.hostname
        redis_port = parsed.port or 6379
        if redis_host and not _port_open(redis_host, redis_port):
            logger.warning("Redis at %s:%s is not reachable at startup.", redis_host, redis_port)
