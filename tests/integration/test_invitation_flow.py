"""Integration tests for the invitation flow.

Covers DEBT-002 (no test coverage for invitation flows) and
DEBT-003 (email match enforcement on acceptance).

Tests organized into:
- Happy path (send, accept, membership, welcome email, owner notification)
- Email match enforcement (matching, mismatching, case-insensitive)
- Error states (invalid token, expired, already accepted, duplicate)
- Permission boundaries (non-owner cannot send/resend/cancel)
- ?next= URL preservation through login/register flow
"""

import secrets

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Invitation, Membership, User
from apps.notifications.models import Notification


@pytest.fixture
def invitation(db, academy, owner_user):
    """Create a pending invitation for a new user."""
    return Invitation.objects.create(
        academy=academy,
        email="invited@example.com",
        role="student",
        token=secrets.token_urlsafe(48),
        invited_by=owner_user,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )


@pytest.fixture
def invited_user(db, invitation):
    """Create a user whose email matches the invitation."""
    user = User.objects.create_user(
        username="inviteduser",
        email=invitation.email,
        password="testpass123",
        first_name="Invited",
        last_name="User",
    )
    return user


@pytest.fixture
def wrong_email_user(db):
    """Create a user whose email does NOT match any invitation."""
    return User.objects.create_user(
        username="wronguser",
        email="wrong@example.com",
        password="testpass123",
        first_name="Wrong",
        last_name="User",
    )


@pytest.fixture
def expired_invitation(db, academy, owner_user):
    """Create an invitation that has already expired."""
    return Invitation.objects.create(
        academy=academy,
        email="expired@example.com",
        role="student",
        token=secrets.token_urlsafe(48),
        invited_by=owner_user,
        expires_at=timezone.now() - timezone.timedelta(days=1),
    )


@pytest.fixture
def accepted_invitation(db, academy, owner_user):
    """Create an invitation that has already been accepted."""
    return Invitation.objects.create(
        academy=academy,
        email="accepted@example.com",
        role="student",
        token=secrets.token_urlsafe(48),
        invited_by=owner_user,
        accepted=True,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )


# ---------------------------------------------------------------------------
# Happy Path Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestInviteMemberHappyPath:
    """Test that an owner can send an invitation."""

    def test_owner_can_send_invitation(self, auth_client, academy):
        """Owner sends an invitation; Invitation record is created and email sent."""
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        response = auth_client.post(url, {
            "email": "newuser@example.com",
            "role": "student",
        })
        # Should redirect back to members page (non-HTMX request)
        assert response.status_code == 302

        # Invitation record created
        inv = Invitation.objects.get(email="newuser@example.com", academy=academy)
        assert inv.role == "student"
        assert inv.accepted is False
        assert inv.token  # non-empty token
        assert inv.expires_at > timezone.now()

        # Invitation email sent
        assert len(mail.outbox) == 1
        assert "newuser@example.com" in mail.outbox[0].to
        assert academy.name in mail.outbox[0].subject

    def test_owner_can_send_instructor_invitation(self, auth_client, academy):
        """Owner can invite an instructor (not just students)."""
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        auth_client.post(url, {
            "email": "prof@example.com",
            "role": "instructor",
        })
        inv = Invitation.objects.get(email="prof@example.com", academy=academy)
        assert inv.role == "instructor"


