from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import DeliveryRequest, Message, TrackingPing
from .serializers import MessageSerializer, TrackingPingSerializer


class DeliveryGroupConsumer(AsyncJsonWebsocketConsumer):
    group_prefix = "delivery"

    async def connect(self):
        self.delivery_id = self.scope["url_route"]["kwargs"]["delivery_id"]
        self.group_name = f"{self.group_prefix}_{self.delivery_id}"
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def broadcast_event(self, event):
        await self.send_json(event["payload"])


class TrackingConsumer(DeliveryGroupConsumer):
    group_prefix = "tracking"

    @database_sync_to_async
    def _is_assigned_driver(self, user_id):
        return DeliveryRequest.objects.filter(id=self.delivery_id, driver_id=user_id).exists()

    @database_sync_to_async
    def _save_ping(self, data):
        ping = TrackingPing.objects.create(delivery_id=self.delivery_id, **data)
        return TrackingPingSerializer(ping).data

    async def receive_json(self, content, **kwargs):
        user = self.scope["user"]
        if user.role != "driver" or not await self._is_assigned_driver(user.id):
            return
        payload = await self._save_ping(
            {"lat": content["lat"], "lng": content["lng"], "heading": content.get("heading")}
        )
        await self.channel_layer.group_send(
            self.group_name, {"type": "broadcast_event", "payload": {"event": "tracking_update", "data": payload}}
        )


class ChatConsumer(DeliveryGroupConsumer):
    group_prefix = "chat"

    @database_sync_to_async
    def _save_message(self, text):
        message = Message.objects.create(delivery_id=self.delivery_id, sender=self.scope["user"], text=text)
        return MessageSerializer(message).data

    async def receive_json(self, content, **kwargs):
        text = content.get("text", "")
        if not text:
            return
        payload = await self._save_message(text)
        await self.channel_layer.group_send(
            self.group_name, {"type": "broadcast_event", "payload": {"event": "new_message", "data": payload}}
        )


class MarketplaceConsumer(DeliveryGroupConsumer):
    group_prefix = "marketplace"
