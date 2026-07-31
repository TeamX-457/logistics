"""
Thin wrapper around the Channels layer for pushing domain events to
WebSocket-connected clients. Group naming is centralized here so the
consumers (tracking/consumers.py) and every app that triggers an event
(deliveries, admin_panel, trips) agree on the same names.

Groups:
  delivery_{id}  -> client + admin watching one delivery's live tracking
  driver_{id}    -> a specific driver's personal notification channel
  admin_dashboard -> all connected admin dashboards
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def _group_send(group_name: str, event_type: str, payload: dict):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "broadcast_event", "event": event_type, "payload": payload},
    )


def delivery_group_name(delivery_id) -> str:
    return f"delivery_{delivery_id}"


def driver_group_name(driver_id) -> str:
    return f"driver_{driver_id}"


ADMIN_GROUP = "admin_dashboard"


def notify_delivery_group(delivery_id, event_type: str, payload: dict):
    _group_send(delivery_group_name(delivery_id), event_type, payload)


def notify_driver(driver_id, event_type: str, payload: dict):
    _group_send(driver_group_name(driver_id), event_type, payload)


def notify_admins(event_type: str, payload: dict):
    _group_send(ADMIN_GROUP, event_type, payload)
