from django.urls import re_path

from .consumers import AdminConsumer, DriverConsumer, TrackingConsumer

websocket_urlpatterns = [
    re_path(r"^ws/driver/$", DriverConsumer.as_asgi()),
    re_path(r"^ws/tracking/(?P<delivery_id>\d+)/$", TrackingConsumer.as_asgi()),
    re_path(r"^ws/admin/$", AdminConsumer.as_asgi()),
]
