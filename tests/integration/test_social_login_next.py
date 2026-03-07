"""Integration tests for BUG-012: Social login ?next= preservation.

Verifies that social login buttons (Google, Facebook) correctly include
the ?next= parameter in their URLs so that django-allauth can redirect
the user back to the intended page after OAuth completes.

The full OAuth flow cannot be tested in integration tests (requires
external provider), but we CAN test that the URLs are correctly
constructed with the ?next= parameter in the rendered HTML.
"""

import secrets

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Invitation


# Enable social login providers for all tests in this module
SOCIAL_ENV = {
    "GOOGLE_OAUTH_CLIENT_ID": "fake-google-client-id",
    "FACEBOOK_APP_ID": "fake-facebook-app-id",
}


@pytest.fixture(autouse=True)
def enable_social_login(monkeypatch):
    """Set env vars so social login buttons are rendered."""
    for key, value in SOCIAL_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def invitation(db, academy, owner_user):
    """Create a pending invitation for testing."""
    return Invitation.objects.create(
        academy=academy,
        email="socialuser@example.com",
        role="student",
        token=secrets.token_urlsafe(48),
        invited_by=owner_user,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )


# ---------------------------------------------------------------------------
# Happy Path: ?next= included in social button URLs
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestSocialButtonNextUrl:
    """Social login buttons include ?next= when a redirect URL is present."""

    def test_login_page_social_buttons_include_next(self, client):
        """On the login page with ?next=, Google/Facebook buttons include ?next=."""
        next_url = "/invitation/some-token/accept/"
        response = client.get(f"{reverse('login')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()

        # Google button should include ?next=
        assert f"google/login/?next={next_url}" in content or \
               f"google/login/?next=%2F" in content
        # Facebook button should include ?next=
        assert f"facebook/login/?next={next_url}" in content or \
               f"facebook/login/?next=%2F" in content

    def test_register_page_social_buttons_include_next(self, client):
        """On the register page with ?next=, social buttons include ?next=."""
        next_url = "/invitation/some-token/accept/"
        response = client.get(f"{reverse('register')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()

        # Google button should include ?next=
        assert f"google/login/?next={next_url}" in content or \
               f"google/login/?next=%2F" in content

    def test_accept_invitation_social_buttons_include_next(self, client, invitation):
        """On the accept-invitation page (unauthenticated), social buttons
        include ?next= pointing back to the accept URL."""
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Social buttons should include ?next= with the accept URL
        expected_next = f"/invitation/{invitation.token}/accept/"
        assert f"google/login/?next={expected_next}" in content or \
               f"google/login/?next=%2Finvitation" in content

    def test_accept_invitation_context_includes_accept_url(self, client, invitation):
        """AcceptInvitationView passes accept_url in context for social buttons."""
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # The accept URL should appear in the rendered page (in social button hrefs)
        assert f"/invitation/{invitation.token}/accept/" in content


# ---------------------------------------------------------------------------
# Boundary: No ?next= parameter (no breakage)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestSocialButtonWithoutNext:
    """Social login buttons work correctly without ?next= (no breakage)."""

    def test_login_page_social_buttons_without_next(self, client):
        """Social buttons render without ?next= when not provided."""
        response = client.get(reverse("login"))

        assert response.status_code == 200
        content = response.content.decode()

        # Buttons should render but without ?next=
        assert "google/login/" in content
        assert "facebook/login/" in content
        # Should NOT have a dangling ?next= with empty value
        assert "?next=" not in content

    def test_register_page_social_buttons_without_next(self, client):
        """Social buttons on register page render without ?next= when not provided."""
        response = client.get(reverse("register"))

        assert response.status_code == 200
        content = response.content.decode()

        # Buttons should render but without ?next=
        assert "google/login/" in content
        assert "?next=" not in content


# ---------------------------------------------------------------------------
# Permission: Social login URLs accessible to unauthenticated users
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestSocialLoginAccessibility:
    """Social login URLs are accessible to unauthenticated users."""

    def test_login_page_accessible_unauthenticated(self, client):
        """Login page with social buttons is accessible without authentication."""
        response = client.get(reverse("login"))
        assert response.status_code == 200
        assert b"Google" in response.content
        assert b"Facebook" in response.content

    def test_register_page_accessible_unauthenticated(self, client):
        """Register page with social buttons is accessible without authentication."""
        response = client.get(reverse("register"))
        assert response.status_code == 200
        assert b"Google" in response.content
        assert b"Facebook" in response.content

    def test_accept_invitation_page_accessible_unauthenticated(self, client, invitation):
        """Accept invitation page shows social buttons for unauthenticated users."""
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.get(url)
        assert response.status_code == 200
        assert b"Google" in response.content
        assert b"Facebook" in response.content


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestSocialButtonEdgeCases:
    """Edge cases for social button ?next= handling."""

    def test_next_url_with_special_characters(self, client):
        """?next= with URL-safe special characters is handled correctly."""
        next_url = "/invitation/abc-123_def/accept/"
        response = client.get(f"{reverse('login')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()
        # The next URL should be present in the social button href
        assert "google/login/?next=" in content

    def test_social_buttons_hidden_when_providers_not_configured(self, client, monkeypatch):
        """Social buttons are not rendered when providers are not configured."""
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
        monkeypatch.delenv("FACEBOOK_APP_ID", raising=False)

        response = client.get(reverse("login"))

        assert response.status_code == 200
        content = response.content.decode()
        # No social buttons should be rendered
        assert "google/login/" not in content
        assert "facebook/login/" not in content
