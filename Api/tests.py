from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class ConnexionApiTests(TestCase):
    def setUp(self):
        self.parent_user = User.objects.create_user(
            username="parent_test",
            password="MotDePasse123"
        )
        self.admin_user = User.objects.create_user(
            username="admin_test",
            password="MotDePasse123",
            is_staff=True,
        )

    def test_connexion_parent_valide_redirige_vers_tableau_parent(self):
        response = self.client.post(
            reverse("sante:connexion"),
            {"username": "parent_test", "password": "MotDePasse123"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("sante:tableau_bord_parent"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_connexion_parent_invalide_affiche_erreur(self):
        response = self.client.post(
            reverse("sante:connexion"),
            {"username": "parent_test", "password": "mauvais_mot_de_passe"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nom d'utilisateur ou mot de passe incorrect.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_connexion_admin_valide_redirige_vers_tableau_admin(self):
        response = self.client.post(
            reverse("sante:connexion_admin"),
            {"username": "admin_test", "password": "MotDePasse123"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("sante:tableau_bord_admin"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertTrue(response.wsgi_request.user.is_staff)

    def test_connexion_admin_refuse_compte_non_admin(self):
        response = self.client.post(
            reverse("sante:connexion_admin"),
            {"username": "parent_test", "password": "MotDePasse123"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ce compte n'a pas accès à l'administration.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)
