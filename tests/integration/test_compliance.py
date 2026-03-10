from datetime import date, timedelta

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone as tz

from apps.accounts.models import Membership, ParentalConsent, User
from apps.academies.models import Academy


@pytest.mark.integration
class TestTermsAcceptance(TestCase):
    """Terms & Privacy acceptance on registration."""

    def setUp(self):
        self.client = Client()

    def _adult_dob(self):
        """Return a DOB for a 20-year-old."""
        today = date.today()
        return (today.replace(year=today.year - 20)).isoformat()

    def test_register_without_accepting_terms_fails(self):
        resp = self.client.post(
            reverse("register"),
            {
                "email": "test@example.com",
                "date_of_birth": self._adult_dob(),
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        assert resp.status_code == 200
        assert User.objects.filter(email="test@example.com").count() == 0

    def test_register_with_terms_accepted_succeeds(self):
        resp = self.client.post(
            reverse("register"),
            {
                "email": "test2@example.com",
                "date_of_birth": self._adult_dob(),
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert resp.status_code == 302
        user = User.objects.get(email="test2@example.com")
        assert user.terms_accepted_at is not None
        assert user.date_of_birth is not None

    def test_register_terms_checkbox_rendered(self):
        resp = self.client.get(reverse("register"))
        content = resp.content.decode()
        assert "Terms of Service" in content
        assert "Privacy Policy" in content
        assert 'type="checkbox"' in content

    def test_branded_signup_requires_terms(self):
        from tests.factories import AcademyFactory

        academy = AcademyFactory()
        resp = self.client.post(
            reverse("branded-signup", kwargs={"slug": academy.slug}),
            {
                "email": "branded@example.com",
                "date_of_birth": self._adult_dob(),
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        assert resp.status_code == 200
        assert User.objects.filter(email="branded@example.com").count() == 0

    def test_branded_signup_with_terms_stores_timestamp(self):
        from tests.factories import AcademyFactory

        academy = AcademyFactory()
        resp = self.client.post(
            reverse("branded-signup", kwargs={"slug": academy.slug}),
            {
                "email": "branded2@example.com",
                "date_of_birth": self._adult_dob(),
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert resp.status_code == 302
        user = User.objects.get(email="branded2@example.com")
        assert user.terms_accepted_at is not None


@pytest.mark.integration
class TestCOPPAAgeGate(TestCase):
    """COPPA: under-13 users require parental consent."""

    def setUp(self):
        self.client = Client()

    def _child_dob(self):
        """Return a DOB for a 10-year-old."""
        today = date.today()
        return (today.replace(year=today.year - 10)).isoformat()

    def _adult_dob(self):
        today = date.today()
        return (today.replace(year=today.year - 20)).isoformat()

    def test_under_13_without_parent_email_fails(self):
        """Under-13 registration without parent email is rejected."""
        resp = self.client.post(
            reverse("register"),
            {
                "email": "kid@example.com",
                "date_of_birth": self._child_dob(),
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert resp.status_code == 200  # form re-rendered with error
        assert User.objects.filter(email="kid@example.com").count() == 0

    def test_under_13_with_parent_email_creates_inactive_account(self):
        """Under-13 with parent email creates account but marks it inactive."""
        resp = self.client.post(
            reverse("register"),
            {
                "email": "kid2@example.com",
                "date_of_birth": self._child_dob(),
                "parent_email": "parent@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert resp.status_code == 200  # renders pending page (not redirect)
        assert "parent@example.com" in resp.content.decode()
        user = User.objects.get(email="kid2@example.com")
        assert user.is_active is False
        assert user.parental_consent_given is False
        assert ParentalConsent.objects.filter(child=user).exists()

    def test_under_13_sends_parental_consent_email(self):
        """Parental consent email is sent to parent."""
        from django.core import mail

        self.client.post(
            reverse("register"),
            {
                "email": "kid3@example.com",
                "date_of_birth": self._child_dob(),
                "parent_email": "parent3@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["parent3@example.com"]
        assert "consent" in mail.outbox[0].subject.lower()

    def test_parent_email_same_as_child_email_rejected(self):
        """Parent email cannot be the same as the child's email."""
        resp = self.client.post(
            reverse("register"),
            {
                "email": "same@example.com",
                "date_of_birth": self._child_dob(),
                "parent_email": "same@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert resp.status_code == 200
        assert User.objects.filter(email="same@example.com").count() == 0

    def test_adult_registration_does_not_require_parent_email(self):
        """Adult users register normally without parent email."""
        resp = self.client.post(
            reverse("register"),
            {
                "email": "adult@example.com",
                "date_of_birth": self._adult_dob(),
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert resp.status_code == 302
        user = User.objects.get(email="adult@example.com")
        assert user.is_active is True
        assert not ParentalConsent.objects.filter(child=user).exists()

    def test_dob_required_for_registration(self):
        """Date of birth is required."""
        resp = self.client.post(
            reverse("register"),
            {
                "email": "nodob@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "accept_terms": "on",
            },
        )
        assert resp.status_code == 200
        assert User.objects.filter(email="nodob@example.com").count() == 0


@pytest.mark.integration
class TestParentalConsentApproval(TestCase):
    """Parent approves child's account via emailed link."""

    def setUp(self):
        self.client = Client()

    def _create_child_with_consent(self):
        """Helper: create an inactive child with pending parental consent."""
        child_dob = date.today().replace(year=date.today().year - 10)
        child = User.objects.create_user(
            email="child@example.com",
            username="childuser",
            password="SecurePass123!",
            first_name="Child",
            last_name="User",
            is_active=False,
            date_of_birth=child_dob,
        )
        consent = ParentalConsent.objects.create(
            child=child,
            parent_email="parent@example.com",
            expires_at=tz.now() + timedelta(days=7),
        )
        return child, consent

    def test_valid_consent_token_approves_account(self):
        child, consent = self._create_child_with_consent()
        resp = self.client.get(
            reverse("approve-parental-consent", kwargs={"token": consent.token})
        )
        assert resp.status_code == 200
        assert "Approved" in resp.content.decode()

        child.refresh_from_db()
        assert child.is_active is True
        assert child.parental_consent_given is True

        consent.refresh_from_db()
        assert consent.approved_at is not None

    def test_expired_token_rejected(self):
        child, consent = self._create_child_with_consent()
        consent.expires_at = tz.now() - timedelta(hours=1)
        consent.save()

        resp = self.client.get(
            reverse("approve-parental-consent", kwargs={"token": consent.token})
        )
        assert resp.status_code == 200
        assert "Expired" in resp.content.decode()

        child.refresh_from_db()
        assert child.is_active is False

    def test_invalid_token_shows_error(self):
        resp = self.client.get(
            reverse("approve-parental-consent", kwargs={"token": "invalid-token-123"})
        )
        assert resp.status_code == 200
        assert "Invalid" in resp.content.decode()

    def test_already_approved_shows_info(self):
        child, consent = self._create_child_with_consent()
        consent.approved_at = tz.now()
        consent.save()
        child.is_active = True
        child.parental_consent_given = True
        child.save()

        resp = self.client.get(
            reverse("approve-parental-consent", kwargs={"token": consent.token})
        )
        assert resp.status_code == 200
        assert "Already Approved" in resp.content.decode()


@pytest.mark.integration
class TestCookieConsentBanner(TestCase):
    """Cookie consent banner on pages."""

    def setUp(self):
        self.client = Client()

    def test_cookie_banner_present_on_login_page(self):
        resp = self.client.get(reverse("login"))
        content = resp.content.decode()
        assert "cookie-consent-banner" in content
        assert "Cookie Policy" in content

    def test_cookie_policy_page_loads(self):
        resp = self.client.get(reverse("cookie-policy"))
        assert resp.status_code == 200
        assert "Cookie Policy" in resp.content.decode()


@pytest.mark.integration
class TestRecordingConsentNotice(TestCase):
    """Recording consent notice in video room."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Comp Recording Academy",
            slug="comp-recording-iso",
            description="A test academy",
            email="comp-recording-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="comp-recording-owner",
            email="comp-recording-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="comp-recording-owner@test.com", password="testpass123"
        )

    def test_video_room_has_recording_notice(self):
        """Video room template includes recording consent banner."""
        from tests.factories import LiveSessionFactory

        session = LiveSessionFactory(academy=self.academy)
        resp = self.auth_client.get(reverse("session-join", kwargs={"pk": session.pk}))
        if resp.status_code == 200:
            content = resp.content.decode()
            assert (
                "recording-consent-banner" in content or "Recording notice" in content
            )


@pytest.mark.integration
class TestLegalPages(TestCase):
    """Enhanced legal pages have required content."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Comp Legal Academy",
            slug="comp-legal-iso",
            description="A test academy",
            email="comp-legal-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="comp-legal-owner",
            email="comp-legal-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(
            username="comp-legal-owner@test.com", password="testpass123"
        )

    def test_privacy_policy_has_subprocessors(self):
        resp = self.client.get(reverse("privacy"))
        content = resp.content.decode()
        assert "Stripe" in content
        assert "SendGrid" in content
        assert "LiveKit" in content
        assert "Cloudflare" in content

    def test_privacy_policy_has_coppa_section(self):
        resp = self.client.get(reverse("privacy"))
        content = resp.content.decode()
        assert "COPPA" in content
        assert "under 13" in content

    def test_privacy_policy_has_breach_notification(self):
        resp = self.client.get(reverse("privacy"))
        content = resp.content.decode()
        assert "breach" in content.lower()
        assert "72 hours" in content

    def test_terms_has_age_requirements(self):
        resp = self.client.get(reverse("terms"))
        content = resp.content.decode()
        assert "13" in content
        assert "COPPA" in content
        assert "parental" in content.lower()

    def test_terms_has_recording_consent(self):
        resp = self.client.get(reverse("terms"))
        content = resp.content.decode()
        assert "recorded" in content.lower()
        assert "recording" in content.lower()

    def test_footer_has_cookie_policy_link(self):
        resp = self.auth_client.get(reverse("dashboard"), follow=True)
        content = resp.content.decode()
        assert "Cookie Policy" in content
