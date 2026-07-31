from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from accounts.models import User
from deliveries.models import Delivery


class BroadcastConsumerMixin:
    """Shared teardown + inbound event->client relay for group-based consumers."""

    group_name = None

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def broadcast_event(self, event):
        await self.send_json({"event": event["event"], "payload": event["payload"]})


class DriverConsumer(BroadcastConsumerMixin, AsyncJsonWebsocketConsumer):
    """A driver's personal channel: job_request / job_taken / job_accepted / delivery_confirmed."""

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated or user.role != User.Role.DRIVER:
            await self.close(code=4403)
            return
        self.group_name = f"driver_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()


class TrackingConsumer(BroadcastConsumerMixin, AsyncJsonWebsocketConsumer):
    """Live tracking for one delivery: location_update / delivery_confirmed."""

    async def connect(self):
        user = self.scope["user"]
        delivery_id = self.scope["url_route"]["kwargs"]["delivery_id"]

        if not user.is_authenticated or not await self._can_view(user, delivery_id):
            await self.close(code=4403)
            return

        self.group_name = f"delivery_{delivery_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    @database_sync_to_async
    def _can_view(self, user, delivery_id):
        try:
            delivery = Delivery.objects.get(pk=delivery_id)
        except Delivery.DoesNotExist:
            return False
        if user.role == User.Role.ADMIN:
            return True
        if user.role == User.Role.CLIENT:
            return delivery.client_id == user.id
        if user.role == User.Role.DRIVER:
            return delivery.driver_id == user.id
        return False


class AdminConsumer(BroadcastConsumerMixin, AsyncJsonWebsocketConsumer):
    """Admin dashboard channel: conflict_alert / job_taken."""

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated or user.role != User.Role.ADMIN:
            await self.close(code=4403)
            return
        self.group_name = "admin_dashboard"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
