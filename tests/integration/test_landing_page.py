"""Integration tests for the public academy landing page (/join/<slug>/).

Tests the BrandedSignupView which serves as both a marketing landing page
and a registration form for new students joining a specific academy.

Covers:
- Happy path (page loads, sections render, branding applied)
- Security / boundary (unpublished courses hidden, no email leaks, 404, auth redirect)
- Empty states (sections hidden when no data)
- Form behavior (errors re-render full page)
- SEO (meta tags)
"""

import pytest
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import Membership, User
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.payments.models import SubscriptionPlan, PackageDeal
from tests.factories import (
    CourseFactory,
    MembershipFactory,
    UserFactory,
)


@pytest.mark.integration
class TestAcademyLandingPage(TestCase):
    """Integration tests for the public academy landing page (/join/<slug>/).

    Uses setUpTestData to create a generic academy once for all tests.
    Tests that require a uniquely configured academy create their own objects
    inside the test method.
    """

    @classmethod
    def setUpTestData(cls):
        """Create a generic academy shared across tests that need no special attributes."""
        cls.academy = Academy.objects.create(
            name="Harmony Music School",
            slug="lp-academylandingpage-iso",
            description="A test academy",
            email="lp-iso@example.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )

    def setUp(self):
        """Clear cache and create a fresh client before each test."""
        cache.clear()
        self.client = Client()

    # -------------------------------------------------------------------
    # Happy path tests
    # -------------------------------------------------------------------

    def test_landing_page_loads_with_academy_data(self):
        """GET /join/<slug>/ returns 200 and shows the academy name."""
        url = reverse("branded-signup", args=[self.academy.slug])
        response = self.client.get(url)

        assert response.status_code == 200
        assert "Harmony Music School" in response.content.decode()

    def test_landing_page_shows_welcome_message(self):
        """Academy welcome_message appears on the landing page."""
        academy = Academy.objects.create(
            name="Welcome Academy",
            slug="lp-welcome-msg-iso",
            email="lp-welcome@example.com",
            timezone="UTC",
            welcome_message="Welcome to our school!",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        assert response.status_code == 200
        assert "Welcome to our school!" in response.content.decode()

    def test_landing_page_shows_description_fallback(self):
        """When no welcome_message is set, the academy description is shown instead."""
        academy = Academy.objects.create(
            name="Description Academy",
            slug="lp-desc-fallback-iso",
            email="lp-desc@example.com",
            timezone="UTC",
            description="Premier music education since 2020",
            welcome_message="",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Premier music education since 2020" in content

    def test_landing_page_shows_default_fallback_when_no_message_or_description(self):
        """Brand-new academy with no welcome_message or description shows default text."""
        academy = Academy.objects.create(
            name="Empty Academy",
            slug="lp-empty-fallback-iso",
            email="lp-empty@example.com",
            timezone="UTC",
            welcome_message="",
            description="",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Start your music journey with us" in content

    def test_landing_page_shows_published_courses(self):
        """Published courses appear on the landing page."""
        instructor = UserFactory()
        CourseFactory(
            academy=self.academy,
            title="Guitar Fundamentals",
            instructor=instructor,
            is_published=True,
        )
        CourseFactory(
            academy=self.academy,
            title="Piano Masterclass",
            instructor=instructor,
            is_published=True,
        )

        url = reverse("branded-signup", args=[self.academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Guitar Fundamentals" in content
        assert "Piano Masterclass" in content

    def test_landing_page_shows_instructors(self):
        """Instructors with bios appear on the landing page."""
        instructor = UserFactory(first_name="Sarah", last_name="Johnson")
        MembershipFactory(
            user=instructor,
            academy=self.academy,
            role="instructor",
            is_active=True,
            bio="Jazz pianist with 20 years of experience",
        )

        url = reverse("branded-signup", args=[self.academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Sarah Johnson" in content
        assert "Jazz pianist with 20 years of experience" in content

    def test_landing_page_shows_pricing(self):
        """Subscription plans and package deals appear on the landing page."""
        SubscriptionPlan.objects.create(
            academy=self.academy,
            name="Pro Monthly",
            price_cents=2999,
            billing_cycle="monthly",
            is_active=True,
        )
        PackageDeal.objects.create(
            academy=self.academy,
            name="10-Lesson Bundle",
            price_cents=19999,
            total_credits=10,
            is_active=True,
        )

        url = reverse("branded-signup", args=[self.academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Pro Monthly" in content
        assert "10-Lesson Bundle" in content
        # Check that the pricing section heading is present
        assert "Pricing" in content

    def test_landing_page_uses_primary_color(self):
        """The academy's primary_color hex code appears in the rendered page."""
        academy = Academy.objects.create(
            name="Color Academy",
            slug="lp-primary-color-iso",
            email="lp-color@example.com",
            timezone="UTC",
            primary_color="#e11d48",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        assert "#e11d48" in response.content.decode()

    # -------------------------------------------------------------------
    # Security / boundary tests
    # -------------------------------------------------------------------

    def test_landing_page_excludes_unpublished_courses(self):
        """Unpublished (draft) courses do not appear on the landing page."""
        instructor = UserFactory()
        CourseFactory(
            academy=self.academy,
            title="Visible Course",
            instructor=instructor,
            is_published=True,
        )
        CourseFactory(
            academy=self.academy,
            title="Draft Secret Course",
            instructor=instructor,
            is_published=False,
        )

        url = reverse("branded-signup", args=[self.academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Visible Course" in content
        assert "Draft Secret Course" not in content

    def test_landing_page_does_not_expose_instructor_emails(self):
        """Instructor email addresses must NOT appear on the public landing page."""
        instructor = UserFactory(
            first_name="David",
            last_name="Smith",
            email="david.secret@instructor.com",
        )
        MembershipFactory(
            user=instructor,
            academy=self.academy,
            role="instructor",
            is_active=True,
        )

        url = reverse("branded-signup", args=[self.academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "David Smith" in content
        assert "david.secret@instructor.com" not in content

    def test_landing_page_404_for_nonexistent_slug(self):
        """GET /join/nonexistent/ returns 404."""
        url = reverse("branded-signup", args=["nonexistent"])
        response = self.client.get(url)

        assert response.status_code == 404

    def test_landing_page_redirects_authenticated_user(self):
        """Authenticated user visiting /join/<slug>/ gets membership created and redirected."""
        academy = Academy.objects.create(
            name="Redirect Academy",
            slug="lp-auth-redirect-iso",
            email="lp-redirect@example.com",
            timezone="UTC",
        )
        user = User.objects.create_user(
            username="lp-redirect-user",
            email="lp-redirect-user@test.com",
            password="testpass123",
        )

        self.client.force_login(user)

        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        # Should redirect to dashboard
        assert response.status_code == 302
        assert reverse("dashboard") in response.url

        # Membership should have been created
        assert Membership.objects.filter(
            user=user, academy=academy, role="student"
        ).exists()

        # User's current_academy should be set
        user.refresh_from_db()
        assert user.current_academy == academy

    # -------------------------------------------------------------------
    # Empty state tests
    # -------------------------------------------------------------------

    def test_landing_page_hides_courses_section_when_empty(self):
        """When the academy has no published courses, the courses section is hidden."""
        academy = Academy.objects.create(
            name="Empty Courses Academy",
            slug="lp-empty-courses-iso",
            email="lp-empty-courses@example.com",
            timezone="UTC",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "What You'll Learn" not in content

    def test_landing_page_hides_instructors_section_when_empty(self):
        """When the academy has no instructors, the instructors section is hidden."""
        academy = Academy.objects.create(
            name="Empty Instructors Academy",
            slug="lp-empty-instructors-iso",
            email="lp-empty-instructors@example.com",
            timezone="UTC",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Meet Our Instructors" not in content

    def test_landing_page_hides_pricing_section_when_empty(self):
        """When the academy has no plans or packages, the pricing section is hidden."""
        academy = Academy.objects.create(
            name="No Plans Academy",
            slug="lp-empty-pricing-iso",
            email="lp-empty-pricing@example.com",
            timezone="UTC",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        assert "Pricing" not in content

    # -------------------------------------------------------------------
    # Form behavior tests
    # -------------------------------------------------------------------

    def test_landing_page_form_error_rerenders_full_page(self):
        """Invalid form submission re-renders the full landing page with all sections."""
        instructor = UserFactory()
        CourseFactory(
            academy=self.academy,
            title="Course That Should Reappear",
            instructor=instructor,
            is_published=True,
        )

        url = reverse("branded-signup", args=[self.academy.slug])

        # POST with missing required fields (no password, no accept_terms)
        response = self.client.post(url, {
            "email": "incomplete@test.com",
        })

        # Should re-render the page (not redirect)
        assert response.status_code == 200
        content = response.content.decode()

        # Course section should still appear in the re-rendered page
        assert "Course That Should Reappear" in content
        # Academy name should still appear
        assert self.academy.name in content

    def test_landing_page_renders_django_messages_on_capacity_error(self):
        """Capacity error message renders on the unauthenticated landing page after redirect."""
        from unittest.mock import patch

        academy = Academy.objects.create(
            name="Capacity Academy",
            slug="lp-capacity-iso",
            email="lp-capacity@example.com",
            timezone="UTC",
        )
        url = reverse("branded-signup", args=[academy.slug])

        # POST a valid registration form while academy is at capacity
        # The view calls check_seat_limit() and redirects with messages.error()
        with patch(
            "apps.academies.views.check_seat_limit",
            return_value=(False, 10, 10),
        ):
            response = self.client.post(
                url,
                {
                    "email": "newstudent@test.com",
                    "date_of_birth": "2000-01-01",
                    "password1": "SecurePass123!",
                    "password2": "SecurePass123!",
                    "accept_terms": "on",
                },
                follow=True,
            )

        content = response.content.decode()
        assert "at capacity" in content
        assert "alert-error" in content

    # -------------------------------------------------------------------
    # SEO tests
    # -------------------------------------------------------------------

    def test_landing_page_has_seo_meta_tags(self):
        """The landing page includes meta description and Open Graph title."""
        academy = Academy.objects.create(
            name="Stellar Music Academy",
            slug="lp-seo-metatags-iso",
            email="lp-seo@example.com",
            timezone="UTC",
            description="World-class music education",
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)

        content = response.content.decode()
        # Check for meta description (from template: academy.welcome_message or description)
        assert "meta" in content.lower()
        assert "World-class music education" in content
        # Check for Open Graph title
        assert "og:title" in content
        assert "Stellar Music Academy" in content
