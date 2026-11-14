import json
import os
import shutil
import tempfile
import zipfile
from datetime import date
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Conversation,
    Enfant,
    JournalSymptome,
    Message,
    PartageEnfant,
    PhotoSymptome,
)


class DossierEnfantActionsTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="parent",
            password="test-password",
        )
        self.autre_parent = User.objects.create_user(
            username="autre-parent",
            password="test-password",
        )
        self.enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Dupont",
            prenom="Alice",
            date_naissance=date(2022, 4, 5),
            sexe="F",
            allergies="Arachides",
        )
        self.export_url = reverse(
            "sante:exporter_dossier_enfant",
            args=[self.enfant.pk],
        )
        self.suppression_url = reverse(
            "sante:supprimer_dossier_enfant",
            args=[self.enfant.pk],
        )

    def test_owner_can_download_archive_with_dossier_data(self):
        JournalSymptome.objects.create(
            enfant=self.enfant,
            symptome="Toux",
            intensite="faible",
        )
        self.client.force_login(self.parent)

        response = self.client.get(self.export_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            dossier = json.loads(archive.read("dossier.json"))
        self.assertEqual(dossier["format"], "toukpedio-dossier-enfant-v1")
        self.assertEqual(
            dossier["donnees"]["enfant"][0]["fields"]["allergies"],
            "Arachides",
        )
        self.assertEqual(
            dossier["donnees"]["symptomes"][0]["fields"]["symptome"],
            "Toux",
        )

    def test_unrelated_parent_cannot_export_or_delete(self):
        self.client.force_login(self.autre_parent)

        self.assertEqual(self.client.get(self.export_url).status_code, 404)
        self.assertEqual(self.client.post(self.suppression_url).status_code, 404)
        self.assertTrue(Enfant.objects.filter(pk=self.enfant.pk).exists())

    def test_shared_parent_can_export_but_cannot_delete(self):
        PartageEnfant.objects.create(
            enfant=self.enfant,
            parent=self.autre_parent,
            accepte=True,
        )
        self.client.force_login(self.autre_parent)

        self.assertEqual(self.client.get(self.export_url).status_code, 200)
        self.assertEqual(self.client.post(self.suppression_url).status_code, 404)
        self.assertTrue(Enfant.objects.filter(pk=self.enfant.pk).exists())

    def test_export_only_includes_conversations_with_requesting_parent(self):
        PartageEnfant.objects.create(
            enfant=self.enfant,
            parent=self.autre_parent,
            accepte=True,
        )
        professionnel = User.objects.create_user(
            username="professionnel",
            password="test-password",
        )
        private_conversation = Conversation.objects.create(
            parent=self.parent,
            professionnel=professionnel,
            enfant=self.enfant,
            sujet="Échange privé",
        )
        shared_conversation = Conversation.objects.create(
            parent=self.autre_parent,
            professionnel=self.parent,
            enfant=self.enfant,
            sujet="Échange autorisé",
        )
        Message.objects.create(
            conversation=private_conversation,
            expediteur=self.parent,
            texte="Message privé",
        )
        Message.objects.create(
            conversation=shared_conversation,
            expediteur=self.autre_parent,
            texte="Message autorisé",
        )
        self.client.force_login(self.autre_parent)

        response = self.client.get(self.export_url)

        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            dossier = json.loads(archive.read("dossier.json"))
        conversations = dossier["donnees"]["conversations"]
        messages = dossier["donnees"]["messages"]
        self.assertEqual(
            [item["pk"] for item in conversations],
            [shared_conversation.pk],
        )
        self.assertEqual(
            [item["fields"]["texte"] for item in messages],
            ["Message autorisé"],
        )

    def test_owner_deletes_child_records_and_related_conversations(self):
        journal = JournalSymptome.objects.create(
            enfant=self.enfant,
            symptome="Toux",
            intensite="faible",
        )
        conversation = Conversation.objects.create(
            parent=self.parent,
            professionnel=self.autre_parent,
            enfant=self.enfant,
            sujet="Suivi médical",
        )
        Message.objects.create(
            conversation=conversation,
            expediteur=self.parent,
            texte="Message de suivi",
        )
        self.client.force_login(self.parent)

        response = self.client.post(self.suppression_url)

        self.assertRedirects(
            response,
            reverse("sante:tableau_bord_parent"),
        )
        self.assertFalse(Enfant.objects.filter(pk=self.enfant.pk).exists())
        self.assertFalse(JournalSymptome.objects.filter(pk=journal.pk).exists())
        self.assertFalse(Conversation.objects.filter(pk=conversation.pk).exists())
        self.assertFalse(Message.objects.filter(conversation=conversation).exists())

    def test_deletion_requires_post(self):
        self.client.force_login(self.parent)

        self.assertEqual(self.client.get(self.suppression_url).status_code, 405)
        self.assertTrue(Enfant.objects.filter(pk=self.enfant.pk).exists())

    def test_export_archive_includes_uploaded_child_and_symptom_photos(self):
        media_root = tempfile.mkdtemp(prefix="toukpedio-test-media-")
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            self.enfant.photo = SimpleUploadedFile(
                "portrait.jpg",
                b"portrait-data",
                content_type="image/jpeg",
            )
            self.enfant.save()
            journal = JournalSymptome.objects.create(
                enfant=self.enfant,
                symptome="Toux",
                intensite="faible",
            )
            photo = PhotoSymptome.objects.create(
                journal=journal,
                photo=SimpleUploadedFile(
                    "symptome.jpg",
                    b"symptom-data",
                    content_type="image/jpeg",
                ),
            )
            self.client.force_login(self.parent)

            response = self.client.get(self.export_url)

            self.assertEqual(response.status_code, 200)
            with zipfile.ZipFile(BytesIO(response.content)) as archive:
                dossier = json.loads(archive.read("dossier.json"))
                self.assertEqual(len(dossier["pieces_jointes"]), 2)
                for attachment, expected_data in zip(
                    dossier["pieces_jointes"],
                    (b"portrait-data", b"symptom-data"),
                ):
                    self.assertEqual(
                        archive.read(attachment["chemin_archive"]),
                        expected_data,
                    )
            self.assertTrue(self.enfant.photo.name)
            self.assertTrue(photo.photo.name)

    def test_deletion_also_removes_uploaded_photos(self):
        media_root = tempfile.mkdtemp(prefix="toukpedio-test-media-")
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            self.enfant.photo = SimpleUploadedFile(
                "portrait.jpg",
                b"portrait-data",
                content_type="image/jpeg",
            )
            self.enfant.save()
            journal = JournalSymptome.objects.create(
                enfant=self.enfant,
                symptome="Toux",
                intensite="faible",
            )
            photo = PhotoSymptome.objects.create(
                journal=journal,
                photo=SimpleUploadedFile(
                    "symptome.jpg",
                    b"symptom-data",
                    content_type="image/jpeg",
                ),
            )
            photo_names = (self.enfant.photo.name, photo.photo.name)
            self.client.force_login(self.parent)

            response = self.client.post(self.suppression_url)

            self.assertEqual(response.status_code, 302)
            self.assertTrue(
                all(
                    not os.path.exists(os.path.join(media_root, name))
                    for name in photo_names
                )
            )
