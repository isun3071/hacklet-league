import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hacklet.settings.dev")
# Plain Django ASGI for now. Channels (WebSockets) arrives in Stage 3.
application = get_asgi_application()
