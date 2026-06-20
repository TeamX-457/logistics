from django.urls import re_path

from .consumers import ChatConsumer, MarketplaceConsumer, TrackingConsumer

websocket_urlpatterns = [
    re_path(r"^ws/deliveries/(?P<delivery_id>\d+)/tracking/$", TrackingConsumer.as_asgi()),
    re_path(r"^ws/deliveries/(?P<delivery_id>\d+)/chat/$", ChatConsumer.as_asgi()),
    re_path(r"^ws/deliveries/(?P<delivery_id>\d+)/marketplace/$", MarketplaceConsumer.as_asgi()),
]
