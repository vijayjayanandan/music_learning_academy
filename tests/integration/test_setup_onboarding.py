"""Integration tests for Sprint 5: Setup Wizard & Onboarding.

Tests the guided 5-step setup wizard (basics, branding, team, course, launch),
the setup checklist on the admin dashboard, the share link / QR code pages,
new Academy model fields (setup_status, currency, minor_mode_enabled), and
the academy-creation redirect to the wizard.

Covers:
- Model fields: defaults, choices, mutations
- Setup progress calculation (setup_progress property)
- Wizard access control (owner-only), step navigation, step POST advancement
- Dashboard setup checklist visibility and progress display
- Share link and QR code access control and content
- Currency form fields
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.academies.models import Academy
from apps.accounts.models import User, Membership


# ===================================================================
# TestAcademySetupFields — model-level defaults and choices
# ===================================================================


@pytest.mark.integration
class TestAcademySetupFields(TestCase):
    """Verify setup_status, currency, and minor_mode_enabled fields."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Setup Fields Academy",
            slug="setup-fields-academy",
            description="A test academy",
            email="setup-fields@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )

    def test_setup_status_default_is_new(self):
        """New academies should default to 'new' setup status."""
        academy = Academy.objects.create(
            name="Default Status", slug="default-status-ob"
        )
        assert academy.setup_status == "new"

    def test_setup_status_choices(self):
        """All expected status choices should exist."""
        choices = [c[0] for c in Academy.SetupStatus.choices]
        assert "new" in choices
        assert "basics_done" in choices
        assert "branding_done" in choices
        assert "team_invited" in choices
        assert "catalog_ready" in choices
        assert "live" in choices

    def test_currency_default_is_usd(self):
        """Academy currency should default to USD."""
        assert self.academy.currency == "USD"

    def test_minor_mode_default_is_false(self):
        """Minor mode should be disabled by default."""
        assert self.academy.minor_mode_enabled is False

    def test_currency_can_be_changed(self):
        """Currency field should accept a different ISO code and persist."""
        self.academy.currency = "EUR"
        self.academy.save()
        self.academy.refresh_from_db()
        assert self.academy.currency == "EUR"

    def test_minor_mode_can_be_enabled(self):
        """Minor mode should toggle to True and persist."""
        self.academy.minor_mode_enabled = True
        self.academy.save()
        self.academy.refresh_from_db()
        assert self.academy.minor_mode_enabled is True


# ===================================================================
# TestSetupProgress — property calculation
# ===================================================================


