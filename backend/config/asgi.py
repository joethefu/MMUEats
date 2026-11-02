"""
ASGI config for the MMUEats backend.

Routes plain HTTP to Django as normal, and WebSocket connections
(ws/notifications/) through Channels with JWT auth middleware, per spec §40:
real-time order status updates over WebSockets.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

# Import after Django apps are loaded (django_asgi_app above forces app loading),
# since these modules import models.
from notifications.middleware import JWTAuthMiddleware  # noqa: E402
from notifications.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
