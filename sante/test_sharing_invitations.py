import smtplib
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Enfant, PartageEnfant


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="notifications@toukpedio.test",
)
class PartageInvitationTests(TestCase):
    def setUp(self):
        self.parent_a = User.objects.create_user(
            username="parent_a",
            email="parent-a@example.com",
            password="test-password-a",
        )
        self.parent_b = User.objects.create_user(
            username="parent_b",
            email="parent-b@example.com",
            password="test-password-b",
        )
        self.autre_parent = User.objects.create_user(
            username="autre_parent",
            email="autre@example.com",
            password="test-password-other",
        )
        self.enfant = Enfant.objects.create(
            parent=self.parent_a,
            nom="Enfant",
            prenom="Partage",
            date_naissance=date(2024, 1, 1),
            sexe="F",
        )
        self.url_invitation = reverse(
            "sante:inviter_parent",
            args=[self.enfant.pk],
        )

    def inviter_parent_b(self):
        self.client.force_login(self.parent_a)
        return self.client.post(
            self.url_invitation,
            {"email": "PARENT-B@EXAMPLE.COM"},
            follow=True,
        )

    def test_invitation_is_persisted_for_matching_recipient_and_emailed(self):
        response = self.inviter_parent_b()

        partage = PartageEnfant.objects.get()
        self.assertEqual(partage.enfant, self.enfant)
        self.assertEqual(partage.parent, self.parent_b)
        self.assertFalse(partage.accepte)
        self.assertFalse(partage.refusee)
        self.assertContains(response, "Invitation envoyée à parent-b@example.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["parent-b@example.com"])
        self.assertIn("Connectez-vous", mail.outbox[0].body)
        self.assertNotIn("allerg", mail.outbox[0].body.lower())
        self.assertNotIn("vaccin", mail.outbox[0].body.lower())

    def test_admin_created_invitation_uses_same_email_notification(self):
        admin_user = User.objects.create_user(
            username="share_admin",
            email="admin@example.com",
            password="test-password-admin",
            is_staff=True,
        )
        self.client.force_login(admin_user)
        response = self.client.post(
            reverse(
                "sante:administration_ajouter_partage",
                args=[self.enfant.pk],
            ),
            {"email": self.parent_b.email},
            follow=True,
        )

        self.assertTrue(
            PartageEnfant.objects.filter(
                enfant=self.enfant,
                parent=self.parent_b,
                accepte=False,
                refusee=False,
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.parent_b.email])
        self.assertContains(response, f"Invitation envoyée à {self.parent_b.email}")

    def test_pending_invitation_is_visible_after_recipient_logs_in(self):
        self.inviter_parent_b()

        self.client.logout()
        self.client.force_login(self.parent_b)
        response = self.client.get(reverse("sante:tableau_bord_parent"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["invitations_en_attente"]),
            list(PartageEnfant.objects.all()),
        )
        self.assertContains(response, "Invitations de partage en attente")
        self.assertContains(response, "Partage Enfant")
        partage = PartageEnfant.objects.get()
        self.assertContains(
            response,
            reverse("sante:accepter_partage", args=[partage.pk]),
        )
        self.assertContains(
            response,
            reverse("sante:refuser_partage", args=[partage.pk]),
        )

    @patch("sante.views.send_mail", side_effect=smtplib.SMTPException("SMTP indisponible"))
    def test_smtp_exception_keeps_invitation_pending_and_warns_inviter(self, mocked_send):
        self.client.force_login(self.parent_a)
        response = self.client.post(
            self.url_invitation,
            {"email": self.parent_b.email},
            follow=True,
        )

        partage = PartageEnfant.objects.get()
        self.assertFalse(partage.accepte)
        self.assertFalse(partage.refusee)
        self.assertTrue(
            any(
                "le courriel n'a pas pu être envoyé" in str(message)
                for message in response.context["messages"]
            )
        )
        self.assertNotContains(response, "Invitation envoyée à")
        mocked_send.assert_called_once()

    @patch("sante.views.send_mail", return_value=0)
    def test_unconfirmed_email_result_is_not_reported_as_sent(self, mocked_send):
        self.client.force_login(self.parent_a)
        response = self.client.post(
            self.url_invitation,
            {"email": self.parent_b.email},
            follow=True,
        )

        self.assertTrue(PartageEnfant.objects.filter(parent=self.parent_b).exists())
        self.assertTrue(
            any(
                "le serveur e-mail n'a pas confirmé l'envoi" in str(message)
                for message in response.context["messages"]
            )
        )
        self.assertNotContains(response, "Invitation envoyée à")
        mocked_send.assert_called_once()

    def test_only_invited_parent_can_accept_and_access_dossier_afterwards(self):
        self.inviter_parent_b()
        partage = PartageEnfant.objects.get()
        detail_url = reverse("sante:detail_enfant", args=[self.enfant.pk])
        accept_url = reverse("sante:accepter_partage", args=[partage.pk])

        self.client.logout()
        self.client.force_login(self.autre_parent)
        self.assertEqual(self.client.post(accept_url).status_code, 404)

        self.client.logout()
        self.client.force_login(self.parent_b)
        self.assertEqual(self.client.get(accept_url).status_code, 405)
        self.assertRedirects(self.client.get(detail_url), reverse("sante:tableau_bord_parent"))

        response = self.client.post(accept_url)
        self.assertRedirects(response, reverse("sante:tableau_bord_parent"))
        partage.refresh_from_db()
        self.assertTrue(partage.accepte)
        self.assertEqual(self.client.get(detail_url).status_code, 200)

    def test_share_acceptance_message_escapes_child_name(self):
        self.enfant.prenom = "<script>alert(1)</script>"
        self.enfant.save(update_fields=["prenom"])
        partage = PartageEnfant.objects.create(
            enfant=self.enfant,
            parent=self.parent_b,
        )
        self.client.force_login(self.parent_b)

        response = self.client.post(
            reverse("sante:accepter_partage", args=[partage.pk]),
            follow=True,
        )

        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_only_invited_parent_can_refuse_pending_invitation(self):
        self.inviter_parent_b()
        partage = PartageEnfant.objects.get()
        refuse_url = reverse("sante:refuser_partage", args=[partage.pk])

        self.client.logout()
        self.client.force_login(self.autre_parent)
        self.assertEqual(self.client.post(refuse_url).status_code, 404)

        self.client.logout()
        self.client.force_login(self.parent_b)
        self.assertEqual(self.client.get(refuse_url).status_code, 405)
        response = self.client.post(refuse_url)

        self.assertRedirects(response, reverse("sante:tableau_bord_parent"))
        partage.refresh_from_db()
        self.assertFalse(partage.accepte)
        self.assertTrue(partage.refusee)
        self.assertEqual(self.client.get(reverse("sante:detail_enfant", args=[self.enfant.pk])).status_code, 302)
        self.assertFalse(
            self.client.get(reverse("sante:tableau_bord_parent"))
            .context["invitations_en_attente"]
            .exists()
        )
