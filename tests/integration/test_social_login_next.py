"""Integration tests for BUG-012: Social login ?next= preservation.

Verifies that social login buttons (Google, Facebook) correctly include
the ?next= parameter in their URLs so that django-allauth can redirect
the user back to the intended page after OAuth completes.

The full OAuth flow cannot be tested in integration tests (requires
external provider), but we CAN test that the URLs are correctly
constructed with the ?next= parameter in the rendered HTML.
"""

import os
import secrets
import unittest.mock

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.accounts.models import Invitation


# Env vars that enable social login buttons in templates
SOCIAL_ENV = {
    "GOOGLE_OAUTH_CLIENT_ID": "fake-google-client-id",
    "FACEBOOK_APP_ID": "fake-facebook-app-id",
}


# ---------------------------------------------------------------------------
# Happy Path: ?next= included in social button URLs
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSocialButtonNextUrl(TestCase):
    """Social login buttons include ?next= when a redirect URL is present."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Social Next Academy",
            slug="soc-nextuurl-iso",
            description="Academy for social next URL tests",
            email="soc-nextuurl@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="soc-nextuurl-owner",
            email="soc-nextuurl-owner@test.com",
            password="testpass123",
            first_name="Social",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="socialuser-nextuurl@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

    def setUp(self):
        self.client = Client()
        self._social_patcher = unittest.mock.patch.dict(os.environ, SOCIAL_ENV)
        self._social_patcher.start()

    def tearDown(self):
        self._social_patcher.stop()

    def test_login_page_social_buttons_include_next(self):
        """On the login page with ?next=, Google/Facebook buttons include ?next=."""
        next_url = "/invitation/some-token/accept/"
        response = self.client.get(f"{reverse('login')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()

        # Google button should include ?next=
        assert f"google/login/?next={next_url}" in content or \
               f"google/login/?next=%2F" in content
        # Facebook button should include ?next=
        assert f"facebook/login/?next={next_url}" in content or \
               f"facebook/login/?next=%2F" in content

    def test_register_page_social_buttons_include_next(self):
        """On the register page with ?next=, social buttons include ?next=."""
        next_url = "/invitation/some-token/accept/"
        response = self.client.get(f"{reverse('register')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()

        # Google button should include ?next=
        assert f"google/login/?next={next_url}" in content or \
               f"google/login/?next=%2F" in content

    def test_accept_invitation_social_buttons_include_next(self):
        """On the accept-invitation page (unauthenticated), social buttons
        include ?next= pointing back to the accept URL."""
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Social buttons should include ?next= with the accept URL
        expected_next = f"/invitation/{self.invitation.token}/accept/"
        assert f"google/login/?next={expected_next}" in content or \
               f"google/login/?next=%2Finvitation" in content

    def test_accept_invitation_context_includes_accept_url(self):
        """AcceptInvitationView passes accept_url in context for social buttons."""
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # The accept URL should appear in the rendered page (in social button hrefs)
        assert f"/invitation/{self.invitation.token}/accept/" in content


# ---------------------------------------------------------------------------
# Boundary: No ?next= parameter (no breakage)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSocialButtonWithoutNext(TestCase):
    """Social login buttons work correctly without ?next= (no breakage)."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Social Without Next Academy",
            slug="soc-wonext-iso",
            description="Academy for social without next tests",
            email="soc-wonext@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="soc-wonext-owner",
            email="soc-wonext-owner@test.com",
            password="testpass123",
            first_name="Social",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self._social_patcher = unittest.mock.patch.dict(os.environ, SOCIAL_ENV)
        self._social_patcher.start()

    def tearDown(self):
        self._social_patcher.stop()

    def test_login_page_social_buttons_without_next(self):
        """Social buttons render without ?next= when not provided."""
        response = self.client.get(reverse("login"))

        assert response.status_code == 200
        content = response.content.decode()

        # Buttons should render but without ?next=
        assert "google/login/" in content
        assert "facebook/login/" in content
        # Should NOT have a dangling ?next= with empty value
        assert "?next=" not in content

    def test_register_page_social_buttons_without_next(self):
        """Social buttons on register page render without ?next= when not provided."""
        response = self.client.get(reverse("register"))

        assert response.status_code == 200
        content = response.content.decode()

        # Buttons should render but without ?next=
        assert "google/login/" in content
        assert "?next=" not in content


# ---------------------------------------------------------------------------
# Permission: Social login URLs accessible to unauthenticated users
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSocialLoginAccessibility(TestCase):
    """Social login URLs are accessible to unauthenticated users."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Social Access Academy",
            slug="soc-access-iso",
            description="Academy for social accessibility tests",
            email="soc-access@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="soc-access-owner",
            email="soc-access-owner@test.com",
            password="testpass123",
            first_name="Social",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="socialuser-access@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

    def setUp(self):
        self.client = Client()
        self._social_patcher = unittest.mock.patch.dict(os.environ, SOCIAL_ENV)
        self._social_patcher.start()

    def tearDown(self):
        self._social_patcher.stop()

    def test_login_page_accessible_unauthenticated(self):
        """Login page with social buttons is accessible without authentication."""
        response = self.client.get(reverse("login"))
        assert response.status_code == 200
        assert b"Google" in response.content
        assert b"Facebook" in response.content

    def test_register_page_accessible_unauthenticated(self):
        """Register page with social buttons is accessible without authentication."""
        response = self.client.get(reverse("register"))
        assert response.status_code == 200
        assert b"Google" in response.content
        assert b"Facebook" in response.content

    def test_accept_invitation_page_accessible_unauthenticated(self):
        """Accept invitation page shows social buttons for unauthenticated users."""
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Google" in response.content
        assert b"Facebook" in response.content


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSocialButtonEdgeCases(TestCase):
    """Edge cases for social button ?next= handling."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Social Edge Academy",
            slug="soc-edge-iso",
            description="Academy for social edge case tests",
            email="soc-edge@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="soc-edge-owner",
            email="soc-edge-owner@test.com",
            password="testpass123",
            first_name="Social",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self._social_patcher = unittest.mock.patch.dict(os.environ, SOCIAL_ENV)
        self._social_patcher.start()

    def tearDown(self):
        self._social_patcher.stop()

    def test_next_url_with_special_characters(self):
        """?next= with URL-safe special characters is handled correctly."""
        next_url = "/invitation/abc-123_def/accept/"
        response = self.client.get(f"{reverse('login')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()
        # The next URL should be present in the social button href
        assert "google/login/?next=" in content

    def test_social_buttons_hidden_when_providers_not_configured(self):
        """Social buttons are not rendered when providers are not configured."""
        # Stop the setUp patcher and explicitly remove all social env vars
        # (load_dotenv may have loaded real values from .env).
        self._social_patcher.stop()
        saved = {}
        for key in ("GOOGLE_OAUTH_CLIENT_ID", "FACEBOOK_APP_ID"):
            if key in os.environ:
                saved[key] = os.environ.pop(key)
        try:
            response = self.client.get(reverse("login"))
        finally:
            os.environ.update(saved)
            self._social_patcher.start()

        assert response.status_code == 200
        content = response.content.decode()
        # No social buttons should be rendered
        assert "google/login/" not in content
        assert "facebook/login/" not in content
