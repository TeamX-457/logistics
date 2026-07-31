"""
Latest-GPS-coordinate cache: Redis in production, an in-process dict in
local/test settings (where no REDIS_URL is configured at all — see
settings/local.py vs settings/production.py). The in-memory fallback only
works within a single process, so it's a dev/single-instance convenience,
not a production substitute.
"""
import json

import redis
from django.conf import settings

_client = None
_local_cache: dict[int, dict] = {}


def _get_client():
    global _client
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url:
        return None
    if _client is None:
        _client = redis.Redis.from_url(redis_url, decode_responses=True)
    return _client


def _key(delivery_id) -> str:
    return f"delivery:{delivery_id}:latest_location"


def set_latest_location(delivery_id, latitude: float, longitude: float, timestamp_iso: str) -> None:
    payload = {"latitude": latitude, "longitude": longitude, "timestamp": timestamp_iso}
    client = _get_client()
    if client is not None:
        client.set(_key(delivery_id), json.dumps(payload))
    else:
        _local_cache[delivery_id] = payload


def get_latest_location(delivery_id) -> dict | None:
    client = _get_client()
    if client is not None:
        raw = client.get(_key(delivery_id))
        return json.loads(raw) if raw else None
    return _local_cache.get(delivery_id)
