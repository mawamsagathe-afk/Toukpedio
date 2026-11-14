from unittest.mock import AsyncMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Conversation,
    Enfant,
    Message,
    Parent,
    ProfessionnelSante,
    Traitement,
)


class PersonnelSanteTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_sante",
            password="Admin!Secure2026",
            is_staff=True,
        )
        self.parent = User.objects.create_user(
            username="parent_sante",
            password="Parent!Secure2026",
        )
        Parent.objects.create(user=self.parent)
        self.enfant = Enfant.objects.create(
            parent=self.parent,
            nom="Test",
            prenom="Enfant",
            date_naissance="2020-01-01",
            sexe="F",
        )

    def _create_professionnel(self, username="soignant_sante"):
        user = User.objects.create_user(
            username=username,
            password="Soignant!Secure2026",
            first_name="Amina",
            last_name="Soignante",
            email=f"{username}@example.com",
        )
        ProfessionnelSante.objects.create(
            user=user,
            profession="Médecin",
            specialite="Pédiatrie",
        )
        return user

    def test_only_admin_can_add_health_professionals(self):
        self.client.force_login(self.parent)
        response = self.client.post(
            reverse("sante:administration_personnel_sante"),
            {},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProfessionnelSante.objects.exists())

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("sante:administration_personnel_sante"),
            {
                "username": "docteur_diallo",
                "first_name": "Awa",
                "last_name": "Diallo",
                "email": "awa@example.com",
                "profession": "Médecin",
                "specialite": "Pédiatrie",
                "numero_ordre": "ORD-123",
                "password1": "Clinic!Secure2026",
                "password2": "Clinic!Secure2026",
            },
        )

        self.assertRedirects(
            response,
            reverse("sante:administration_personnel_sante"),
        )
        professional = User.objects.get(username="docteur_diallo")
        self.assertEqual(professional.email, "awa@example.com")
        self.assertFalse(professional.is_staff)
        self.assertEqual(professional.profil_sante.profession, "Médecin")
        self.assertEqual(professional.profil_sante.specialite, "Pédiatrie")
        self.assertEqual(professional.profil_sante.numero_ordre, "ORD-123")

    def test_health_professional_logs_into_dedicated_space_and_inbox(self):
        professional = self._create_professionnel()
        conversation = Conversation.objects.create(
            parent=self.parent,
            professionnel=professional,
            enfant=self.enfant,
            sujet="Question sur un symptôme",
        )

        self.client.force_login(professional)
        response = self.client.get(reverse("sante:espace_sante"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Question sur un symptôme")

        response = self.client.get(reverse("sante:messagerie"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["conversations"][0].pk,
            conversation.pk,
        )

    def test_health_professional_can_prescribe_only_for_assigned_conversation(self):
        professional = self._create_professionnel()
        conversation = Conversation.objects.create(
            parent=self.parent,
            professionnel=professional,
            enfant=self.enfant,
            sujet="Question sur un symptôme",
        )
        self.client.force_login(professional)
        response = self.client.post(
            reverse(
                "sante:professionnel_prescrire_traitement",
                args=[conversation.pk],
            ),
            {
                "medicament": "Médicament de test",
                "dose": "5 ml",
                "frequence": "quotidienne",
                "premiere_prise": "2030-01-01T10:00",
                "date_fin": "2030-01-05",
                "notes": "Selon l’ordonnance du professionnel.",
            },
        )

        self.assertRedirects(
            response,
            reverse("sante:conversation_detail", args=[conversation.pk]),
        )
        traitement = Traitement.objects.get()
        self.assertEqual(traitement.enfant, self.enfant)
        self.assertEqual(traitement.prescrit_par, professional)

        other_professional = self._create_professionnel("autre_soignant")
        self.client.force_login(other_professional)
        response = self.client.post(
            reverse(
                "sante:professionnel_prescrire_traitement",
                args=[conversation.pk],
            ),
            {},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Traitement.objects.count(), 1)

    def test_quiz_summary_creates_a_private_direct_conversation(self):
        professional = self._create_professionnel()
        self.client.force_login(self.parent)
        session = self.client.session
        session[f"assistant_contact_apercu_{self.parent.pk}_{self.enfant.pk}"] = True
        session.save()

        channel_layer = type("ChannelLayerStub", (), {})()
        channel_layer.group_send = AsyncMock()
        with (
            patch("sante.views.get_channel_layer", return_value=channel_layer),
            patch(
                "sante.views.async_to_sync",
                side_effect=lambda _function: (
                    lambda *_args, **_kwargs: None
                ),
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post(
                reverse(
                    "sante:assistant_contact_agent",
                    args=[self.enfant.pk],
                ),
                {"consent": "yes"},
            )

        conversation = Conversation.objects.get()
        initial_message = Message.objects.get(conversation=conversation)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(conversation.parent, self.parent)
        self.assertEqual(conversation.professionnel, professional)
        self.assertEqual(conversation.enfant, self.enfant)
        self.assertIn("évaluation de santé", initial_message.texte)
        self.assertEqual(
            response.json()["redirect_url"],
            reverse("sante:conversation_detail", args=[conversation.pk]),
        )
