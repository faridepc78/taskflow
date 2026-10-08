from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class EmailLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="emailuser", email="person@example.com", password="Pass12345!"
        )

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "PERSON@example.com", "password": "Pass12345!"},
        )
        self.assertRedirects(response, reverse("projects:dashboard"))

    def test_login_with_username_still_works(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "emailuser", "password": "Pass12345!"},
        )
        self.assertRedirects(response, reverse("projects:dashboard"))

    def test_ambiguous_email_is_rejected(self):
        User.objects.create_user(
            username="another", email="person@example.com", password="Pass12345!"
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "person@example.com", "password": "Pass12345!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
