import pytest
from django.core import mail
from django.urls import reverse


@pytest.mark.integration
class TestPasswordResetViews:
    def test_password_reset_form_loads(self, client):
        response = client.get(reverse("password-reset"))
        assert response.status_code == 200
        assert b"Reset your password" in response.content

    def test_password_reset_done_loads(self, client):
        response = client.get(reverse("password-reset-done"))
        assert response.status_code == 200
        assert b"Check your email" in response.content

    def test_password_reset_complete_loads(self, client):
        response = client.get(reverse("password-reset-complete"))
        assert response.status_code == 200
        assert b"Password reset complete" in response.content

    def test_password_reset_sends_email(self, client, owner_user, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        response = client.post(reverse("password-reset"), {
            "email": "owner@test.com",
        })
        assert response.status_code == 302
        assert len(mail.outbox) == 1
        assert "Password reset" in mail.outbox[0].subject

    def test_password_reset_nonexistent_email_still_redirects(self, client, db, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        response = client.post(reverse("password-reset"), {
            "email": "nobody@test.com",
        })
        assert response.status_code == 302
        assert len(mail.outbox) == 0

    def test_login_page_has_forgot_password_link(self, client):
        response = client.get(reverse("login"))
        assert b"Forgot password?" in response.content
        assert b"password-reset" in response.content or b"/accounts/password-reset/" in response.content
