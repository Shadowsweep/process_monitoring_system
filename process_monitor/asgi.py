"""
ASGI config for process_monitor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
# Importing with a delay

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'process_monitor.settings')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import routing AFTER Django setup
import monitor_app.routing  

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            monitor_app.routing.websocket_urlpatterns
        )
    ),
})