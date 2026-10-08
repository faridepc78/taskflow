from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ResetSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.first = User.objects.create_user(username="first", email="first@example.com", password="Original123!")
        self.second = User.objects.create_user(username="second", email="second@example.com", password="Original123!")

    @patch("accounts.views.password_reset.send_password_reset_otp")
    def test_switching_account_clears_previous_verification(self, send):
        session = self.client.session
        session["password_reset_email"] = self.first.email
        session["password_reset_verified"] = True
        session["password_reset_verified_email"] = self.first.email
        session.save()
        response = self.client.post(reverse("accounts:forgot-password"), {"email": self.second.email})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("password_reset_verified", self.client.session)
        self.assertEqual(self.client.get(reverse("accounts:reset-password")).status_code, 302)

    def test_verified_session_must_match_email(self):
        session = self.client.session
        session["password_reset_email"] = self.second.email
        session["password_reset_verified"] = True
        session["password_reset_verified_email"] = self.first.email
        session.save()
        self.assertRedirects(self.client.get(reverse("accounts:reset-password")), reverse("accounts:forgot-password"))

    def test_login_is_rate_limited(self):
        url = reverse("accounts:login")
        for _ in range(10):
            self.client.post(url, {"username": self.first.username, "password": "wrong"})
        response = self.client.post(url, {"username": self.first.username, "password": "Original123!"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
