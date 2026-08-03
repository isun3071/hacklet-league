import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hacklet.settings.dev")

# This is what gunicorn serves in production, via the uvicorn worker (see Dockerfile).
#
# Why ASGI: the Stage 4 AI proxy streams model output to the player over SSE, and a streamed
# response occupies its worker for the whole generation. On sync WSGI workers a handful of
# concurrent players would exhaust the pool and block every other request on the box. Async
# request handling is the point; there is no Channels and no WebSocket layer.
#
# Django runs the existing sync views in a threadpool under ASGI, so nothing else changes.
application = get_asgi_application()
