from datetime import date, timedelta
import json
from unittest.mock import patch
from urllib.error import URLError

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Enfant, Vaccination, VaccinationRappel
from .reminders import send_due_vaccination_reminders, send_email_reminder
from .vaccination_calendar import (
    prochaine_vaccination_enfant,
    programmer_rappels_pour_vaccination,
)


class ParentContactViewsTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="parent_contacts",
            email="parent@example.com",
            password="Secure-test-password-123",
        )
        self.client.force_login(self.parent)

    def enfant_data(self, **overrides):
        data = {
            "nom": "Test",
            "prenom": "Enfant",
            "date_naissance": "2025-01-01",
            "sexe": "F",
            "email_parent": "nouveau@example.com",
            "telephone_parent": "+237 655 123 456",
            "adresse": "",
            "groupe_sanguin": "",
            "allergies": "",
            "traitement": "",
            "antecedents": "",
            "observations": "",
        }
        data.update(overrides)
        return data

    def test_add_form_displays_parent_contact_fields(self):
        response = self.client.get(reverse("sante:ajouter_enfant"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("email_parent", response.context["form"].fields)
        self.assertIn("telephone_parent", response.context["form"].fields)
        self.assertContains(response, 'name="email_parent"')
        self.assertContains(response, 'name="telephone_parent"')
        self.assertContains(response, "whatsapp_consent")

    def test_add_saves_parent_email_phone_and_consent(self):
        response = self.client.post(
            reverse("sante:ajouter_enfant"),
            self.enfant_data(whatsapp_consent="on"),
        )

        self.assertRedirects(response, reverse("sante:enfant"))
        enfant = Enfant.objects.get(parent=self.parent)
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.email, "nouveau@example.com")
        self.assertEqual(enfant.telephone_parent, "+237 655 123 456")
        self.assertTrue(enfant.whatsapp_consent)

    def test_add_rejects_invalid_email_and_phone(self):
        for invalid_data in (
            self.enfant_data(email_parent="not-an-email"),
            self.enfant_data(telephone_parent="+237 6ABC"),
        ):
            with self.subTest(invalid_data=invalid_data):
                response = self.client.post(
                    reverse("sante:ajouter_enfant"),
                    invalid_data,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Enfant.objects.count(), 0)

    def test_parent_can_update_contacts_for_owned_child(self):
        enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Test",
            prenom="Enfant",
            date_naissance=date(2025, 1, 1),
            sexe="F",
        )

        response = self.client.post(
            reverse("sante:modifier_enfant", args=[enfant.pk]),
            self.enfant_data(
                email_parent="updated@example.com",
                telephone_parent="+237 699 111 222",
                whatsapp_consent="on",
            ),
        )

        self.assertRedirects(
            response,
            reverse("sante:detail_enfant", args=[enfant.pk]),
        )
        enfant.refresh_from_db()
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.email, "updated@example.com")
        self.assertEqual(enfant.telephone_parent, "+237 699 111 222")
        self.assertTrue(enfant.whatsapp_consent)

    def test_parent_cannot_modify_another_parents_child(self):
        other_parent = User.objects.create_user(
            username="other_parent",
            password="Secure-test-password-456",
        )
        enfant = Enfant.objects.create(
            parent=other_parent,
            nom="Autre",
            prenom="Enfant",
            date_naissance=date(2025, 1, 1),
            sexe="M",
        )

        response = self.client.post(
            reverse("sante:modifier_enfant", args=[enfant.pk]),
            self.enfant_data(),
        )

        self.assertEqual(response.status_code, 404)
        enfant.refresh_from_db()
        self.assertEqual(enfant.telephone_parent, "")


class VaccinationReminderTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="reminder_parent",
            email="reminder@example.com",
            password="Secure-test-password-789",
        )
        self.enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Enfant",
            prenom="Test",
            date_naissance=date(2025, 1, 1),
            sexe="F",
            telephone_parent="+237 655 123 456",
            whatsapp_consent=True,
        )
        self.vaccination = Vaccination.objects.create(
            enfant=self.enfant,
            nom_vaccin="Vaccin de test",
            date_prevue=timezone.localdate() + timedelta(days=10),
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="test@toukpedio.local",
    )
    def test_email_reminder_sends_using_test_backend(self):
        reminder = VaccinationRappel.objects.create(
            vaccination=self.vaccination,
            canal="email",
            delai="J0",
            date_tentative=timezone.now(),
        )

        self.assertTrue(send_email_reminder(reminder))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reminder@example.com"])
        reminder.refresh_from_db()
        self.assertEqual(reminder.statut, "envoye")

    def test_scheduling_does_not_duplicate_reminder_deadlines(self):
        first = programmer_rappels_pour_vaccination(self.vaccination)
        second = programmer_rappels_pour_vaccination(self.vaccination)

        self.assertEqual(len(first), 6)
        self.assertEqual(len(second), 6)
        self.assertTrue(all(not item["created"] for item in second))
        self.assertEqual(
            VaccinationRappel.objects.filter(vaccination=self.vaccination).count(),
            6,
        )

    def test_combined_birth_vaccine_advances_to_first_six_week_vaccine(self):
        self.enfant.date_naissance = date(2026, 8, 29)
        self.enfant.save(update_fields=["date_naissance"])
        Vaccination.objects.create(
            enfant=self.enfant,
            nom_vaccin="BCG et Pollomyelite",
            dose="1er dose",
            date_prevue=date(2026, 9, 9),
            date_effectuee=date(2026, 9, 9),
        )

        prochain = prochaine_vaccination_enfant(self.enfant)

        self.assertEqual(prochain["nom_vaccin"], "DTCoq-HepB-Hib")
        self.assertEqual(prochain["dose"], "1ère dose")
        self.assertEqual(prochain["date_prevue"], date(2026, 10, 10))

    def test_saved_first_dose_with_ordinal_variant_advances_to_second_dose(self):
        self.enfant.date_naissance = date(2026, 8, 29)
        self.enfant.save(update_fields=["date_naissance"])
        Vaccination.objects.create(
            enfant=self.enfant,
            nom_vaccin="BCG et Pollomyelite",
            dose="1er dose",
            date_prevue=date(2026, 9, 9),
            date_effectuee=date(2026, 9, 9),
        )
        Vaccination.objects.create(
            enfant=self.enfant,
            nom_vaccin="DTCoq-HepB-Hib",
            dose="1er  dose",
            date_prevue=date(2026, 10, 10),
            date_effectuee=date(2026, 10, 10),
        )

        prochain = prochaine_vaccination_enfant(self.enfant)

        self.assertEqual(prochain["nom_vaccin"], "DTCoq-HepB-Hib")
        self.assertEqual(prochain["dose"], "2ème dose")
        self.assertEqual(prochain["date_prevue"], date(2026, 11, 7))

    def test_parent_add_updates_next_vaccine_immediately(self):
        self.enfant.date_naissance = date(2026, 8, 29)
        self.enfant.save(update_fields=["date_naissance"])
        self.client.force_login(self.parent)

        response = self.client.post(
            reverse("sante:ajouter_vaccination", args=[self.enfant.pk]),
            {
                "age": "Naissance",
                "nom_vaccin": "BCG et Pollomyelite",
                "dose": "1er dose",
                "date_prevue": "2026-09-09",
                "date_effectuee": "2026-09-09",
                "prochaine_dose": "",
                "observations": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("sante:vaccination", args=[self.enfant.pk]),
        )
        self.assertTrue(
            Vaccination.objects.filter(
                enfant=self.enfant,
                nom_vaccin="BCG et Pollomyelite",
                date_effectuee=date(2026, 9, 9),
            ).exists()
        )

        vaccination_response = self.client.get(
            reverse("sante:vaccination", args=[self.enfant.pk])
        )

        self.assertEqual(vaccination_response.status_code, 200)
        self.assertEqual(
            vaccination_response.context["prochaine_vaccination"]["nom_vaccin"],
            "DTCoq-HepB-Hib",
        )
        self.assertEqual(
            vaccination_response.context["prochaine_vaccination"]["date_prevue"],
            date(2026, 10, 10),
        )

    def test_planned_but_not_administered_vaccine_does_not_advance_calendar(self):
        self.enfant.date_naissance = date(2026, 8, 29)
        self.enfant.save(update_fields=["date_naissance"])
        Vaccination.objects.create(
            enfant=self.enfant,
            nom_vaccin="BCG et Pollomyelite",
            dose="1er dose",
            date_prevue=date(2026, 9, 9),
        )

        prochain = prochaine_vaccination_enfant(self.enfant)

        self.assertEqual(prochain["nom_vaccin"], "BCG")
        self.assertEqual(prochain["date_prevue"], date(2026, 8, 29))

    def test_parent_can_open_and_update_vaccination_form(self):
        self.client.force_login(self.parent)
        edit_url = reverse(
            "sante:modifier_vaccination",
            args=[self.enfant.pk, self.vaccination.pk],
        )

        get_response = self.client.get(edit_url)

        self.assertEqual(get_response.status_code, 200)
        self.assertTrue(get_response.context["modification"])
        self.assertEqual(
            get_response.context["form"].instance,
            self.vaccination,
        )
        self.assertContains(get_response, "Modifier une vaccination")

        post_response = self.client.post(
            edit_url,
            {
                "age": "10 semaines",
                "nom_vaccin": "Vaccin corrigé",
                "dose": "2ème dose",
                "date_prevue": "2025-03-15",
                "date_effectuee": "2025-03-15",
                "prochaine_dose": "",
                "observations": "Correction saisie par le parent",
            },
        )

        self.assertRedirects(
            post_response,
            reverse("sante:vaccination", args=[self.enfant.pk]),
        )
        self.vaccination.refresh_from_db()
        self.assertEqual(self.vaccination.nom_vaccin, "Vaccin corrigé")
        self.assertEqual(self.vaccination.date_effectuee, date(2025, 3, 15))
        self.assertEqual(
            self.vaccination.observations,
            "Correction saisie par le parent",
        )

    def test_vaccination_list_shows_edit_action(self):
        self.client.force_login(self.parent)

        response = self.client.get(
            reverse("sante:vaccination", args=[self.enfant.pk])
        )

        edit_url = reverse(
            "sante:modifier_vaccination",
            args=[self.enfant.pk, self.vaccination.pk],
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, edit_url)
        self.assertContains(response, "Modifier")

    def test_only_authorized_parent_can_edit_vaccination(self):
        other_parent = User.objects.create_user(
            username="reminder_other_parent",
            password="reminder-other-password",
        )
        self.client.force_login(other_parent)
        edit_url = reverse(
            "sante:modifier_vaccination",
            args=[self.enfant.pk, self.vaccination.pk],
        )

        response = self.client.post(
            edit_url,
            {"nom_vaccin": "Modification non autorisée"},
        )

        self.assertEqual(response.status_code, 404)
        self.vaccination.refresh_from_db()
        self.assertEqual(self.vaccination.nom_vaccin, "Vaccin de test")

    def test_edit_url_cannot_target_vaccination_of_another_child(self):
        self.client.force_login(self.parent)
        another_child = Enfant.objects.create(
            parent=self.parent,
            nom="Autre",
            prenom="Enfant",
            date_naissance=date(2024, 1, 1),
            sexe="M",
        )
        edit_url = reverse(
            "sante:modifier_vaccination",
            args=[another_child.pk, self.vaccination.pk],
        )

        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 404)

    @override_settings(
        WHATSAPP_TOKEN="test-token",
        WHATSAPP_PHONE_NUMBER_ID="test-number-id",
        WHATSAPP_TEMPLATE_NAME="approved_generic_reminder",
        WHATSAPP_TEMPLATE_LANGUAGE="fr",
    )
    @patch("sante.reminders.urllib_request.urlopen", side_effect=URLError("offline"))
    def test_whatsapp_api_failure_is_saved(self, mocked_urlopen):
        VaccinationRappel.objects.create(
            vaccination=self.vaccination,
            canal="whatsapp",
            delai="J0",
            date_tentative=timezone.now() - timedelta(minutes=1),
        )

        self.assertEqual(send_due_vaccination_reminders(), 0)
        reminder = VaccinationRappel.objects.get(
            vaccination=self.vaccination,
            canal="whatsapp",
        )
        self.assertEqual(reminder.statut, "echec")
        self.assertIn("offline", reminder.resultat)
        self.assertEqual(reminder.nombre_tentatives, 1)
        mocked_urlopen.assert_called_once()

    @override_settings(
        WHATSAPP_TOKEN="test-token",
        WHATSAPP_PHONE_NUMBER_ID="test-number-id",
        WHATSAPP_TEMPLATE_NAME="approved_generic_reminder",
        WHATSAPP_TEMPLATE_LANGUAGE="fr",
    )
    @patch("sante.reminders.urllib_request.urlopen")
    def test_whatsapp_without_acceptance_id_is_not_marked_sent(self, mocked_urlopen):
        mocked_urlopen.return_value.__enter__.return_value.read.return_value = b"{}"
        VaccinationRappel.objects.create(
            vaccination=self.vaccination,
            canal="whatsapp",
            delai="J0",
            date_tentative=timezone.now() - timedelta(minutes=1),
        )

        self.assertEqual(send_due_vaccination_reminders(), 0)
        reminder = VaccinationRappel.objects.get(
            vaccination=self.vaccination,
            canal="whatsapp",
        )
        self.assertEqual(reminder.statut, "echec")
        self.assertIn("n'a pas confirmé", reminder.resultat)
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["type"], "template")
        self.assertNotIn("Enfant", request.data.decode("utf-8"))

    @override_settings(
        WHATSAPP_TOKEN="test-token",
        WHATSAPP_PHONE_NUMBER_ID="test-number-id",
        WHATSAPP_TEMPLATE_NAME="approved_generic_reminder",
        WHATSAPP_TEMPLATE_LANGUAGE="fr",
    )
    @patch("sante.reminders.urllib_request.urlopen")
    def test_whatsapp_api_acceptance_is_recorded(self, mocked_urlopen):
        mocked_urlopen.return_value.__enter__.return_value.read.return_value = (
            b'{"messages":[{"id":"wamid.test-123"}]}'
        )
        VaccinationRappel.objects.create(
            vaccination=self.vaccination,
            canal="whatsapp",
            delai="J0",
            date_tentative=timezone.now() - timedelta(minutes=1),
        )

        self.assertEqual(send_due_vaccination_reminders(), 1)
        reminder = VaccinationRappel.objects.get(
            vaccination=self.vaccination,
            canal="whatsapp",
        )
        self.assertEqual(reminder.statut, "envoye")
        self.assertEqual(reminder.fournisseur_message_id, "wamid.test-123")

    @override_settings(
        WHATSAPP_TOKEN="",
        WHATSAPP_PHONE_NUMBER_ID="",
        WHATSAPP_TEMPLATE_NAME="",
        WHATSAPP_TEMPLATE_LANGUAGE="",
    )
    def test_missing_whatsapp_configuration_is_recorded_without_sending(self):
        VaccinationRappel.objects.create(
            vaccination=self.vaccination,
            canal="whatsapp",
            delai="J0",
            date_tentative=timezone.now() - timedelta(minutes=1),
        )

        self.assertEqual(send_due_vaccination_reminders(), 0)
        reminder = VaccinationRappel.objects.get(
            vaccination=self.vaccination,
            canal="whatsapp",
        )
        self.assertEqual(reminder.statut, "echec")
        self.assertIn("WHATSAPP_TOKEN", reminder.resultat)

    def test_missing_parent_contacts_create_no_reminders(self):
        self.parent.email = ""
        self.parent.save(update_fields=["email"])
        self.enfant.telephone_parent = ""
        self.enfant.whatsapp_consent = False
        self.enfant.save(update_fields=["telephone_parent", "whatsapp_consent"])

        self.assertEqual(
            programmer_rappels_pour_vaccination(self.vaccination),
            [],
        )
        self.assertFalse(
            VaccinationRappel.objects.filter(vaccination=self.vaccination).exists()
        )
