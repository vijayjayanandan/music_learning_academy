"""
End-to-end payment journey integration tests.

Tests the full Priya's Mom journey: course discovery → price visible →
checkout → webhook → enrollment created → student can access lessons.

Also covers individual task validations for the payment flow sprint.
"""

import pytest
from unittest.mock import MagicMock
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.payments.models import (
    Payment,
    PackageDeal,
)


# =========================================================================
# Task 1: Payment gating on EnrollView
# =========================================================================


@pytest.mark.integration
class TestEnrollmentPaymentGating(TestCase):
    """Paid courses redirect to checkout; free courses enroll directly."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Payment Gating Academy",
            slug="pay-gating-iso",
            description="A test academy",
            email="pay-gating-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-gating-iso",
            email="instructor-gating-iso@test.com",
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

        cls.student = User.objects.create_user(
            username="student-gating-iso",
            email="student-gating-iso@test.com",
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

        cls.free_course = Course.objects.create(
            academy=cls.academy,
            title="Free Guitar Basics",
            slug="pay-gating-free-guitar",
            instructor=cls.instructor,
            instrument="Guitar",
            difficulty_level="beginner",
            price_cents=0,
            is_published=True,
        )
        cls.paid_course = Course.objects.create(
            academy=cls.academy,
            title="Advanced Piano Masterclass",
            slug="pay-gating-advanced-piano",
            instructor=cls.instructor,
            instrument="Piano",
            difficulty_level="advanced",
            price_cents=2999,
            is_published=True,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="student-gating-iso@test.com", password="testpass123"
        )

    def test_free_course_enrollment_works_directly(self):
        """Happy path: free course creates enrollment without payment."""
        self.student_client.post(reverse("enroll", args=[self.free_course.slug]))
        assert Enrollment.objects.filter(
            student__email="student-gating-iso@test.com", course=self.free_course
        ).exists()

    def test_paid_course_redirects_to_checkout(self):
        """Boundary: paid course redirects to checkout, no enrollment created."""
        response = self.student_client.post(
            reverse("enroll", args=[self.paid_course.slug])
        )
        assert response.status_code == 302
        assert "checkout/course/pay-gating-advanced-piano" in response.url
        assert not Enrollment.objects.filter(
            student__email="student-gating-iso@test.com", course=self.paid_course
        ).exists()


# =========================================================================
# Task 2: Price display on course cards
# =========================================================================


@pytest.mark.integration
class TestCoursePriceDisplay(TestCase):
    """Course cards and detail pages show correct price."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Price Display Academy",
            slug="pay-price-iso",
            description="A test academy",
            email="pay-price-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-price-iso",
            email="instructor-price-iso@test.com",
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

        cls.student = User.objects.create_user(
            username="student-price-iso",
            email="student-price-iso@test.com",
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

        cls.free_course = Course.objects.create(
            academy=cls.academy,
            title="Free Guitar Basics",
            slug="pay-price-free-guitar",
            instructor=cls.instructor,
            instrument="Guitar",
            difficulty_level="beginner",
            price_cents=0,
            is_published=True,
        )
        cls.paid_course = Course.objects.create(
            academy=cls.academy,
            title="Advanced Piano Masterclass",
            slug="pay-price-advanced-piano",
            instructor=cls.instructor,
            instrument="Piano",
            difficulty_level="advanced",
            price_cents=2999,
            is_published=True,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="student-price-iso@test.com", password="testpass123"
        )

    def test_course_model_is_free_property(self):
        """Course.is_free returns correct value."""
        assert self.free_course.is_free is True
        assert self.paid_course.is_free is False

    def test_course_model_price_display(self):
        """Course.price_display returns formatted string."""
        assert self.free_course.price_display == "Free"
        assert self.paid_course.price_display == "$29.99"

    def test_course_list_shows_free_badge(self):
        """Course grid shows Free badge for free courses."""
        response = self.student_client.get(reverse("course-list"))
        content = response.content.decode()
        assert "badge-success" in content
        assert "Free" in content

    def test_course_list_shows_price_badge(self):
        """Course grid shows price badge for paid courses."""
        response = self.student_client.get(reverse("course-list"))
        content = response.content.decode()
        assert "$29.99" in content


# =========================================================================
# Task 3: Buy/Enroll button logic
# =========================================================================


@pytest.mark.integration
class TestCourseDetailButtons(TestCase):
    """Course detail page shows correct button based on state."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Detail Buttons Academy",
            slug="pay-buttons-iso",
            description="A test academy",
            email="pay-buttons-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-buttons-iso",
            email="instructor-buttons-iso@test.com",
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

        cls.student = User.objects.create_user(
            username="student-buttons-iso",
            email="student-buttons-iso@test.com",
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

        cls.free_course = Course.objects.create(
            academy=cls.academy,
            title="Free Guitar Basics",
            slug="pay-buttons-free-guitar",
            instructor=cls.instructor,
            instrument="Guitar",
            difficulty_level="beginner",
            price_cents=0,
            is_published=True,
        )
        cls.paid_course = Course.objects.create(
            academy=cls.academy,
            title="Advanced Piano Masterclass",
            slug="pay-buttons-advanced-piano",
            instructor=cls.instructor,
            instrument="Piano",
            difficulty_level="advanced",
            price_cents=2999,
            is_published=True,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="student-buttons-iso@test.com", password="testpass123"
        )

    def test_paid_course_shows_buy_button(self):
        """Student viewing paid course sees Buy button with price."""
        response = self.student_client.get(
            reverse("course-detail", args=[self.paid_course.slug])
        )
        content = response.content.decode()
        assert "Buy Course" in content
        assert "$29.99" in content
        assert "checkout/course/pay-buttons-advanced-piano" in content

    def test_free_course_shows_enroll_button(self):
        """Student viewing free course sees Enroll Free button."""
        response = self.student_client.get(
            reverse("course-detail", args=[self.free_course.slug])
        )
        content = response.content.decode()
        assert "Enroll Free" in content

    def test_enrolled_student_sees_continue(self):
        """Enrolled student sees Continue Learning button."""
        Enrollment.objects.create(
            student=self.student,
            course=self.free_course,
            academy=self.academy,
        )
        response = self.student_client.get(
            reverse("course-detail", args=[self.free_course.slug])
        )
        content = response.content.decode()
        assert "Continue Learning" in content


# =========================================================================
# Task 4: Package price display
# =========================================================================


@pytest.mark.integration
class TestPackagePriceDisplay(TestCase):
    """Package deals display correct prices."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Package Price Academy",
            slug="pay-package-iso",
            description="A test academy",
            email="pay-package-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-package-iso",
            email="owner-package-iso@test.com",
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
            username="owner-package-iso@test.com", password="testpass123"
        )

    def test_package_price_display_property(self):
        """PackageDeal.price_display returns formatted string."""
        pkg = PackageDeal.objects.create(
            academy=self.academy,
            name="10 Sessions",
            price_cents=9999,
            total_credits=10,
        )
        assert pkg.price_display == "$99.99"

    def test_package_price_per_credit(self):
        """PackageDeal.price_per_credit_display calculates correctly."""
        pkg = PackageDeal.objects.create(
            academy=self.academy,
            name="10 Sessions",
            price_cents=10000,
            total_credits=10,
        )
        assert pkg.price_per_credit_display == "$10.00"

    def test_pricing_page_shows_correct_package_price(self):
        """Pricing page displays dollar amount, not True/False."""
        PackageDeal.objects.create(
            academy=self.academy,
            name="10 Lesson Pack",
            price_cents=9999,
            total_credits=10,
            is_active=True,
        )
        response = self.auth_client.get(reverse("pricing"))
        content = response.content.decode()
        assert "$99.99" in content
        # The old bug showed $True or $False
        assert "$True" not in content
        assert "$False" not in content