@pytest.mark.integration
class TestSetupProgress(TestCase):
    """Verify the setup_progress property returns correct (completed, total, pct)."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Progress Academy",
            slug="progress-academy-ob",
            description="A test academy",
            email="progress@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-progress-ob",
            email="owner-progress-ob@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="instructor-progress-ob",
            email="instructor-progress-ob@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor,
            academy=cls.academy,
            role="instructor",
            instruments=["Piano"],
        )

    def test_setup_progress_returns_tuple(self):
        """setup_progress should return a 3-tuple."""
        result = self.academy.setup_progress
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_setup_progress_total_is_five(self):
        """There should always be 5 setup progress steps."""
        _, total, _ = self.academy.setup_progress
        assert total == 5

    def test_setup_progress_empty_academy(self):
        """Academy with just a name and description should have basics done."""
        academy = Academy.objects.create(
            name="Progress Test",
            slug="progress-test-ob",
            description="Test description",
        )
        completed, total, pct = academy.setup_progress
        assert total == 5
        assert completed >= 1  # basics (name + description) should be true

    def test_setup_progress_with_branding_and_team(self):
        """Academy with custom branding + instructor should reflect in progress."""
        self.academy.description = "A full description"
        self.academy.primary_color = "#ff0000"
        self.academy.save()
        # instructor is already created in setUpTestData
        completed, _, _ = self.academy.setup_progress
        # basics (name+desc), branding (custom color), team (instructor exists)
        assert completed >= 3


# ===================================================================
# TestSetupWizard — access control, step rendering, step advancement
# ===================================================================


@pytest.mark.integration
class TestSetupWizard(TestCase):
    """Integration tests for SetupWizardView."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Wizard Academy",
            slug="wizard-academy-ob",
            description="A test academy",
            email="wizard@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-wizard-ob",
            email="owner-wizard-ob@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-wizard-ob",
            email="student-wizard-ob@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
            instruments=["Piano"],
            skill_level="beginner",
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-wizard-ob@test.com", password="testpass123"
        )
        self.anon_client = Client()

    def test_owner_can_access_wizard(self):
        """Owner should get 200 on the setup wizard page."""
        url = reverse("academy-setup", args=[self.academy.slug])
        response = self.auth_client.get(url)
        assert response.status_code == 200
        assert "Set Up" in response.content.decode()

    def test_student_cannot_access_wizard(self):
        """Students should get 403 (owner-only view)."""
        student_client = Client()
        student_client.login(
            username="student-wizard-ob@test.com", password="testpass123"
        )
        url = reverse("academy-setup", args=[self.academy.slug])
        response = student_client.get(url)
        assert response.status_code == 403

    def test_wizard_shows_basics_step_for_new_academy(self):
        """Wizard should show 'basics' step content for a new academy."""
        self.academy.setup_status = "new"
        self.academy.save()
        url = reverse("academy-setup", args=[self.academy.slug])
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Basic Information" in content

    def test_basics_step_post_advances_status(self):
        """Posting valid basics should advance setup_status to basics_done."""
        self.academy.setup_status = "new"
        self.academy.save()
        url = reverse("academy-setup-step", args=[self.academy.slug, "basics"])
        response = self.auth_client.post(
            url,
            {
                "name": self.academy.name,
                "description": "Updated description",
                "timezone": "UTC",
                "currency": "USD",
            },
        )
        assert response.status_code == 302
        assert "branding" in response.url
        self.academy.refresh_from_db()
        assert self.academy.setup_status == "basics_done"

    def test_branding_step_post_advances_status(self):
        """Posting valid branding should advance setup_status to branding_done."""
        self.academy.setup_status = "basics_done"
        self.academy.save()
        url = reverse("academy-setup-step", args=[self.academy.slug, "branding"])
        response = self.auth_client.post(
            url,
            {
                "primary_color": "#ff5733",
                "welcome_message": "Hello!",
            },
        )
        assert response.status_code == 302
        assert "team" in response.url
        self.academy.refresh_from_db()
        assert self.academy.setup_status == "branding_done"

    def test_team_step_skip_advances_status(self):
        """Posting team step (skip) should advance to team_invited."""
        self.academy.setup_status = "branding_done"
        self.academy.save()
        url = reverse("academy-setup-step", args=[self.academy.slug, "team"])
        response = self.auth_client.post(url)
        assert response.status_code == 302
        assert "course" in response.url
        self.academy.refresh_from_db()
        assert self.academy.setup_status == "team_invited"

    def test_course_step_skip_advances_status(self):
        """Skipping course step should advance to catalog_ready."""
        self.academy.setup_status = "team_invited"
        self.academy.save()
        url = reverse("academy-setup-step", args=[self.academy.slug, "course"])
        response = self.auth_client.post(url)
        assert response.status_code == 302
        assert "launch" in response.url
        self.academy.refresh_from_db()
        assert self.academy.setup_status == "catalog_ready"

    def test_launch_step_sets_live(self):
        """Launch should set status to live and redirect to dashboard."""
        self.academy.setup_status = "catalog_ready"
        self.academy.save()
        url = reverse("academy-setup-step", args=[self.academy.slug, "launch"])
        response = self.auth_client.post(url)
        assert response.status_code == 302
        self.academy.refresh_from_db()
        assert self.academy.setup_status == "live"

    def test_can_navigate_to_specific_step(self):
        """Owner should be able to jump to any step via URL."""
        url = reverse("academy-setup-step", args=[self.academy.slug, "launch"])
        response = self.auth_client.get(url)
        assert response.status_code == 200

    def test_create_academy_redirects_to_wizard(self):
        """Creating a new academy should redirect to setup wizard."""
        url = reverse("academy-create")
        response = self.auth_client.post(
            url,
            {
                "name": "Wizard Redirect Test",
                "description": "Test desc",
                "timezone": "UTC",
                "currency": "USD",
                "primary_color": "#6366f1",
            },
            follow=False,
        )
        assert response.status_code == 302
        assert "setup" in response.url


