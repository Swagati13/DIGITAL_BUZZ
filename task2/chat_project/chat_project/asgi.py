"""
ASGI config for chat_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

# application = get_asgi_application()
# chat_project/asgi.py
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_project.settings")

# Initialize Django BEFORE importing anything that uses models
django.setup()

from chat.sio_app import sio_app  # now safe to import
from socketio import ASGIApp

django_asgi_app = get_asgi_application()

# Mount Socket.IO + Django ASGI together
application = ASGIApp(sio_app, django_asgi_app)