# =========================================================================
# Task 6: Sidebar navigation
# =========================================================================


@pytest.mark.integration
class TestSidebarPaymentLinks(TestCase):
    """Payment-related links appear in sidebar for correct roles."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Sidebar Links Academy",
            slug="pay-sidebar-iso",
            description="A test academy",
            email="pay-sidebar-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-sidebar-iso",
            email="owner-sidebar-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-sidebar-iso",
            email="student-sidebar-iso@test.com",
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
            username="owner-sidebar-iso@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-sidebar-iso@test.com", password="testpass123"
        )

    def test_student_sees_subscription_link(self):
        """Student sidebar shows My Subscriptions."""
        response = self.student_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert "My Subscriptions" in content

    def test_student_sees_packages_link(self):
        """Student sidebar shows My Packages."""
        response = self.student_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert "My Packages" in content

    def test_owner_sees_coupons_and_payouts(self):
        """Owner sidebar shows Coupons and Payouts."""
        response = self.auth_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert "Coupons" in content
        assert "Payouts" in content


# =========================================================================
# Task 7: Webhook idempotency
# =========================================================================


@pytest.mark.integration
class TestWebhookIdempotency(TestCase):
    """Duplicate webhook calls don't create duplicate records."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Webhook Idempotency Academy",
            slug="pay-webhook-iso",
            description="A test academy",
            email="pay-webhook-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.student = User.objects.create_user(
            username="student-webhook-iso",
            email="student-webhook-iso@test.com",
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
        self.client = Client()

    def _make_session(
        self, session_id, metadata, amount=2999, payment_intent="pi_test"
    ):
        """Create a mock Stripe session object that supports both .id and .get()."""
        session = MagicMock()
        session.id = session_id
        session.get = lambda key, default=None: {
            "metadata": metadata,
            "amount_total": amount,
            "payment_intent": payment_intent,
            "subscription": "",
        }.get(key, default)
        return session

    def test_duplicate_webhook_creates_single_payment(self):
        """Calling handle_checkout_completed twice creates only one Payment."""
        from apps.payments.stripe_service import handle_checkout_completed

        Course.objects.create(
            academy=self.academy,
            title="Test Course",
            slug="pay-webhook-test-course",
            instructor=self.student,
            instrument="Piano",
            difficulty_level="beginner",
            price_cents=2999,
            is_published=True,
        )

        metadata = {
            "payment_type": "course",
            "academy_id": str(self.academy.pk),
            "user_id": str(self.student.pk),
            "course_slug": "pay-webhook-test-course",
        }
        session = self._make_session("cs_test_idempotent_123", metadata)

        # First call - creates records
        handle_checkout_completed(session)
        assert (
            Payment.objects.filter(
                stripe_checkout_session_id="cs_test_idempotent_123"
            ).count()
            == 1
        )

        # Second call - idempotent, no duplicate
        handle_checkout_completed(session)
        assert (
            Payment.objects.filter(
                stripe_checkout_session_id="cs_test_idempotent_123"
            ).count()
            == 1
        )

    def test_different_sessions_create_separate_payments(self):
        """Different session IDs each create their own records."""
        from apps.payments.stripe_service import handle_checkout_completed

        Course.objects.create(
            academy=self.academy,
            title="Test Course 2",
            slug="pay-webhook-test-course-2",
            instructor=self.student,
            instrument="Piano",
            difficulty_level="beginner",
            price_cents=2999,
            is_published=True,
        )

        for i in range(2):
            metadata = {
                "payment_type": "course",
                "academy_id": str(self.academy.pk),
                "user_id": str(self.student.pk),
                "course_slug": "pay-webhook-test-course-2",
            }
            session = self._make_session(
                f"cs_test_different_{i}", metadata, payment_intent=f"pi_test_{i}"
            )
            handle_checkout_completed(session)

        assert (
            Payment.objects.filter(
                stripe_checkout_session_id__startswith="cs_test_different_"
            ).count()
            == 2
        )