# ===================================================================
# TestDashboardSetupChecklist — checklist visibility and content
# ===================================================================


@pytest.mark.integration
class TestDashboardSetupChecklist(TestCase):
    """Verify the setup checklist card on the admin dashboard."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Checklist Academy",
            slug="checklist-academy-ob",
            description="A test academy",
            email="checklist@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-checklist-ob",
            email="owner-checklist-ob@test.com",
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
            username="owner-checklist-ob@test.com", password="testpass123"
        )

    def test_checklist_shown_when_setup_incomplete(self):
        """Dashboard should show checklist when academy is not live."""
        self.academy.setup_status = "new"
        self.academy.save()
        url = reverse("admin-dashboard")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Complete Your Setup" in content

    def test_checklist_hidden_when_live(self):
        """Dashboard should NOT show checklist when academy is live."""
        self.academy.setup_status = "live"
        self.academy.save()
        url = reverse("admin-dashboard")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Complete Your Setup" not in content

    def test_checklist_shows_progress_percentage(self):
        """Checklist should display a progress percentage."""
        self.academy.setup_status = "basics_done"
        self.academy.save()
        url = reverse("admin-dashboard")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "%" in content  # progress percentage shown somewhere


# ===================================================================
# TestShareLink — share page and QR code access control / content
# ===================================================================


@pytest.mark.integration
class TestShareLink(TestCase):
    """Integration tests for ShareLinkView and QRCodeView."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Share Link Academy",
            slug="share-link-academy-ob",
            description="A test academy",
            email="sharelink@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-share-ob",
            email="owner-share-ob@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-share-ob",
            email="student-share-ob@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
            instruments=["Piano"],
            skill_level="beginner",
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-share-ob@test.com", password="testpass123"
        )

    def test_owner_can_access_share_page(self):
        """Owner should get 200 on the share page."""
        url = reverse("academy-share", args=[self.academy.slug])
        response = self.auth_client.get(url)
        assert response.status_code == 200
        assert "Share" in response.content.decode()

    def test_share_page_contains_signup_url(self):
        """Share page should contain the branded signup URL."""
        url = reverse("academy-share", args=[self.academy.slug])
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert f"/join/{self.academy.slug}/" in content

    def test_student_cannot_access_share_page(self):
        """Students should get 403 on the share page."""
        student_client = Client()
        student_client.login(
            username="student-share-ob@test.com", password="testpass123"
        )
        url = reverse("academy-share", args=[self.academy.slug])
        response = student_client.get(url)
        assert response.status_code == 403

    def test_qr_code_returns_png(self):
        """QR code endpoint should return an image/png response."""
        url = reverse("academy-qr-code", args=[self.academy.slug])
        response = self.auth_client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"

    def test_student_cannot_access_qr_code(self):
        """Students should get 403 on the QR code endpoint."""
        student_client = Client()
        student_client.login(
            username="student-share-ob@test.com", password="testpass123"
        )
        url = reverse("academy-qr-code", args=[self.academy.slug])
        response = student_client.get(url)
        assert response.status_code == 403


# ===================================================================
# TestCurrencyForm — currency field on academy forms
# ===================================================================


@pytest.mark.integration
class TestCurrencyForm(TestCase):
    """Verify currency field exists on relevant academy forms."""

    def test_currency_in_academy_form(self):
        """AcademyForm should include the currency field."""
        from apps.academies.forms import AcademyForm

        form = AcademyForm()
        assert "currency" in form.fields

    def test_basics_form_has_currency(self):
        """AcademyBasicsForm (wizard step 1) should include the currency field."""
        from apps.academies.forms import AcademyBasicsForm

        form = AcademyBasicsForm()
        assert "currency" in form.fields

    def test_branding_form_has_no_currency(self):
        """AcademyBrandingForm should NOT include currency (that is in basics)."""
        from apps.academies.forms import AcademyBrandingForm

        form = AcademyBrandingForm()
        assert "currency" not in form.fields
