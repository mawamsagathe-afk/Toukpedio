from datetime import timedelta
import re
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Enfant,
    JournalSymptome,
    PriseTraitement,
    SuiviCroissance,
    Temperature,
    Traitement,
)
from .views import (
    _contient_signe_urgence,
    _limiter_reponse_assistant,
    _urgence_nourrisson,
)


class AssistantUrgencesNourrissonTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="parent_urgences",
            password="test-password-123",
        )
        self.enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Test",
            prenom="Bebe",
            date_naissance=timezone.localdate() - timedelta(days=60),
            sexe="F",
        )
        self.client.force_login(self.parent)

    def test_recent_fever_in_symptom_journal_triggers_urgent_guidance(self):
        JournalSymptome.objects.create(
            enfant=self.enfant,
            symptome="Fièvre",
            intensite="forte",
            temperature="38.0",
        )

        self.assertTrue(_urgence_nourrisson(self.enfant, ""))

    def test_repeated_vomiting_in_message_triggers_urgent_guidance(self):
        self.assertTrue(
            _urgence_nourrisson(
                self.enfant,
                "Il a des vomissements répétés toutes les 3 heures.",
            )
        )

    def test_recent_temperature_record_triggers_urgent_guidance(self):
        Temperature.objects.create(
            enfant=self.enfant,
            valeur="38.0",
        )

        self.assertTrue(_urgence_nourrisson(self.enfant, ""))

    def test_repeated_vomiting_in_recent_symptom_journal_triggers_urgent_guidance(self):
        JournalSymptome.objects.create(
            enfant=self.enfant,
            symptome="Vomissements répétés",
            intensite="forte",
            description="Vomissements toutes les 3 heures",
        )

        self.assertTrue(_urgence_nourrisson(self.enfant, ""))

    def test_negated_fever_and_vomiting_do_not_trigger_infant_rule(self):
        self.assertFalse(
            _urgence_nourrisson(
                self.enfant,
                "Pas de fièvre et aucun vomissement.",
            )
        )

    def test_infant_rule_does_not_apply_after_three_months(self):
        self.enfant.date_naissance = timezone.localdate() - timedelta(days=120)
        self.enfant.save(update_fields=["date_naissance"])

        self.assertFalse(
            _urgence_nourrisson(self.enfant, "Fièvre à 38 °C.")
        )

    def test_fever_message_returns_urgent_response_without_calling_gemini(self):
        with patch("sante.views.genai.Client") as gemini_client:
            response = self.client.post(
                reverse("sante:assistant_gemini", args=[self.enfant.pk]),
                {"message": "Il a de la fièvre à 38 °C."},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["urgent"])
        self.assertIn("15 ou le 112", response.json()["reply"])
        gemini_client.assert_not_called()

    def test_temperature_at_least_38_opens_child_chat_automatically(self):
        response = self.client.post(
            reverse("sante:suivi_temperature", args=[self.enfant.pk]),
            {"valeur": "38.0", "observation": "Fatigué"},
        )

        temperature = Temperature.objects.get(enfant=self.enfant)
        self.assertRedirects(
            response,
            (
                f"{reverse('sante:detail_enfant', args=[self.enfant.pk])}"
                f"?assistant_temperature_id={temperature.pk}"
            ),
            fetch_redirect_response=False,
        )

        page = self.client.get(response.url)
        self.assertContains(page, 'data-temperature-initial-id="%s"' % temperature.pk)
        self.assertContains(page, "38.0 °C")

    def test_normal_temperature_keeps_existing_follow_up_flow(self):
        response = self.client.post(
            reverse("sante:suivi_temperature", args=[self.enfant.pk]),
            {"valeur": "37.2", "observation": ""},
        )

        self.assertRedirects(
            response,
            reverse("sante:suivi_temperature", args=[self.enfant.pk]),
            fetch_redirect_response=False,
        )

    def test_temperature_just_below_threshold_keeps_existing_follow_up_flow(self):
        response = self.client.post(
            reverse("sante:suivi_temperature", args=[self.enfant.pk]),
            {"valeur": "37.9", "observation": ""},
        )

        self.assertRedirects(
            response,
            reverse("sante:suivi_temperature", args=[self.enfant.pk]),
            fetch_redirect_response=False,
        )

    def test_elevated_temperature_prompt_receives_child_context_and_recent_dose(self):
        self.enfant.date_naissance = timezone.localdate() - timedelta(days=365 * 5)
        self.enfant.allergies = "Arachides"
        self.enfant.antecedents = "Asthme"
        self.enfant.save(update_fields=["date_naissance", "allergies", "antecedents"])
        SuiviCroissance.objects.create(
            enfant=self.enfant,
            date_mesure=timezone.localdate(),
            poids="18.50",
            taille="110.00",
        )
        traitement = Traitement.objects.create(
            enfant=self.enfant,
            medicament="Doliprane",
            dose="dose inscrite",
            frequence="unique",
            premiere_prise=timezone.now() - timedelta(hours=2),
            actif=True,
        )
        PriseTraitement.objects.create(
            traitement=traitement,
            date_heure_prevue=timezone.now() - timedelta(hours=2),
            date_heure_prise=timezone.now() - timedelta(hours=2),
            statut="prise",
            observation="Prise notée par le parent",
        )
        temperature = Temperature.objects.create(
            enfant=self.enfant,
            valeur="38.4",
            observation="Mesure frontale",
        )

        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
            patch("sante.views.genai.Client") as gemini_client,
        ):
            gemini_client.return_value.models.generate_content.return_value.text = (
                "Proposez régulièrement à boire et surveillez son état."
            )
            response = self.client.post(
                reverse("sante:assistant_gemini", args=[self.enfant.pk]),
                {"temperature_id": str(temperature.pk)},
            )

        self.assertEqual(response.status_code, 200)
        prompt = gemini_client.return_value.models.generate_content.call_args.kwargs[
            "contents"
        ]
        for expected in (
            "38.4 °C",
            "Âge calculé",
            "18.50 kg",
            "Arachides",
            "Asthme",
            "Doliprane",
            "Prise notée par le parent",
            "50 mots maximum",
            "Doliprane et Efferalgan contiennent tous deux du paracétamol",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, prompt)

    def test_infant_high_temperature_returns_short_urgent_alert_without_gemini(self):
        temperature = Temperature.objects.create(
            enfant=self.enfant,
            valeur="38.2",
        )

        with patch("sante.views.genai.Client") as gemini_client:
            response = self.client.post(
                reverse("sante:assistant_gemini", args=[self.enfant.pk]),
                {"temperature_id": str(temperature.pk)},
            )

        self.assertTrue(response.json()["urgent"])
        self.assertIn("38.2 °C", response.json()["reply"])
        self.assertLessEqual(
            len(re.findall(r"\S+", response.json()["reply"])),
            50,
        )
        gemini_client.assert_not_called()

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    def test_gemini_prompt_adapts_guidance_to_person_and_age(self):
        with patch("sante.views.genai.Client") as gemini_client:
            gemini_client.return_value.models.generate_content.return_value.text = (
                "Reposez-vous et surveillez les symptômes."
            )
            response = self.client.post(
                reverse("sante:assistant_gemini", args=[self.enfant.pk]),
                {"message": "Que faire pour un rhume léger ?"},
            )

        self.assertEqual(response.status_code, 200)
        prompt = gemini_client.return_value.models.generate_content.call_args.kwargs[
            "contents"
        ]
        self.assertIn("Ne suppose pas qu'une question concerne l'enfant du dossier", prompt)
        self.assertIn("mesures générales et non médicamenteuses adaptées à l'âge", prompt)
        self.assertIn("Ne fournis jamais de dose ou de schéma de prise", prompt)
        self.assertIn("50 mots maximum", prompt)

    def test_assistant_word_limit_is_enforced_on_model_response(self):
        response_text = " ".join(f"mot{index}" for index in range(60))

        limited_response = _limiter_reponse_assistant(response_text)

        self.assertLessEqual(len(re.findall(r"\S+", limited_response)), 50)

    def test_additional_emergency_signs_are_detected(self):
        for message in (
            "Il a des difficultés respiratoires.",
            "Il est inhabituellement somnolent.",
            "Il a la nuque raide.",
            "Il n'a plus de larmes et ses couches sont sèches.",
            "Son état général est préoccupant.",
        ):
            with self.subTest(message=message):
                self.assertTrue(_contient_signe_urgence(message))
