from datetime import timedelta

from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import EmailVerificationToken, PasswordResetToken


class RegistrationTests(APITestCase):
    def test_customer_can_register(self):
        url = reverse("authentication:register")
        payload = {
            "full_name": "Jane Wanjiru",
            "email": "jane@gmail.com",
            "phone_number": "+254712345678",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="jane@gmail.com")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertFalse(user.is_email_verified)
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())
        # Verification email was "sent" (console/locmem backend in tests).
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].subject.lower())

    def test_non_university_email_is_accepted(self):
        """Spec explicitly requires NOT restricting registration to a university domain."""
        url = reverse("authentication:register")
        payload = {
            "full_name": "John Otieno",
            "email": "john.otieno@outlook.com",
            "phone_number": "+254798765432",
            "password": "AnotherPass123",
            "confirm_password": "AnotherPass123",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_password_mismatch_rejected(self):
        url = reverse("authentication:register")
        payload = {
            "full_name": "Test User",
            "email": "mismatch@gmail.com",
            "phone_number": "+254700000000",
            "password": "StrongPass123",
            "confirm_password": "DifferentPass123",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="mismatch@gmail.com").exists())

    def test_duplicate_email_rejected(self):
        User.objects.create_user(email="dup@gmail.com", password="StrongPass123", full_name="Dup User")
        url = reverse("authentication:register")
        payload = {
            "full_name": "Dup User 2",
            "email": "dup@gmail.com",
            "phone_number": "+254711111111",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        url = reverse("authentication:register")
        payload = {
            "full_name": "Weak Pass",
            "email": "weak@gmail.com",
            "phone_number": "+254722222222",
            "password": "12345678",
            "confirm_password": "12345678",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailVerificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="verify@gmail.com", password="StrongPass123", full_name="Verify Me"
        )
        self.user.is_email_verified = False
        self.user.save()

    def test_valid_token_verifies_email(self):
        token = EmailVerificationToken.objects.create(user=self.user)
        url = reverse("authentication:verify-email")
        response = self.client.post(url, {"token": token.token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

        token.refresh_from_db()
        self.assertTrue(token.is_used)

    def test_expired_token_rejected(self):
        token = EmailVerificationToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timedelta(hours=1)
        token.save()

        url = reverse("authentication:verify-email")
        response = self.client.post(url, {"token": token.token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "token_expired")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_used_token_cannot_be_reused(self):
        token = EmailVerificationToken.objects.create(user=self.user)
        token.mark_used()

        url = reverse("authentication:verify-email")
        response = self.client.post(url, {"token": token.token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_token_rejected(self):
        url = reverse("authentication:verify-email")
        response = self.client.post(url, {"token": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_issues_new_token_and_invalidates_old(self):
        old_token = EmailVerificationToken.objects.create(user=self.user)
        url = reverse("authentication:resend-verification")
        response = self.client.post(url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old_token.refresh_from_db()
        self.assertTrue(old_token.is_used)  # invalidated
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user, used_at__isnull=True).count(), 1)

    def test_resend_verification_does_not_leak_unregistered_email(self):
        url = reverse("authentication:resend-verification")
        response = self.client.post(url, {"email": "nobody@gmail.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # same generic response either way


class LoginTests(APITestCase):
    def setUp(self):
        self.verified_user = User.objects.create_user(
            email="loggedin@gmail.com", password="StrongPass123", full_name="Verified User"
        )
        self.verified_user.is_email_verified = True
        self.verified_user.save()

        self.unverified_user = User.objects.create_user(
            email="unverified@gmail.com", password="StrongPass123", full_name="Unverified User"
        )
        self.unverified_user.is_email_verified = False
        self.unverified_user.save()

    def test_login_before_verification_blocked(self):
        url = reverse("authentication:login")
        response = self.client.post(url, {"email": "unverified@gmail.com", "password": "StrongPass123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "email_not_verified")

    def test_login_after_verification_succeeds(self):
        url = reverse("authentication:login")
        response = self.client.post(url, {"email": "loggedin@gmail.com", "password": "StrongPass123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "loggedin@gmail.com")

    def test_login_wrong_password_rejected(self):
        url = reverse("authentication:login")
        response = self.client.post(url, {"email": "loggedin@gmail.com", "password": "WrongPassword"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_suspended_user_cannot_login(self):
        self.verified_user.is_suspended = True
        self.verified_user.save()
        url = reverse("authentication:login")
        response = self.client.post(url, {"email": "loggedin@gmail.com", "password": "StrongPass123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_endpoint_requires_auth(self):
        url = reverse("users:me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_returns_profile_when_authenticated(self):
        login_url = reverse("authentication:login")
        login_resp = self.client.post(login_url, {"email": "loggedin@gmail.com", "password": "StrongPass123"})
        access = login_resp.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(reverse("users:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "loggedin@gmail.com")

    def test_logout_blacklists_refresh_token(self):
        login_url = reverse("authentication:login")
        login_resp = self.client.post(login_url, {"email": "loggedin@gmail.com", "password": "StrongPass123"})
        access, refresh = login_resp.data["access"], login_resp.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_resp = self.client.post(reverse("authentication:logout"), {"refresh": refresh})
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        refresh_resp = self.client.post(reverse("authentication:token-refresh"), {"refresh": refresh})
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reset@gmail.com", password="OldPass123", full_name="Reset Me"
        )
        self.user.is_email_verified = True
        self.user.save()

    def test_request_reset_creates_token_and_sends_email(self):
        url = reverse("authentication:password-reset-request")
        response = self.client.post(url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PasswordResetToken.objects.filter(user=self.user).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_confirm_reset_with_valid_token_changes_password(self):
        token = PasswordResetToken.objects.create(user=self.user)
        url = reverse("authentication:password-reset-confirm")
        response = self.client.post(
            url, {"token": token.token, "password": "BrandNewPass123", "confirm_password": "BrandNewPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass123"))

        token.refresh_from_db()
        self.assertTrue(token.is_used)

    def test_confirm_reset_with_expired_token_rejected(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timedelta(hours=1)
        token.save()

        url = reverse("authentication:password-reset-confirm")
        response = self.client.post(
            url, {"token": token.token, "password": "BrandNewPass123", "confirm_password": "BrandNewPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "token_expired")

    def test_change_password_requires_correct_old_password(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("authentication:change-password")
        response = self.client.post(
            url,
            {"old_password": "WrongOldPass", "new_password": "NewerPass123", "confirm_password": "NewerPass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("authentication:change-password")
        response = self.client.post(
            url,
            {"old_password": "OldPass123", "new_password": "NewerPass123", "confirm_password": "NewerPass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewerPass123"))