@pytest.mark.integration
@pytest.mark.django_db
class TestAcceptInvitationHappyPath:
    """Test the full accept-invitation flow for a logged-in user."""

    def test_accept_invitation_get_renders_page(self, client, invitation):
        """GET request shows the accept-invitation page."""
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.get(url)
        assert response.status_code == 200
        assert invitation.academy.name.encode() in response.content

    def test_logged_in_user_can_accept_invitation(self, client, invitation, invited_user):
        """Matching user accepts invitation and becomes a member."""
        client.force_login(invited_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.post(url)

        # Redirects to dashboard
        assert response.status_code == 302
        assert reverse("dashboard") in response.url

        # Membership created
        assert Membership.objects.filter(
            user=invited_user,
            academy=invitation.academy,
            role="student",
        ).exists()

        # Invitation marked as accepted
        invitation.refresh_from_db()
        assert invitation.accepted is True

        # User's current_academy set
        invited_user.refresh_from_db()
        assert invited_user.current_academy == invitation.academy

    def test_welcome_email_sent_after_acceptance(self, client, invitation, invited_user):
        """A welcome email is sent to the user after accepting."""
        client.force_login(invited_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        client.post(url)

        # Welcome email is the first (and only) email sent on acceptance
        assert len(mail.outbox) == 1
        welcome_email = mail.outbox[0]
        assert invited_user.email in welcome_email.to
        assert "Welcome" in welcome_email.subject
        assert invitation.academy.name in welcome_email.subject

    def test_owner_notification_created_after_acceptance(
        self, client, invitation, invited_user, owner_user
    ):
        """Owner gets a notification when an invitation is accepted."""
        client.force_login(invited_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        client.post(url)

        notifications = Notification.objects.filter(
            recipient=owner_user,
            academy=invitation.academy,
            notification_type="invitation",
        )
        assert notifications.count() == 1
        assert "accepted" in notifications.first().message.lower()

    def test_success_message_set_after_acceptance(self, client, invitation, invited_user):
        """A success flash message is set after acceptance."""
        client.force_login(invited_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.post(url, follow=True)

        # Check messages framework
        messages_list = list(response.context["messages"])
        assert len(messages_list) >= 1
        assert "Welcome" in str(messages_list[0])


# ---------------------------------------------------------------------------
# Email Match Enforcement (DEBT-003)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestEmailMatchEnforcement:
    """Test that only the invited email can accept the invitation."""

    def test_matching_email_can_accept(self, client, invitation, invited_user):
        """User whose email matches the invitation can accept."""
        client.force_login(invited_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.post(url)

        assert response.status_code == 302  # redirect to dashboard
        invitation.refresh_from_db()
        assert invitation.accepted is True

    def test_non_matching_email_sees_error_page(self, client, invitation, wrong_email_user):
        """User with different email sees the email_mismatch error page."""
        client.force_login(wrong_email_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.post(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Should render the email_mismatch template
        assert "mismatch" in content.lower() or wrong_email_user.email in content

        # Invitation should NOT be accepted
        invitation.refresh_from_db()
        assert invitation.accepted is False

        # No membership should be created
        assert not Membership.objects.filter(
            user=wrong_email_user, academy=invitation.academy
        ).exists()

    def test_email_comparison_is_case_insensitive(self, client, invitation, db):
        """Email match ignores case: INVITED@EXAMPLE.COM matches invited@example.com."""
        # Create user with uppercased email
        upper_user = User.objects.create_user(
            username="upperuser",
            email="INVITED@EXAMPLE.COM",
            password="testpass123",
        )
        client.force_login(upper_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.post(url)

        # Should succeed (redirect to dashboard)
        assert response.status_code == 302
        invitation.refresh_from_db()
        assert invitation.accepted is True
        assert Membership.objects.filter(
            user=upper_user, academy=invitation.academy
        ).exists()


# ---------------------------------------------------------------------------
# Error State Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestInvitationErrorStates:
    """Test that invalid/expired/already-accepted invitations show correct error pages."""

    def test_invalid_token_shows_invalid_page(self, client):
        """A completely bogus token renders the invalid invitation page."""
        url = reverse("accept-invitation", kwargs={"token": "bogus-token-that-doesnt-exist"})
        response = client.get(url)

        assert response.status_code == 200
        assert b"invalid" in response.content.lower() or b"not found" in response.content.lower()

    def test_expired_invitation_shows_expired_page(self, client, expired_invitation):
        """An expired invitation renders the expired page."""
        url = reverse("accept-invitation", kwargs={"token": expired_invitation.token})
        response = client.get(url)

        assert response.status_code == 200
        assert b"expired" in response.content.lower()

    def test_already_accepted_invitation_shows_accepted_page(self, client, accepted_invitation):
        """An already-accepted invitation renders the already_accepted page."""
        url = reverse("accept-invitation", kwargs={"token": accepted_invitation.token})
        response = client.get(url)

        assert response.status_code == 200
        assert b"already" in response.content.lower()

    def test_duplicate_invitation_prevented(self, auth_client, academy, invitation):
        """Sending a second invitation to the same email is blocked."""
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        response = auth_client.post(url, {
            "email": invitation.email,
            "role": "student",
        })

        # Should redirect (non-HTMX) without creating a new invitation
        assert response.status_code == 302
        assert Invitation.objects.filter(
            email=invitation.email, academy=academy, accepted=False
        ).count() == 1  # still just the original

    def test_duplicate_invitation_prevented_htmx(self, auth_client, academy, invitation):
        """HTMX request for duplicate invitation returns partial with error."""
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        response = auth_client.post(
            url,
            {"email": invitation.email, "role": "student"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert "already been sent" in content

    def test_cannot_invite_existing_member(self, auth_client, academy, owner_user):
        """Cannot send invitation to someone who is already a member."""
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        response = auth_client.post(url, {
            "email": owner_user.email,
            "role": "student",
        })

        assert response.status_code == 302
        assert not Invitation.objects.filter(
            email=owner_user.email, academy=academy
        ).exists()

    def test_unauthenticated_post_redirects_to_login(self, client, invitation):
        """POST to accept-invitation without login redirects to login with ?next=."""
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.post(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url
        assert invitation.token in response.url

    def test_expired_invitation_post_shows_expired_page(self, client, expired_invitation, db):
        """POST to an expired invitation renders the expired page."""
        user = User.objects.create_user(
            username="expuser",
            email=expired_invitation.email,
            password="testpass123",
        )
        client.force_login(user)
        url = reverse("accept-invitation", kwargs={"token": expired_invitation.token})
        response = client.post(url)

        assert response.status_code == 200
        assert b"expired" in response.content.lower()


# ---------------------------------------------------------------------------
# Permission Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestInvitationPermissions:
    """Test that only owners can send/resend/cancel invitations."""

    def test_student_cannot_send_invitation(self, client, student_user, academy):
        """Student gets 403 when trying to invite a member."""
        client.force_login(student_user)
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        response = client.post(url, {
            "email": "hack@example.com",
            "role": "student",
        })
        assert response.status_code == 403

        # No invitation created
        assert not Invitation.objects.filter(email="hack@example.com").exists()

    def test_instructor_cannot_send_invitation(self, client, instructor_user, academy):
        """Instructor gets 403 when trying to invite a member."""
        client.force_login(instructor_user)
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        response = client.post(url, {
            "email": "hack@example.com",
            "role": "student",
        })
        assert response.status_code == 403

    def test_resend_invitation_works_for_owner(self, auth_client, academy, invitation):
        """Owner can resend a pending invitation, which updates token and expiry."""
        old_token = invitation.token
        old_expires = invitation.expires_at

        url = reverse("resend-invitation", kwargs={
            "slug": academy.slug,
            "pk": invitation.pk,
        })
        response = auth_client.post(url)
        assert response.status_code == 200

        invitation.refresh_from_db()
        assert invitation.token != old_token  # new token
        assert invitation.expires_at > old_expires  # extended expiry

        # Resend email sent
        assert len(mail.outbox) == 1
        assert invitation.email in mail.outbox[0].to

    def test_student_cannot_resend_invitation(self, client, student_user, academy, invitation):
        """Student gets 403 when trying to resend."""
        client.force_login(student_user)
        url = reverse("resend-invitation", kwargs={
            "slug": academy.slug,
            "pk": invitation.pk,
        })
        response = client.post(url)
        assert response.status_code == 403

    def test_cancel_invitation_works_for_owner(self, auth_client, academy, invitation):
        """Owner can cancel a pending invitation, which deletes it."""
        url = reverse("cancel-invitation", kwargs={
            "slug": academy.slug,
            "pk": invitation.pk,
        })
        response = auth_client.post(url)
        assert response.status_code == 200

        assert not Invitation.objects.filter(pk=invitation.pk).exists()

    def test_student_cannot_cancel_invitation(self, client, student_user, academy, invitation):
        """Student gets 403 when trying to cancel."""
        client.force_login(student_user)
        url = reverse("cancel-invitation", kwargs={
            "slug": academy.slug,
            "pk": invitation.pk,
        })
        response = client.post(url)
        assert response.status_code == 403

        # Invitation still exists
        assert Invitation.objects.filter(pk=invitation.pk).exists()


# ---------------------------------------------------------------------------
# ?next= Flow Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestNextUrlPreservation:
    """Test that ?next= is preserved through login/register links."""

    def test_login_page_preserves_next_in_register_link(self, client):
        """Login page's 'Register' link includes ?next= parameter."""
        next_url = "/invitation/some-token/accept/"
        response = client.get(f"{reverse('login')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()
        # The register link should include ?next=
        assert f"next={next_url}" in content or f"next=%2F" in content

    def test_register_page_preserves_next_in_login_link(self, client):
        """Register page's 'Sign In' link includes ?next= parameter."""
        next_url = "/invitation/some-token/accept/"
        response = client.get(f"{reverse('register')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()
        # The login link should include ?next=
        assert f"next={next_url}" in content or f"next=%2F" in content

    def test_register_redirects_to_next_url_after_signup(self, client):
        """After registration, user is redirected to the ?next= URL."""
        next_url = "/invitation/some-token/accept/"
        response = client.post(
            f"{reverse('register')}?next={next_url}",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
                "next": next_url,
            },
        )
        assert response.status_code == 302
        assert next_url in response.url

    def test_accept_invitation_get_shows_login_link_with_next(self, client, invitation):
        """Accept page for unauthenticated user shows login link with ?next=."""
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Login link should have ?next= pointing back to the accept URL
        assert f"/invitation/{invitation.token}/accept/" in content

    def test_accept_invitation_get_shows_register_link_with_next(self, client, invitation):
        """Accept page for unauthenticated user shows register link with ?next=."""
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Register link should have ?next= pointing back to the accept URL
        assert "register" in content.lower()
        assert invitation.token in content


# ---------------------------------------------------------------------------
# Invitation Acceptance — Idempotency / Edge Cases
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestInvitationEdgeCases:
    """Edge cases around invitation acceptance."""

    def test_accept_creates_membership_with_correct_role(self, client, academy, owner_user):
        """Invitation role propagates to the created Membership."""
        inv = Invitation.objects.create(
            academy=academy,
            email="instructor_invite@example.com",
            role="instructor",
            token=secrets.token_urlsafe(48),
            invited_by=owner_user,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        user = User.objects.create_user(
            username="newinstructor",
            email="instructor_invite@example.com",
            password="testpass123",
        )
        client.force_login(user)
        url = reverse("accept-invitation", kwargs={"token": inv.token})
        client.post(url)

        membership = Membership.objects.get(user=user, academy=academy)
        assert membership.role == "instructor"

    def test_accept_does_not_duplicate_membership(self, client, invitation, invited_user, academy):
        """If user already has a membership (edge case), get_or_create handles it."""
        # Pre-create membership
        Membership.objects.create(
            user=invited_user, academy=academy, role="student"
        )
        client.force_login(invited_user)
        url = reverse("accept-invitation", kwargs={"token": invitation.token})
        response = client.post(url)

        assert response.status_code == 302
        assert Membership.objects.filter(
            user=invited_user, academy=academy
        ).count() == 1  # no duplicate

    def test_htmx_invite_returns_partial(self, auth_client, academy):
        """HTMX invitation request returns the partial template."""
        url = reverse("academy-invite", kwargs={"slug": academy.slug})
        response = auth_client.post(
            url,
            {"email": "htmxuser@example.com", "role": "student"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        # Invitation created
        assert Invitation.objects.filter(
            email="htmxuser@example.com", academy=academy
        ).exists()
