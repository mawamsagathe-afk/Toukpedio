import asyncio

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Conversation, Message


User = get_user_model()


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"sante_conversation_{self.conversation_id}"
        self.joined = False

        if not self.user.is_authenticated or not await self._a_conversation_accessible():
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        self.joined = True
        await self.accept()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence.update",
                "user_id": self.user.pk,
                "online": True,
            },
        )
        read_ids = await self._diffuser_messages_lus()
        if read_ids:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "messages.read",
                    "message_ids": read_ids,
                    "reader_id": self.user.pk,
                },
            )
            await self._notifier_compteur_non_lus()

    async def disconnect(self, close_code):
        if getattr(self, "joined", False):
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence.update",
                    "user_id": self.user.pk,
                    "online": False,
                },
            )
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if action == "send_message":
            text = content.get("text", "")
            if not isinstance(text, str) or not text.strip():
                await self.send_json({"type": "error", "message": "Écrivez un message."})
                return
            if len(text.strip()) > 4000:
                await self.send_json(
                    {"type": "error", "message": "Le message est limité à 4 000 caractères."}
                )
                return

            message = await self._creer_message(text.strip())
            if message is None:
                await self.send_json(
                    {"type": "error", "message": "Cette conversation est fermée."}
                )
                return

            await self.channel_layer.group_send(
                self.group_name,
                {"type": "message.created", "message": message},
            )
            await self.channel_layer.group_send(
                f"sante_messagerie_inbox_{message['recipient_id']}",
                {
                    "type": "inbox.notification",
                    "notification": {
                        "conversation_id": self.conversation_id,
                        "subject": message["subject"],
                        "child_name": message["child_name"],
                        "sender_name": message["sender_name"],
                        "text": message["text"],
                        "sent_at": message["sent_at"],
                        "unread_count": message["unread_count"],
                    },
                },
            )
        elif action == "mark_read":
            message_ids = content.get("message_ids", [])
            if not isinstance(message_ids, list):
                return
            read_ids = await self._marquer_messages_lus(message_ids)
            if read_ids:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "messages.read",
                        "message_ids": read_ids,
                        "reader_id": self.user.pk,
                    },
                )
                await self._notifier_compteur_non_lus()
        elif action == "presence_check":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence.probe",
                    "requester_id": self.user.pk,
                    "requester_channel": self.channel_name,
                },
            )

    async def message_created(self, event):
        await self.send_json({"type": "message", **event["message"]})

    async def messages_read(self, event):
        await self.send_json(
            {
                "type": "read",
                "message_ids": event["message_ids"],
                "reader_id": event["reader_id"],
            }
        )

    async def presence_update(self, event):
        if event["user_id"] != self.user.pk:
            await self.send_json(
                {
                    "type": "presence",
                    "user_id": event["user_id"],
                    "online": event["online"],
                }
            )

    async def presence_probe(self, event):
        if event["requester_id"] == self.user.pk:
            return
        await self.channel_layer.send(
            event["requester_channel"],
            {
                "type": "presence.result",
                "user_id": self.user.pk,
                "online": True,
            },
        )

    async def presence_result(self, event):
        await self.send_json(
            {
                "type": "presence",
                "user_id": event["user_id"],
                "online": event["online"],
            }
        )

    @database_sync_to_async
    def _a_conversation_accessible(self):
        return Conversation.objects.filter(
            Q(parent=self.user) | Q(professionnel=self.user),
            pk=self.conversation_id,
            parent__is_active=True,
            professionnel__is_active=True,
        ).exists()

    @database_sync_to_async
    def _creer_message(self, text):
        conversation = (
            Conversation.objects
            .filter(
                Q(parent=self.user) | Q(professionnel=self.user),
                pk=self.conversation_id,
                ouverte=True,
            )
            .first()
        )
        if conversation is None:
            return None

        message = Message.objects.create(
            conversation=conversation,
            expediteur=self.user,
            texte=text,
        )
        conversation.dernier_message_le = message.envoye_le
        conversation.save(update_fields=["dernier_message_le", "mise_a_jour"])
        return {
            "id": message.pk,
            "text": message.texte,
            "sender_id": self.user.pk,
            "sender_name": self.user.get_full_name() or self.user.username,
            "sent_at": message.envoye_le.isoformat(),
            "read_at": None,
            "recipient_id": (
                conversation.professionnel_id
                if self.user.pk == conversation.parent_id
                else conversation.parent_id
            ),
            "subject": conversation.sujet,
            "child_name": conversation.enfant.prenom if conversation.enfant else "",
            "unread_count": (
                Message.objects.filter(
                    conversation=conversation,
                    lu_le__isnull=True,
                    expediteur=self.user,
                )
                .count()
            ),
        }

    @database_sync_to_async
    def _marquer_messages_lus(self, message_ids):
        ids = [
            message_id
            for message_id in message_ids[:100]
            if isinstance(message_id, int)
        ]
        unread = Message.objects.filter(
            conversation_id=self.conversation_id,
            pk__in=ids,
            lu_le__isnull=True,
        ).exclude(expediteur=self.user)
        read_ids = list(unread.values_list("pk", flat=True))
        if read_ids:
            unread.update(lu_le=timezone.now())
        return read_ids

    @database_sync_to_async
    def _diffuser_messages_lus(self):
        unread = Message.objects.filter(
            conversation_id=self.conversation_id,
            lu_le__isnull=True,
        ).exclude(expediteur=self.user)
        read_ids = list(unread.values_list("pk", flat=True))
        if read_ids:
            unread.update(lu_le=timezone.now())
        return read_ids

    @database_sync_to_async
    def _compteurs_non_lus(self):
        conversation = Conversation.objects.get(pk=self.conversation_id)
        autre_id = (
            conversation.professionnel_id
            if self.user.pk == conversation.parent_id
            else conversation.parent_id
        )
        non_lus_utilisateur = Message.objects.filter(
            conversation_id=self.conversation_id,
            lu_le__isnull=True,
        ).exclude(expediteur=self.user).count()
        non_lus_autre = Message.objects.filter(
            conversation_id=self.conversation_id,
            lu_le__isnull=True,
            expediteur=self.user,
        ).count()
        return autre_id, non_lus_utilisateur, non_lus_autre

    async def _notifier_compteur_non_lus(self):
        autre_id, non_lus_utilisateur, non_lus_autre = (
            await self._compteurs_non_lus()
        )
        await asyncio.gather(
            self.channel_layer.group_send(
                f"sante_messagerie_inbox_{self.user.pk}",
                {
                    "type": "inbox.read_update",
                    "conversation_id": self.conversation_id,
                    "unread_count": non_lus_utilisateur,
                },
            ),
            self.channel_layer.group_send(
                f"sante_messagerie_inbox_{autre_id}",
                {
                    "type": "inbox.read_update",
                    "conversation_id": self.conversation_id,
                    "unread_count": non_lus_autre,
                },
            ),
        )


class InboxConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close(code=4403)
            return

        self.group_name = f"sante_messagerie_inbox_{self.user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def inbox_notification(self, event):
        await self.send_json(
            {
                "type": "conversation_update",
                **event["notification"],
            }
        )

    async def inbox_read_update(self, event):
        await self.send_json(
            {
                "type": "unread_count",
                "conversation_id": event["conversation_id"],
                "unread_count": event["unread_count"],
            }
        )
