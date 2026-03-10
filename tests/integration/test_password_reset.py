import pytest
from django.core import mail
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy


@pytest.mark.integration
class TestPasswordResetViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Password Reset Academy",
            slug="pwreset-passwordresetviews-iso",
            description="Test academy for password reset tests",
            email="pwreset-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="pwreset-owner-iso",
            email="owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()

    def test_password_reset_form_loads(self):
        response = self.client.get(reverse("password-reset"))
        assert response.status_code == 200
        assert b"Reset your password" in response.content

    def test_password_reset_done_loads(self):
        response = self.client.get(reverse("password-reset-done"))
        assert response.status_code == 200
        assert b"Check your email" in response.content

    def test_password_reset_complete_loads(self):
        response = self.client.get(reverse("password-reset-complete"))
        assert response.status_code == 200
        assert b"Password reset complete" in response.content

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_sends_email(self):
        response = self.client.post(reverse("password-reset"), {
            "email": "owner@test.com",
        })
        assert response.status_code == 302
        assert len(mail.outbox) == 1
        assert "Password reset" in mail.outbox[0].subject

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_nonexistent_email_still_redirects(self):
        response = self.client.post(reverse("password-reset"), {
            "email": "nobody@test.com",
        })
        assert response.status_code == 302
        assert len(mail.outbox) == 0

    def test_login_page_has_forgot_password_link(self):
        response = self.client.get(reverse("login"))
        assert b"Forgot password?" in response.content
        assert b"password-reset" in response.content or b"/accounts/password-reset/" in response.content
