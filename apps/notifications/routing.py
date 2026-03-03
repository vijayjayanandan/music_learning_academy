from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/notifications/<str:academy_slug>/", consumers.NotificationConsumer.as_asgi()),
]
