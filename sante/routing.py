from django.urls import path

from .consumers import ConversationConsumer, InboxConsumer


websocket_urlpatterns = [
    path(
        "ws/messagerie/inbox/",
        InboxConsumer.as_asgi(),
    ),
    path(
        "ws/messagerie/<int:conversation_id>/",
        ConversationConsumer.as_asgi(),
    ),
]
