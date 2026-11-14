import smtplib
from datetime import date, timedelta
from unittest.mock import patch
from urllib.parse import quote
import uuid

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import ModeGardeForm
from .models import (
    BienEtre,
    Enfant,
    ModeGarde,
    Temperature,
)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="notifications@toukpedio.test",
    MODE_GARDE_TOKEN_VALIDITY_DAYS=7,
)
class ModeGardeEmailTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="mode_garde_parent",
            first_name="Parent",
            last_name="Test",
            email="parent@example.com",
            password="mode-garde-test-password",
        )
        self.enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Enfant",
            prenom="Awa",
            date_naissance=date(2022, 6, 15),
            sexe="F",
            allergies="Arachides",
            traitement="Traitement autorisé",
            antecedents="Antécédent sélectionné",
            telephone_parent="+237 600 000 000",
        )
        self.client.force_login(self.parent)
        self.url_creation = reverse(
            "sante:creer_mode_garde",
            args=[self.enfant.pk],
        )

    def form_data(self, **overrides):
        data = {
            "nom_gardien": "Marie Gardienne",
            "email_gardien": "gardienne@example.com",
            "telephone_gardien": "",
            "type_gardien": "autre",
            "date_debut": timezone.localdate().isoformat(),
            "date_fin": (timezone.localdate() + timedelta(days=2)).isoformat(),
            "heure_debut": "08:30",
            "heure_fin": "17:15",
            "partager_allergies": "on",
            "partager_traitement": "on",
            "partager_alimentation": "on",
            "partager_sommeil": "on",
            "partager_hydratation": "on",
            "partager_antecedents": "on",
            "partager_vaccinations": "on",
            "partager_consultations": "on",
            "partager_temperature": "on",
            "partager_contact_parent": "on",
            "consignes": "Appeler le parent en cas de besoin.",
            "contact_urgence": "+237 699 000 000",
        }
        data.update(overrides)
        return data

    def test_form_validates_email_and_keeps_existing_share_fields(self):
        form = ModeGardeForm(self.form_data())

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn("email_gardien", form.fields)
        self.assertIn("heure_debut", form.fields)
        self.assertIn("partager_hydratation", form.fields)
        self.assertIn("partager_temperature", form.fields)

        invalid_form = ModeGardeForm(
            self.form_data(email_gardien="not-an-email")
        )
        self.assertFalse(invalid_form.is_valid())
        self.assertIn("email_gardien", invalid_form.errors)

    def test_creation_saves_guardian_and_sends_expiring_personal_link(self):
        response = self.client.post(
            self.url_creation,
            self.form_data(),
            follow=True,
        )

        mode_garde = ModeGarde.objects.get(enfant=self.enfant)
        self.assertRedirects(
            response,
            reverse(
                "sante:mode_garde_detail",
                args=[self.enfant.pk, mode_garde.pk],
            ),
        )
        self.assertEqual(mode_garde.nom_gardien, "Marie Gardienne")
        self.assertEqual(mode_garde.email_gardien, "gardienne@example.com")
        self.assertEqual(mode_garde.telephone_gardien, "")
        self.assertEqual(mode_garde.heure_debut.strftime("%H:%M"), "08:30")
        self.assertEqual(mode_garde.heure_fin.strftime("%H:%M"), "17:15")
        self.assertGreater(
            mode_garde.token_expires_at,
            timezone.now() + timedelta(days=6, hours=23),
        )
        self.assertLess(
            mode_garde.token_expires_at,
            timezone.now() + timedelta(days=7, minutes=1),
        )
        self.assertEqual(len(mail.outbox), 1)
        outgoing = mail.outbox[0]
        self.assertEqual(
            outgoing.subject,
            "Informations de garde de votre enfant — TOUKPEDIO",
        )
        self.assertEqual(outgoing.to, ["gardienne@example.com"])
        public_url = reverse(
            "sante:consulter_mode_garde",
            kwargs={"token": mode_garde.token},
        )
        self.assertIn(public_url, outgoing.body)
        self.assertIn("Awa Enfant", outgoing.body)
        self.assertIn("Parent Test", outgoing.body)
        self.assertTrue(outgoing.alternatives)
        self.assertIn("Consulter la fiche de garde", outgoing.alternatives[0][0])
        self.assertContains(response, "fiche de garde a été enregistrée et envoyée")

    def test_invalid_email_does_not_create_or_send(self):
        response = self.client.post(
            self.url_creation,
            self.form_data(email_gardien="adresse-invalide"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email_gardien")
        self.assertFalse(ModeGarde.objects.filter(enfant=self.enfant).exists())
        self.assertEqual(mail.outbox, [])

    @patch(
        "sante.views.send_mail",
        side_effect=smtplib.SMTPException("SMTP unavailable"),
    )
    def test_smtp_failure_keeps_saved_record_and_reports_error(self, mocked_send):
        with self.assertLogs("sante.views", level="ERROR"):
            response = self.client.post(
                self.url_creation,
                self.form_data(),
                follow=True,
            )

        self.assertEqual(ModeGarde.objects.filter(enfant=self.enfant).count(), 1)
        self.assertContains(response, "La fiche a été enregistrée")
        self.assertContains(response, "l'e-mail n'a pas pu être envoyé")
        self.assertNotContains(response, "fiche de garde a été enregistrée et envoyée")
        mocked_send.assert_called_once()

    def test_valid_token_reads_selected_information_only_and_is_read_only(self):
        response = self.client.post(self.url_creation, self.form_data())
        mode_garde = ModeGarde.objects.get(enfant=self.enfant)
        BienEtre.objects.create(
            enfant=self.enfant,
            date_suivi=timezone.localdate(),
            humeur="bonne",
            sommeil="bon",
            alimentation="Repas du midi préparé",
            hydratation="Proposer de l'eau",
        )
        Temperature.objects.create(
            enfant=self.enfant,
            valeur="37.2",
            observation="Température stable",
        )
        public_url = reverse(
            "sante:consulter_mode_garde",
            kwargs={"token": mode_garde.token},
        )
        autre_enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Autre",
            prenom="Dossier",
            date_naissance=date(2021, 3, 2),
            sexe="M",
            allergies="Information non partagée",
        )
        ModeGarde.objects.create(
            enfant=autre_enfant,
            parent=self.parent,
            nom_gardien="Autre gardien",
            email_gardien="autre@example.com",
            type_gardien="autre",
            date_debut=timezone.localdate(),
            date_fin=timezone.localdate() + timedelta(days=2),
        )

        self.client.logout()
        public_response = self.client.get(public_url)

        self.assertEqual(public_response.status_code, 200)
        self.assertContains(public_response, "Awa Enfant")
        self.assertContains(public_response, "08:30")
        self.assertContains(public_response, "17:15")
        self.assertContains(public_response, "Arachides")
        self.assertContains(public_response, "Traitement autorisé")
        self.assertContains(public_response, "Repas du midi préparé")
        self.assertContains(public_response, "Proposer de l&#x27;eau")
        self.assertContains(public_response, "37.2")
        self.assertNotContains(public_response, "Motif de consultation")
        self.assertNotContains(public_response, "Information non partagée")
        self.assertEqual(
            public_url,
            f"/mode-garde/consulter/{mode_garde.token}/",
        )

        post_response = self.client.post(public_url, {"consignes": "modifié"})
        self.assertEqual(post_response.status_code, 405)
        mode_garde.refresh_from_db()
        self.assertEqual(mode_garde.consignes, "Appeler le parent en cas de besoin.")

    def test_invalid_expired_and_revoked_tokens_are_denied(self):
        self.client.post(self.url_creation, self.form_data())
        mode_garde = ModeGarde.objects.get(enfant=self.enfant)
        public_url = reverse(
            "sante:consulter_mode_garde",
            kwargs={"token": mode_garde.token},
        )
        self.client.logout()

        invalid = self.client.get(
            reverse(
                "sante:consulter_mode_garde",
                kwargs={"token": uuid.uuid4()},
            )
        )
        self.assertEqual(invalid.status_code, 404)
        self.assertContains(invalid, "Lien de consultation indisponible", status_code=404)
        malformed = self.client.get(
            reverse(
                "sante:consulter_mode_garde",
                kwargs={"token": "token-invalide"},
            )
        )
        self.assertEqual(malformed.status_code, 404)
        self.assertContains(
            malformed,
            "Lien de consultation indisponible",
            status_code=404,
        )

        mode_garde.token_expires_at = timezone.now() - timedelta(seconds=1)
        mode_garde.save(update_fields=["token_expires_at"])
        expired = self.client.get(public_url)
        self.assertEqual(expired.status_code, 410)
        self.assertContains(expired, "a expiré", status_code=410)

        mode_garde.token_expires_at = timezone.now() + timedelta(days=1)
        mode_garde.token_revoked_at = timezone.now()
        mode_garde.save(update_fields=["token_expires_at", "token_revoked_at"])
        revoked = self.client.get(public_url)
        self.assertEqual(revoked.status_code, 404)

    def test_only_owner_can_revoke_public_token(self):
        self.client.post(self.url_creation, self.form_data())
        mode_garde = ModeGarde.objects.get(enfant=self.enfant)
        revoke_url = reverse(
            "sante:revoquer_lien_mode_garde",
            args=[self.enfant.pk, mode_garde.pk],
        )
        public_url = reverse(
            "sante:consulter_mode_garde",
            kwargs={"token": mode_garde.token},
        )
        other_parent = User.objects.create_user(
            username="other_parent",
            password="other-test-password",
        )

        self.client.logout()
        self.client.force_login(other_parent)
        self.assertEqual(self.client.post(revoke_url).status_code, 404)

        self.client.logout()
        self.client.force_login(self.parent)
        self.assertEqual(self.client.get(revoke_url).status_code, 405)
        self.assertRedirects(self.client.post(revoke_url), reverse(
            "sante:mode_garde_detail",
            args=[self.enfant.pk, mode_garde.pk],
        ))
        mode_garde.refresh_from_db()
        self.assertIsNotNone(mode_garde.token_revoked_at)

        self.client.logout()
        self.assertEqual(self.client.get(public_url).status_code, 404)

    def test_sms_view_renders_encoded_sms_link_without_redirecting(self):
        mode_garde = ModeGarde.objects.create(
            enfant=self.enfant,
            parent=self.parent,
            nom_gardien="Marie Gardienne",
            email_gardien="gardienne@example.com",
            telephone_gardien="+237 655 123 456",
            type_gardien="autre",
            date_debut=timezone.localdate(),
            date_fin=timezone.localdate() + timedelta(days=2),
        )
        url = reverse(
            "sante:mode_garde_sms",
            args=[self.enfant.pk, mode_garde.pk],
        )

        response = self.client.get(url)

        lien_fiche = "http://testserver" + reverse(
            "sante:consulter_mode_garde",
            kwargs={"token": mode_garde.token},
        )
        message = (
            f"Fiche de garde de {self.enfant.prenom}. "
            f"Valable du {mode_garde.date_debut.strftime('%d/%m/%Y')} "
            f"au {mode_garde.date_fin.strftime('%d/%m/%Y')}. "
            f"Consulter : {lien_fiche}"
        )
        expected_sms_url = f"sms:237655123456?body={quote(message, safe='')}"

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sante/mode_garde_sms.html")
        self.assertEqual(response.context["sms_url"], expected_sms_url)
        self.assertContains(response, "Ouvrir mon application SMS")
        self.assertContains(response, expected_sms_url.replace("&", "&amp;"))
        self.assertNotIn("Location", response)

    def test_sms_view_still_requires_authorized_parent(self):
        mode_garde = ModeGarde.objects.create(
            enfant=self.enfant,
            parent=self.parent,
            nom_gardien="Marie Gardienne",
            email_gardien="gardienne@example.com",
            telephone_gardien="+237 655 123 456",
            type_gardien="autre",
            date_debut=timezone.localdate(),
            date_fin=timezone.localdate() + timedelta(days=2),
        )
        other_parent = User.objects.create_user(
            username="sms_other_parent",
            password="other-test-password",
        )
        self.client.force_login(other_parent)

        response = self.client.get(
            reverse(
                "sante:mode_garde_sms",
                args=[self.enfant.pk, mode_garde.pk],
            )
        )

        self.assertEqual(response.status_code, 404)


class ModeGardeDetailAccessTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="mode_detail_owner",
            password="mode-detail-owner-password",
        )
        self.enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Dossier",
            prenom="Mode",
            date_naissance=date(2022, 1, 1),
            sexe="F",
        )
        self.mode_garde = ModeGarde.objects.create(
            enfant=self.enfant,
            parent=self.parent,
            nom_gardien="Gardien de test",
            type_gardien="autre",
            date_debut=timezone.localdate(),
            date_fin=timezone.localdate() + timedelta(days=1),
        )
        self.detail_url = reverse(
            "sante:mode_garde_detail",
            args=[self.enfant.pk, self.mode_garde.pk],
        )

    def test_owner_can_open_existing_mode_garde(self):
        self.client.force_login(self.parent)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["mode_garde"], self.mode_garde)

    def test_nonexistent_mode_garde_renders_clean_404_page(self):
        self.client.force_login(self.parent)
        url = reverse(
            "sante:mode_garde_detail",
            args=[self.enfant.pk, self.mode_garde.pk + 1000],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "sante/mode_garde_404.html")
        self.assertContains(response, "Fiche de garde introuvable", status_code=404)

    def test_mode_garde_associated_with_another_child_returns_clean_404(self):
        other_enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Autre",
            prenom="Enfant",
            date_naissance=date(2021, 1, 1),
            sexe="M",
        )
        self.client.force_login(self.parent)
        url = reverse(
            "sante:mode_garde_detail",
            args=[other_enfant.pk, self.mode_garde.pk],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "sante/mode_garde_404.html")

    def test_non_owner_cannot_open_mode_garde(self):
        other_parent = User.objects.create_user(
            username="mode_detail_other",
            password="mode-detail-other-password",
        )
        self.client.force_login(other_parent)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "sante/mode_garde_404.html")

    def test_admin_link_uses_real_child_and_mode_ids_and_admin_can_open(self):
        admin = User.objects.create_superuser(
            username="mode_detail_admin",
            email="admin@example.com",
            password="mode-detail-admin-password",
        )
        self.client.force_login(admin)
        admin_child_url = reverse(
            "sante:administration_enfant_detail",
            args=[self.enfant.pk],
        )

        response = self.client.get(admin_child_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.detail_url)

        detail_response = self.client.get(self.detail_url)

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(
            detail_response.context["mode_garde"].pk,
            self.mode_garde.pk,
        )
