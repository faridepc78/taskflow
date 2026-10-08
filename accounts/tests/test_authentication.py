from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import Profile

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "taskflow-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse("accounts:register")
        self.verify_url = reverse("accounts:verify-email")
        self.valid_payload = {
            "first_name": "Farid",
            "last_name": "Test",
            "username": "farid_test",
            "email": "farid@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

    @patch("accounts.views.registration.send_registration_otp")
    def test_register_stores_pending_data_without_creating_user(self, send_otp):
        response = self.client.post(self.register_url, self.valid_payload)

        self.assertRedirects(response, self.verify_url)
        self.assertFalse(User.objects.filter(username="farid_test").exists())
        self.assertEqual(
            self.client.session["pending_registration"]["email"],
            "farid@example.com",
        )
        send_otp.assert_called_once_with("farid@example.com")

    def test_register_rejects_password_mismatch(self):
        payload = {**self.valid_payload, "password_confirm": "DifferentPass123!"}

        response = self.client.post(self.register_url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertFalse(User.objects.filter(username="farid_test").exists())

    def test_register_rejects_duplicate_username_and_email(self):
        User.objects.create_user(
            username="farid_test",
            email="farid@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(self.register_url, self.valid_payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already taken.")
        self.assertContains(response, "An account with this email already exists.")

    def test_verify_email_creates_user_and_profile(self):
        session = self.client.session
        session["pending_registration"] = {
            "first_name": "Farid",
            "last_name": "Test",
            "username": "farid_test",
            "email": "farid@example.com",
            "password": "pbkdf2_sha256$1000000$test$wN9bJpRk0rA6R7aAQqg5tC8N6Awjz3Vf4HoF3PPJgMs=",
        }
        session.save()
        cache.set("register_otp:farid@example.com", "123456", 300)

        response = self.client.post(self.verify_url, {"code": "123456"})

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="farid_test")
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertNotIn("pending_registration", self.client.session)

    def test_verify_email_rejects_wrong_code(self):
        session = self.client.session
        session["pending_registration"] = {
            "first_name": "Farid",
            "last_name": "Test",
            "username": "farid_test",
            "email": "farid@example.com",
            "password": "unused",
        }
        session.save()
        cache.set("register_otp:farid@example.com", "123456", 300)

        response = self.client.post(self.verify_url, {"code": "654321"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid verification code")
        self.assertEqual(cache.get("register_otp_attempts:farid@example.com"), 1)


@override_settings(CACHES=TEST_CACHES)
class AuthenticationAndPasswordTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="farid",
            email="farid@example.com",
            password="OldStrongPass123!",
        )
        Profile.objects.get_or_create(user=self.user)

    def test_login_and_logout(self):
        login_response = self.client.post(
            reverse("accounts:login"),
            {"username": "farid", "password": "OldStrongPass123!"},
        )
        self.assertRedirects(login_response, reverse("projects:dashboard"))

        logout_response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(logout_response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("accounts.views.password_reset.send_password_reset_otp")
    def test_forgot_password_starts_reset_flow(self, send_otp):
        response = self.client.post(
            reverse("accounts:forgot-password"),
            {"email": "farid@example.com"},
        )

        self.assertRedirects(response, reverse("accounts:verify-password-reset"))
        self.assertEqual(
            self.client.session["password_reset_email"],
            "farid@example.com",
        )
        send_otp.assert_called_once_with("farid@example.com")

    def test_reset_password_requires_verified_session(self):
        response = self.client.get(reverse("accounts:reset-password"))
        self.assertRedirects(response, reverse("accounts:forgot-password"))

    def test_reset_password_changes_credentials(self):
        session = self.client.session
        session["password_reset_email"] = "farid@example.com"
        session["password_reset_verified"] = True
        session.save()

        response = self.client.post(
            reverse("accounts:reset-password"),
            {
                "password": "NewStrongPass456!",
                "password_confirm": "NewStrongPass456!",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass456!"))
        self.assertFalse(self.user.check_password("OldStrongPass123!"))

    def test_change_password_keeps_user_logged_in(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:change-password"),
            {
                "current_password": "OldStrongPass123!",
                "new_password": "NewStrongPass456!",
                "new_password_confirm": "NewStrongPass456!",
            },
        )

        self.assertRedirects(response, reverse("projects:dashboard"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass456!"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
