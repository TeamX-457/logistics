import os

from dotenv import load_dotenv

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistica_tracking.settings.local')

django_asgi_app = get_asgi_application()

from tracking.routing import websocket_urlpatterns  # noqa: E402
from tracking.ws_auth import JWTAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
