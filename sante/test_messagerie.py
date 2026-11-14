import asyncio
from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from .models import Conversation, Enfant, Message, Parent
from .consumers import InboxConsumer
from .routing import websocket_urlpatterns


class MessagerieViewTests(TestCase):
    def setUp(self):
        self.parent_user = User.objects.create_user(
            username="parent_chat",
            password="test-password-123",
        )
        Parent.objects.create(user=self.parent_user)
        self.professionnel = User.objects.create_user(
            username="soignant_chat",
            password="test-password-123",
            is_staff=True,
        )
        self.enfant = Enfant.objects.create(
            parent=self.parent_user,
            nom="Test",
            prenom="Enfant",
            date_naissance="2020-01-01",
            sexe="F",
        )
        self.client.force_login(self.parent_user)

    def test_parent_can_create_conversation_and_initial_message(self):
        response = self.client.post(
            reverse("sante:nouvelle_conversation"),
            {
                "professionnel": self.professionnel.pk,
                "enfant": self.enfant.pk,
                "sujet": "Question santé",
                "message": "Bonjour, je souhaite un conseil.",
            },
        )

        conversation = Conversation.objects.get()
        self.assertRedirects(
            response,
            reverse("sante:conversation_detail", args=[conversation.pk]),
        )
        self.assertEqual(conversation.parent, self.parent_user)
        self.assertEqual(conversation.professionnel, self.professionnel)
        self.assertEqual(conversation.enfant, self.enfant)
        self.assertEqual(conversation.messages.get().texte, "Bonjour, je souhaite un conseil.")

    def test_new_conversation_notifies_professional_inbox(self):
        channel_layer = type("ChannelLayerStub", (), {})()
        channel_layer.group_send = AsyncMock()
        with (
            patch("sante.views.get_channel_layer", return_value=channel_layer),
            patch(
                "sante.views.async_to_sync",
                side_effect=lambda async_function: async_to_sync(async_function),
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(
                reverse("sante:nouvelle_conversation"),
                {
                    "professionnel": self.professionnel.pk,
                    "enfant": self.enfant.pk,
                    "sujet": "Question santé",
                    "message": "Bonjour",
                },
            )

        self.assertEqual(response.status_code, 302)
        channel_layer.group_send.assert_awaited_once()
        group_name, event = channel_layer.group_send.await_args.args
        self.assertEqual(
            group_name,
            f"sante_messagerie_inbox_{self.professionnel.pk}",
        )
        self.assertEqual(event["notification"]["text"], "Bonjour")

    def test_parent_cannot_start_conversation_with_unavailable_user(self):
        ordinary_user = User.objects.create_user(
            username="ordinary_user",
            password="test-password-123",
        )
        response = self.client.post(
            reverse("sante:nouvelle_conversation"),
            {
                "professionnel": ordinary_user.pk,
                "sujet": "Question santé",
                "message": "Bonjour",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Conversation.objects.exists())

    def test_parent_and_assigned_professional_can_view_but_other_staff_cannot(self):
        conversation = Conversation.objects.create(
            parent=self.parent_user,
            professionnel=self.professionnel,
            sujet="Question santé",
        )
        self.client.force_login(self.professionnel)
        self.assertEqual(
            self.client.get(
                reverse("sante:conversation_detail", args=[conversation.pk])
            ).status_code,
            200,
        )

        other_staff = User.objects.create_user(
            username="other_staff",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_login(other_staff)
        self.assertEqual(
            self.client.get(
                reverse("sante:conversation_detail", args=[conversation.pk])
            ).status_code,
            404,
        )

    def test_opening_conversation_marks_incoming_messages_as_read(self):
        conversation = Conversation.objects.create(
            parent=self.parent_user,
            professionnel=self.professionnel,
            sujet="Question santé",
        )
        message = Message.objects.create(
            conversation=conversation,
            expediteur=self.professionnel,
            texte="Bonjour",
        )

        response = self.client.get(
            reverse("sante:conversation_detail", args=[conversation.pk])
        )

        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertIsNotNone(message.lu_le)

    def test_inbox_displays_unread_message_count_to_participant(self):
        conversation = Conversation.objects.create(
            parent=self.parent_user,
            professionnel=self.professionnel,
            sujet="Question santé",
        )
        Message.objects.create(
            conversation=conversation,
            expediteur=self.professionnel,
            texte="Réponse",
        )

        response = self.client.get(reverse("sante:messagerie"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["conversations"][0].non_lus, 1)


@override_settings(
    CHANNEL_LAYERS={
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
)
class MessagerieWebsocketTests(TransactionTestCase):
    def setUp(self):
        self.parent_user = User.objects.create_user(
            username="parent_ws",
            password="test-password-123",
        )
        self.professionnel = User.objects.create_user(
            username="pro_ws",
            password="test-password-123",
            is_staff=True,
        )
        self.autre_parent = User.objects.create_user(
            username="other_parent_ws",
            password="test-password-123",
        )
        self.conversation = Conversation.objects.create(
            parent=self.parent_user,
            professionnel=self.professionnel,
            sujet="Suivi enfant",
        )
        self.application = URLRouter(websocket_urlpatterns)

    def _communicator(self, user, conversation_id=None):
        communicator = WebsocketCommunicator(
            self.application,
            f"/ws/messagerie/{conversation_id or self.conversation.pk}/",
        )
        communicator.scope["user"] = user
        return communicator

    async def _receive_type(self, communicator, expected_type):
        while True:
            event = await asyncio.wait_for(
                communicator.receive_json_from(),
                timeout=2,
            )
            if event.get("type") == expected_type:
                return event

    async def test_messages_are_broadcast_and_saved_for_both_participants(self):
        parent_socket = self._communicator(self.parent_user)
        professional_socket = self._communicator(self.professionnel)
        parent_connected, _ = await parent_socket.connect()
        professional_connected, _ = await professional_socket.connect()
        self.assertTrue(parent_connected)
        self.assertTrue(professional_connected)

        presence_event = await self._receive_type(parent_socket, "presence")
        self.assertEqual(presence_event["user_id"], self.professionnel.pk)
        self.assertTrue(presence_event["online"])

        await parent_socket.send_json_to(
            {"action": "send_message", "text": "Bonjour, voici une question."}
        )
        parent_event, professional_event = await asyncio.gather(
            self._receive_type(parent_socket, "message"),
            self._receive_type(professional_socket, "message"),
        )

        self.assertEqual(parent_event["text"], "Bonjour, voici une question.")
        self.assertEqual(professional_event["sender_id"], self.parent_user.pk)
        saved = await database_sync_to_async(
            lambda: Message.objects.get(conversation=self.conversation)
        )()
        self.assertEqual(saved.texte, "Bonjour, voici une question.")

        await professional_socket.send_json_to(
            {"action": "mark_read", "message_ids": [professional_event["id"]]}
        )
        read_event = await self._receive_type(parent_socket, "read")
        self.assertEqual(read_event["message_ids"], [professional_event["id"]])
        updated_message = await database_sync_to_async(
            lambda: Message.objects.get(pk=professional_event["id"])
        )()
        self.assertIsNotNone(updated_message.lu_le)

        await parent_socket.disconnect()
        await professional_socket.disconnect()

    async def test_unrelated_user_is_denied_websocket_access(self):
        communicator = self._communicator(self.autre_parent)
        connected, close_code = await communicator.connect()

        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_professional_inbox_receives_live_message_notification(self):
        inbox_socket = WebsocketCommunicator(
            InboxConsumer.as_asgi(),
            "/ws/messagerie/inbox/",
        )
        inbox_socket.scope["user"] = self.professionnel
        parent_socket = self._communicator(self.parent_user)
        inbox_connected, _ = await inbox_socket.connect()
        parent_connected, _ = await parent_socket.connect()
        self.assertTrue(inbox_connected)
        self.assertTrue(parent_connected)

        await parent_socket.send_json_to(
            {"action": "send_message", "text": "Message entrant en direct"}
        )
        notification = await self._receive_type(
            inbox_socket,
            "conversation_update",
        )

        self.assertEqual(notification["conversation_id"], self.conversation.pk)
        self.assertEqual(notification["text"], "Message entrant en direct")
        self.assertEqual(notification["unread_count"], 1)

        await inbox_socket.disconnect()
        await parent_socket.disconnect()

    async def test_read_receipt_updates_unread_counts_for_both_inboxes(self):
        parent_inbox = WebsocketCommunicator(
            InboxConsumer.as_asgi(),
            "/ws/messagerie/inbox/",
        )
        parent_inbox.scope["user"] = self.parent_user
        professional_inbox = WebsocketCommunicator(
            InboxConsumer.as_asgi(),
            "/ws/messagerie/inbox/",
        )
        professional_inbox.scope["user"] = self.professionnel
        parent_socket = self._communicator(self.parent_user)
        professional_socket = self._communicator(self.professionnel)

        communicators = (
            parent_inbox,
            professional_inbox,
            parent_socket,
            professional_socket,
        )
        for communicator in communicators:
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

        await professional_socket.send_json_to(
            {"action": "send_message", "text": "Conseil"}
        )
        message = await self._receive_type(parent_socket, "message")
        await self._receive_type(parent_inbox, "conversation_update")

        await parent_socket.send_json_to(
            {"action": "mark_read", "message_ids": [message["id"]]}
        )
        await self._receive_type(parent_socket, "read")
        parent_update = await self._receive_type(parent_inbox, "unread_count")
        professional_update = await self._receive_type(
            professional_inbox,
            "unread_count",
        )

        self.assertEqual(parent_update["unread_count"], 0)
        self.assertEqual(professional_update["unread_count"], 0)

        for communicator in communicators:
            await communicator.disconnect()
