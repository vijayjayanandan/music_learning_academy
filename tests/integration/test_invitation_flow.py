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
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Invitation, Membership, User
from apps.academies.models import Academy
from apps.notifications.models import Notification


# ---------------------------------------------------------------------------
# Happy Path Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestInviteMemberHappyPath(TestCase):
    """Test that an owner can send an invitation."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Invite Happy Academy",
            slug="inv-happy-academy",
            description="A test academy",
            email="inv-happy@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="inv-happy-owner",
            email="inv-happy-owner@test.com",
            password="testpass123",
            first_name="Happy",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="inv-happy-owner@test.com", password="testpass123")

    def test_owner_can_send_invitation(self):
        """Owner sends an invitation; Invitation record is created and email sent."""
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        response = self.auth_client.post(url, {
            "email": "newuser@example.com",
            "role": "student",
        })
        # Should redirect back to members page (non-HTMX request)
        assert response.status_code == 302

        # Invitation record created
        inv = Invitation.objects.get(email="newuser@example.com", academy=self.academy)
        assert inv.role == "student"
        assert inv.accepted is False
        assert inv.token  # non-empty token
        assert inv.expires_at > timezone.now()

        # Invitation email sent
        assert len(mail.outbox) == 1
        assert "newuser@example.com" in mail.outbox[0].to
        assert self.academy.name in mail.outbox[0].subject

    def test_owner_can_send_instructor_invitation(self):
        """Owner can invite an instructor (not just students)."""
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        self.auth_client.post(url, {
            "email": "prof@example.com",
            "role": "instructor",
        })
        inv = Invitation.objects.get(email="prof@example.com", academy=self.academy)
        assert inv.role == "instructor"


@pytest.mark.integration
class TestAcceptInvitationHappyPath(TestCase):
    """Test the full accept-invitation flow for a logged-in user."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Invite Accept Academy",
            slug="inv-accept-academy",
            description="A test academy",
            email="inv-accept@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="inv-accept-owner",
            email="inv-accept-owner@test.com",
            password="testpass123",
            first_name="Accept",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-accept-invited@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        cls.invited_user = User.objects.create_user(
            username="inv-accept-inviteduser",
            email="inv-accept-invited@example.com",
            password="testpass123",
            first_name="Invited",
            last_name="User",
        )

    def setUp(self):
        self.client = Client()

    def test_accept_invitation_get_renders_page(self):
        """GET request shows the accept-invitation page."""
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.get(url)
        assert response.status_code == 200
        assert self.invitation.academy.name.encode() in response.content

    def test_logged_in_user_can_accept_invitation(self):
        """Matching user accepts invitation and becomes a member."""
        self.client.force_login(self.invited_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.post(url)

        # Redirects to dashboard
        assert response.status_code == 302
        assert reverse("dashboard") in response.url

        # Membership created
        assert Membership.objects.filter(
            user=self.invited_user,
            academy=self.invitation.academy,
            role="student",
        ).exists()

        # Invitation marked as accepted
        self.invitation.refresh_from_db()
        assert self.invitation.accepted is True

        # User's current_academy set
        self.invited_user.refresh_from_db()
        assert self.invited_user.current_academy == self.invitation.academy

    def test_welcome_email_sent_after_acceptance(self):
        """A welcome email is sent to the user after accepting."""
        self.client.force_login(self.invited_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        self.client.post(url)

        # Welcome email is the first (and only) email sent on acceptance
        assert len(mail.outbox) == 1
        welcome_email = mail.outbox[0]
        assert self.invited_user.email in welcome_email.to
        assert "Welcome" in welcome_email.subject
        assert self.invitation.academy.name in welcome_email.subject

    def test_owner_notification_created_after_acceptance(self):
        """Owner gets a notification when an invitation is accepted."""
        self.client.force_login(self.invited_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        self.client.post(url)

        notifications = Notification.objects.filter(
            recipient=self.owner,
            academy=self.invitation.academy,
            notification_type="invitation",
        )
        assert notifications.count() == 1
        assert "accepted" in notifications.first().message.lower()

    def test_success_message_set_after_acceptance(self):
        """A success flash message is set after acceptance."""
        self.client.force_login(self.invited_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.post(url, follow=True)

        # Check messages framework
        messages_list = list(response.context["messages"])
        assert len(messages_list) >= 1
        assert "Welcome" in str(messages_list[0])


# ---------------------------------------------------------------------------
# Email Match Enforcement (DEBT-003)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestEmailMatchEnforcement(TestCase):
    """Test that only the invited email can accept the invitation."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Email Match Academy",
            slug="inv-email-match-academy",
            description="A test academy",
            email="inv-email-match@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="inv-email-match-owner",
            email="inv-email-match-owner@test.com",
            password="testpass123",
            first_name="Match",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-email-match-invited@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        cls.invited_user = User.objects.create_user(
            username="inv-email-match-inviteduser",
            email="inv-email-match-invited@example.com",
            password="testpass123",
            first_name="Invited",
            last_name="User",
        )
        cls.wrong_email_user = User.objects.create_user(
            username="inv-email-match-wronguser",
            email="inv-email-match-wrong@example.com",
            password="testpass123",
            first_name="Wrong",
            last_name="User",
        )

    def setUp(self):
        self.client = Client()

    def test_matching_email_can_accept(self):
        """User whose email matches the invitation can accept."""
        self.client.force_login(self.invited_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.post(url)

        assert response.status_code == 302  # redirect to dashboard
        self.invitation.refresh_from_db()
        assert self.invitation.accepted is True

    def test_non_matching_email_sees_error_page(self):
        """User with different email sees the email_mismatch error page."""
        self.client.force_login(self.wrong_email_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.post(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Should render the email_mismatch template
        assert "mismatch" in content.lower() or self.wrong_email_user.email in content

        # Invitation should NOT be accepted
        self.invitation.refresh_from_db()
        assert self.invitation.accepted is False

        # No membership should be created
        assert not Membership.objects.filter(
            user=self.wrong_email_user, academy=self.invitation.academy
        ).exists()

    def test_email_comparison_is_case_insensitive(self):
        """Email match ignores case: INVITED@EXAMPLE.COM matches invited@example.com."""
        # Create user with uppercased email — test-specific object, stays in test body
        upper_user = User.objects.create_user(
            username="inv-email-match-upperuser",
            email="INV-EMAIL-MATCH-INVITED@EXAMPLE.COM",
            password="testpass123",
        )
        self.client.force_login(upper_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.post(url)

        # Should succeed (redirect to dashboard)
        assert response.status_code == 302
        self.invitation.refresh_from_db()
        assert self.invitation.accepted is True
        assert Membership.objects.filter(
            user=upper_user, academy=self.invitation.academy
        ).exists()


# ---------------------------------------------------------------------------
# Error State Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestInvitationErrorStates(TestCase):
    """Test that invalid/expired/already-accepted invitations show correct error pages."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Error States Academy",
            slug="inv-error-academy",
            description="A test academy",
            email="inv-error@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="inv-error-owner",
            email="inv-error-owner@test.com",
            password="testpass123",
            first_name="Error",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        # Pending invitation (for duplicate/unauthenticated tests)
        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-error-invited@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        # Expired invitation
        cls.expired_invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-error-expired@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        # Already-accepted invitation
        cls.accepted_invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-error-accepted@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            accepted=True,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(username="inv-error-owner@test.com", password="testpass123")

    def test_invalid_token_shows_invalid_page(self):
        """A completely bogus token renders the invalid invitation page."""
        url = reverse("accept-invitation", kwargs={"token": "bogus-token-that-doesnt-exist"})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"invalid" in response.content.lower() or b"not found" in response.content.lower()

    def test_expired_invitation_shows_expired_page(self):
        """An expired invitation renders the expired page."""
        url = reverse("accept-invitation", kwargs={"token": self.expired_invitation.token})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"expired" in response.content.lower()

    def test_already_accepted_invitation_shows_accepted_page(self):
        """An already-accepted invitation renders the already_accepted page."""
        url = reverse("accept-invitation", kwargs={"token": self.accepted_invitation.token})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"already" in response.content.lower()

    def test_duplicate_invitation_prevented(self):
        """Sending a second invitation to the same email is blocked."""
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        response = self.auth_client.post(url, {
            "email": self.invitation.email,
            "role": "student",
        })

        # Should redirect (non-HTMX) without creating a new invitation
        assert response.status_code == 302
        assert Invitation.objects.filter(
            email=self.invitation.email, academy=self.academy, accepted=False
        ).count() == 1  # still just the original

    def test_duplicate_invitation_prevented_htmx(self):
        """HTMX request for duplicate invitation returns partial with error."""
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        response = self.auth_client.post(
            url,
            {"email": self.invitation.email, "role": "student"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert "already been sent" in content

    def test_cannot_invite_existing_member(self):
        """Cannot send invitation to someone who is already a member."""
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        response = self.auth_client.post(url, {
            "email": self.owner.email,
            "role": "student",
        })

        assert response.status_code == 302
        assert not Invitation.objects.filter(
            email=self.owner.email, academy=self.academy
        ).exists()

    def test_unauthenticated_post_redirects_to_login(self):
        """POST to accept-invitation without login redirects to login with ?next=."""
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.post(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url
        assert self.invitation.token in response.url

    def test_expired_invitation_post_shows_expired_page(self):
        """POST to an expired invitation renders the expired page."""
        # Test-specific user — created inline because it belongs to this single test
        user = User.objects.create_user(
            username="inv-error-expuser",
            email=self.expired_invitation.email,
            password="testpass123",
        )
        self.client.force_login(user)
        url = reverse("accept-invitation", kwargs={"token": self.expired_invitation.token})
        response = self.client.post(url)

        assert response.status_code == 200
        assert b"expired" in response.content.lower()


# ---------------------------------------------------------------------------
# Permission Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestInvitationPermissions(TestCase):
    """Test that only owners can send/resend/cancel invitations."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Permissions Academy",
            slug="inv-perms-academy",
            description="A test academy",
            email="inv-perms@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="inv-perms-owner",
            email="inv-perms-owner@test.com",
            password="testpass123",
            first_name="Perms",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="inv-perms-instructor",
            email="inv-perms-instructor@test.com",
            password="testpass123",
            first_name="Perms",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor",
            instruments=["Piano"],
        )

        cls.student = User.objects.create_user(
            username="inv-perms-student",
            email="inv-perms-student@test.com",
            password="testpass123",
            first_name="Perms",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student, academy=cls.academy, role="student",
            instruments=["Piano"], skill_level="beginner",
        )

        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-perms-invited@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(username="inv-perms-owner@test.com", password="testpass123")

    def test_student_cannot_send_invitation(self):
        """Student gets 403 when trying to invite a member."""
        self.client.force_login(self.student)
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        response = self.client.post(url, {
            "email": "hack@example.com",
            "role": "student",
        })
        assert response.status_code == 403

        # No invitation created
        assert not Invitation.objects.filter(email="hack@example.com").exists()

    def test_instructor_cannot_send_invitation(self):
        """Instructor gets 403 when trying to invite a member."""
        self.client.force_login(self.instructor)
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        response = self.client.post(url, {
            "email": "hack@example.com",
            "role": "student",
        })
        assert response.status_code == 403

    def test_resend_invitation_works_for_owner(self):
        """Owner can resend a pending invitation, which updates token and expiry."""
        old_token = self.invitation.token
        old_expires = self.invitation.expires_at

        url = reverse("resend-invitation", kwargs={
            "slug": self.academy.slug,
            "pk": self.invitation.pk,
        })
        response = self.auth_client.post(url)
        assert response.status_code == 200

        self.invitation.refresh_from_db()
        assert self.invitation.token != old_token  # new token
        assert self.invitation.expires_at > old_expires  # extended expiry

        # Resend email sent
        assert len(mail.outbox) == 1
        assert self.invitation.email in mail.outbox[0].to

    def test_student_cannot_resend_invitation(self):
        """Student gets 403 when trying to resend."""
        self.client.force_login(self.student)
        url = reverse("resend-invitation", kwargs={
            "slug": self.academy.slug,
            "pk": self.invitation.pk,
        })
        response = self.client.post(url)
        assert response.status_code == 403

    def test_cancel_invitation_works_for_owner(self):
        """Owner can cancel a pending invitation, which deletes it."""
        url = reverse("cancel-invitation", kwargs={
            "slug": self.academy.slug,
            "pk": self.invitation.pk,
        })
        response = self.auth_client.post(url)
        assert response.status_code == 200

        assert not Invitation.objects.filter(pk=self.invitation.pk).exists()

    def test_student_cannot_cancel_invitation(self):
        """Student gets 403 when trying to cancel."""
        self.client.force_login(self.student)
        url = reverse("cancel-invitation", kwargs={
            "slug": self.academy.slug,
            "pk": self.invitation.pk,
        })
        response = self.client.post(url)
        assert response.status_code == 403

        # Invitation still exists
        assert Invitation.objects.filter(pk=self.invitation.pk).exists()


# ---------------------------------------------------------------------------
# ?next= Flow Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestNextUrlPreservation(TestCase):
    """Test that ?next= is preserved through login/register links."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Next URL Academy",
            slug="inv-next-academy",
            description="A test academy",
            email="inv-next@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="inv-next-owner",
            email="inv-next-owner@test.com",
            password="testpass123",
            first_name="Next",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-next-invited@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

    def setUp(self):
        self.client = Client()

    def test_login_page_preserves_next_in_register_link(self):
        """Login page's 'Register' link includes ?next= parameter."""
        next_url = "/invitation/some-token/accept/"
        response = self.client.get(f"{reverse('login')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()
        # The register link should include ?next=
        assert f"next={next_url}" in content or f"next=%2F" in content

    def test_register_page_preserves_next_in_login_link(self):
        """Register page's 'Sign In' link includes ?next= parameter."""
        next_url = "/invitation/some-token/accept/"
        response = self.client.get(f"{reverse('register')}?next={next_url}")

        assert response.status_code == 200
        content = response.content.decode()
        # The login link should include ?next=
        assert f"next={next_url}" in content or f"next=%2F" in content

    def test_register_redirects_to_next_url_after_signup(self):
        """After registration, user is redirected to the ?next= URL."""
        next_url = "/invitation/some-token/accept/"
        response = self.client.post(
            f"{reverse('register')}?next={next_url}",
            {
                "email": "inv-next-newuser@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "date_of_birth": "2000-01-01",
                "accept_terms": "on",
                "next": next_url,
            },
        )
        assert response.status_code == 302
        assert next_url in response.url

    def test_accept_invitation_get_shows_login_link_with_next(self):
        """Accept page for unauthenticated user shows login link with ?next=."""
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Login link should have ?next= pointing back to the accept URL
        assert f"/invitation/{self.invitation.token}/accept/" in content

    def test_accept_invitation_get_shows_register_link_with_next(self):
        """Accept page for unauthenticated user shows register link with ?next=."""
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Register link should have ?next= pointing back to the accept URL
        assert "register" in content.lower()
        assert self.invitation.token in content


# ---------------------------------------------------------------------------
# Invitation Acceptance — Idempotency / Edge Cases
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestInvitationEdgeCases(TestCase):
    """Edge cases around invitation acceptance."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Edge Cases Academy",
            slug="inv-edge-academy",
            description="A test academy",
            email="inv-edge@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="inv-edge-owner",
            email="inv-edge-owner@test.com",
            password="testpass123",
            first_name="Edge",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.invitation = Invitation.objects.create(
            academy=cls.academy,
            email="inv-edge-invited@example.com",
            role="student",
            token=secrets.token_urlsafe(48),
            invited_by=cls.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        cls.invited_user = User.objects.create_user(
            username="inv-edge-inviteduser",
            email="inv-edge-invited@example.com",
            password="testpass123",
            first_name="Invited",
            last_name="User",
        )

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(username="inv-edge-owner@test.com", password="testpass123")

    def test_accept_creates_membership_with_correct_role(self):
        """Invitation role propagates to the created Membership."""
        # Test-specific invitation + user — created inline because unique to this test
        inv = Invitation.objects.create(
            academy=self.academy,
            email="inv-edge-instructor-invite@example.com",
            role="instructor",
            token=secrets.token_urlsafe(48),
            invited_by=self.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        user = User.objects.create_user(
            username="inv-edge-newinstructor",
            email="inv-edge-instructor-invite@example.com",
            password="testpass123",
        )
        self.client.force_login(user)
        url = reverse("accept-invitation", kwargs={"token": inv.token})
        self.client.post(url)

        membership = Membership.objects.get(user=user, academy=self.academy)
        assert membership.role == "instructor"

    def test_accept_does_not_duplicate_membership(self):
        """If user already has a membership (edge case), get_or_create handles it."""
        # Pre-create membership
        Membership.objects.create(
            user=self.invited_user, academy=self.academy, role="student"
        )
        self.client.force_login(self.invited_user)
        url = reverse("accept-invitation", kwargs={"token": self.invitation.token})
        response = self.client.post(url)

        assert response.status_code == 302
        assert Membership.objects.filter(
            user=self.invited_user, academy=self.academy
        ).count() == 1  # no duplicate

    def test_htmx_invite_returns_partial(self):
        """HTMX invitation request returns the partial template."""
        url = reverse("academy-invite", kwargs={"slug": self.academy.slug})
        response = self.auth_client.post(
            url,
            {"email": "inv-edge-htmxuser@example.com", "role": "student"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        # Invitation created
        assert Invitation.objects.filter(
            email="inv-edge-htmxuser@example.com", academy=self.academy
        ).exists()
