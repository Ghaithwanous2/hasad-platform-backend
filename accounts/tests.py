from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import EmailVerification, User


class RegistrationFlowTests(TestCase):
    REGISTER_URL = "/api/v1/auth/register/"
    VERIFY_URL = "/api/v1/auth/register/verify/"
    RESEND_URL = "/api/v1/auth/register/resend/"
    LOGIN_URL = "/api/v1/auth/login/"

    password = "StrongPass!2026"

    def setUp(self):
        self.client = APIClient()
        self.email = "farmer.test@example.com"

    def registration_payload(self, email=None):
        return {
            "account_type": "FARMER",
            "email": email or self.email,
            "phone": "",
            "password": self.password,
            "password_confirm": self.password,
            "first_name": "Test",
            "last_name": "Farmer",
        }

    def register_user(self, email=None):
        sent_codes = []

        def capture_email(
            recipient_email,
            verification_code,
        ):
            sent_codes.append(
                {
                    "recipient_email": recipient_email,
                    "verification_code": verification_code,
                }
            )
            return 1

        with patch(
            "accounts.serializers.send_email_verification_code",
            side_effect=capture_email,
        ):
            response = self.client.post(
                self.REGISTER_URL,
                self.registration_payload(email),
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(len(sent_codes), 1)

        return response, sent_codes[0]["verification_code"]

    def test_register_creates_inactive_user_and_sends_otp(self):
        response, code = self.register_user()

        user = User.objects.get(
            email=self.email,
        )

        verification = EmailVerification.objects.get(
            user=user,
        )

        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertEqual(user.role, User.Role.FARMER)
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertEqual(
            str(verification.verification_id),
            response.data["verification_id"],
        )

    def test_register_rejects_admin_role(self):
        payload = self.registration_payload()
        payload["account_type"] = "ADMIN"

        response = self.client.post(
            self.REGISTER_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            User.objects.filter(
                email=self.email,
            ).exists()
        )

    def test_register_rejects_duplicate_email(self):
        self.register_user()

        response = self.client.post(
            self.REGISTER_URL,
            self.registration_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            User.objects.filter(
                email=self.email,
            ).count(),
            1,
        )

    def test_verify_correct_otp_activates_user_and_returns_tokens(self):
        register_response, code = self.register_user()

        verification_id = register_response.data[
            "verification_id"
        ]

        response = self.client.post(
            self.VERIFY_URL,
            {
                "verification_id": verification_id,
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

        user = User.objects.get(
            email=self.email,
        )

        verification = EmailVerification.objects.get(
            user=user,
        )

        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)
        self.assertIsNotNone(verification.verified_at)

    def test_verify_wrong_otp_is_rejected_and_counts_attempt(self):
        register_response, _ = self.register_user()

        verification_id = register_response.data[
            "verification_id"
        ]

        response = self.client.post(
            self.VERIFY_URL,
            {
                "verification_id": verification_id,
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        verification = EmailVerification.objects.get(
            verification_id=verification_id,
        )

        self.assertEqual(verification.attempts, 1)

        user = verification.user

        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)

    def test_verify_expired_otp_is_rejected(self):
        register_response, code = self.register_user()

        verification_id = register_response.data[
            "verification_id"
        ]

        verification = EmailVerification.objects.get(
            verification_id=verification_id,
        )

        verification.expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        verification.save(
            update_fields=["expires_at"],
        )

        response = self.client.post(
            self.VERIFY_URL,
            {
                "verification_id": verification_id,
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user = verification.user

        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)

    def test_verified_otp_cannot_be_used_again(self):
        register_response, code = self.register_user()

        verification_id = register_response.data[
            "verification_id"
        ]

        first_response = self.client.post(
            self.VERIFY_URL,
            {
                "verification_id": verification_id,
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        second_response = self.client.post(
            self.VERIFY_URL,
            {
                "verification_id": verification_id,
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_resend_sends_new_otp_after_cooldown(self):
        register_response, first_code = self.register_user()

        verification_id = register_response.data[
            "verification_id"
        ]

        verification = EmailVerification.objects.get(
            verification_id=verification_id,
        )

        verification.last_sent_at = (
            timezone.now() - timedelta(seconds=61)
        )
        verification.save(
            update_fields=["last_sent_at"],
        )

        sent_codes = []

        def capture_email(
            recipient_email,
            verification_code,
        ):
            sent_codes.append(verification_code)
            return 1

        with patch(
            "accounts.serializers.send_email_verification_code",
            side_effect=capture_email,
        ):
            response = self.client.post(
                self.RESEND_URL,
                {
                    "verification_id": verification_id,
                },
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(sent_codes), 1)
        self.assertNotEqual(sent_codes[0], first_code)

        verification.refresh_from_db()

        self.assertEqual(verification.attempts, 0)
        self.assertNotEqual(
            verification.code_hash,
            "",
        )

    def test_resend_is_rejected_before_cooldown_finishes(self):
        register_response, _ = self.register_user()

        verification_id = register_response.data[
            "verification_id"
        ]

        response = self.client.post(
            self.RESEND_URL,
            {
                "verification_id": verification_id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_can_login_after_email_verification(self):
        register_response, code = self.register_user()

        verification_id = register_response.data[
            "verification_id"
        ]

        verify_response = self.client.post(
            self.VERIFY_URL,
            {
                "verification_id": verification_id,
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            verify_response.status_code,
            status.HTTP_200_OK,
        )

        response = self.client.post(
            self.LOGIN_URL,
            {
                "identifier": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
