"""Tests for the payment success page with purchase details and CTAs."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.payments.models import Payment, PackagePurchase, SubscriptionPlan, Subscription, PackageDeal


@pytest.mark.integration
class TestPaymentSuccessPageCourseDetails(TestCase):
    """Test that the success page shows course details and Start Learning CTA."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Payment Success Academy",
            slug="paysuc-coursedetails-iso",
            description="A test academy",
            email="paysuc-coursedetails@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="paysuc-coursedetails-owner",
            email="paysuc-coursedetails-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self.client.login(
            username="paysuc-coursedetails-owner@test.com", password="testpass123"
        )

    def test_success_page_shows_course_details(self):
        """Happy path: payment with course FK shows course name + Start Learning link."""
        course = Course.objects.create(
            academy=self.academy,
            title="Jazz Piano Masterclass",
            slug="jazz-piano-masterclass-paysuc",
            instructor=self.owner,
            instrument="Piano",
            difficulty_level="beginner",
            price_cents=4999,
            is_published=True,
        )
        payment = Payment.objects.create(
            academy=self.academy,
            student=self.owner,
            amount_cents=4999,
            payment_type="course",
            course=course,
            description="Course purchase: Jazz Piano Masterclass",
            stripe_checkout_session_id="cs_test_course_123",
            status="completed",
            paid_at=timezone.now(),
        )

        url = reverse("payment-success") + "?session_id=cs_test_course_123"
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Shows purchase details
        assert "Jazz Piano Masterclass" in content
        assert payment.amount_display in content
        assert payment.invoice_number in content
        # Shows Start Learning CTA linking to the course
        assert "Start Learning" in content
        course_url = reverse("course-detail", kwargs={"slug": course.slug})
        assert course_url in content

    def test_success_page_shows_subscription_details(self):
        """Subscription purchase shows plan name and View My Subscriptions CTA."""
        plan = SubscriptionPlan.objects.create(
            academy=self.academy,
            name="Pro Monthly",
            price_cents=2999,
            billing_cycle="monthly",
            is_active=True,
        )
        subscription = Subscription.objects.create(
            academy=self.academy,
            student=self.owner,
            plan=plan,
            status="active",
            stripe_subscription_id="sub_test_paysuc_sub",
        )
        payment = Payment.objects.create(
            academy=self.academy,
            student=self.owner,
            amount_cents=2999,
            payment_type="subscription",
            subscription=subscription,
            description="Subscription: Pro Monthly",
            stripe_checkout_session_id="cs_test_sub_456",
            status="completed",
            paid_at=timezone.now(),
        )

        url = reverse("payment-success") + "?session_id=cs_test_sub_456"
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Subscription: Pro Monthly" in content
        assert payment.amount_display in content
        assert "View My Subscriptions" in content
        assert reverse("my-subscriptions") in content
        # Should NOT show Start Learning
        assert "Start Learning" not in content

    def test_success_page_shows_package_details(self):
        """Package purchase shows package name and View My Packages CTA."""
        package = PackageDeal.objects.create(
            academy=self.academy,
            name="10 Lesson Bundle",
            price_cents=7999,
            total_credits=10,
            is_active=True,
        )
        payment = Payment.objects.create(
            academy=self.academy,
            student=self.owner,
            amount_cents=7999,
            payment_type="package",
            description="Package purchase: 10 Lesson Bundle",
            stripe_checkout_session_id="cs_test_pkg_789",
            status="completed",
            paid_at=timezone.now(),
        )
        PackagePurchase.objects.create(
            academy=self.academy,
            student=self.owner,
            package=package,
            credits_remaining=package.total_credits,
            payment=payment,
        )

        url = reverse("payment-success") + "?session_id=cs_test_pkg_789"
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "10 Lesson Bundle" in content
        assert payment.amount_display in content
        assert "View My Packages" in content
        assert reverse("my-packages") in content
        assert "Start Learning" not in content


@pytest.mark.integration
class TestPaymentSuccessPageFallback(TestCase):
    """Test fallback behavior when payment record cannot be found."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Payment Fallback Academy",
            slug="paysuc-fallback-iso",
            description="A test academy",
            email="paysuc-fallback@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="paysuc-fallback-owner",
            email="paysuc-fallback-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        # user_a and user_b are used in the isolation test; created here so they
        # exist for the whole class and are only assigned fresh clients in setUp.
        cls.user_a = User.objects.create_user(
            username="paysuc-fallback-usera",
            email="paysuc-usera@test.com",
            password="testpass123",
            first_name="User",
            last_name="A",
        )
        cls.user_a.current_academy = cls.academy
        cls.user_a.save()
        Membership.objects.create(user=cls.user_a, academy=cls.academy, role="student")

        cls.user_b = User.objects.create_user(
            username="paysuc-fallback-userb",
            email="paysuc-userb@test.com",
            password="testpass123",
            first_name="User",
            last_name="B",
        )
        cls.user_b.current_academy = cls.academy
        cls.user_b.save()
        Membership.objects.create(user=cls.user_b, academy=cls.academy, role="student")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="paysuc-fallback-owner@test.com", password="testpass123"
        )
        self.client_b = Client()
        self.client_b.login(
            username="paysuc-userb@test.com", password="testpass123"
        )

    def test_success_page_generic_fallback(self):
        """Unknown session_id shows generic success message with dashboard link."""
        url = reverse("payment-success") + "?session_id=cs_unknown_session"
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Shows generic message
        assert "Your payment has been processed" in content
        assert "Go to Dashboard" in content
        # Does NOT show purchase details section
        assert "Purchase Details" not in content
        assert "Start Learning" not in content

    def test_success_page_no_session_id(self):
        """No session_id parameter shows generic success."""
        url = reverse("payment-success")
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Your payment has been processed" in content
        assert "Go to Dashboard" in content
        assert "Purchase Details" not in content

    def test_success_page_other_users_payment_not_shown(self):
        """A user cannot see another user's payment details (tenant + user isolation)."""
        # Create a payment for user_a (set up in setUpTestData)
        course = Course.objects.create(
            academy=self.academy,
            title="Secret Course",
            slug="secret-course-paysuc",
            instructor=self.owner,
            instrument="Piano",
            difficulty_level="beginner",
            price_cents=9999,
            is_published=True,
        )
        Payment.objects.create(
            academy=self.academy,
            student=self.user_a,
            amount_cents=9999,
            payment_type="course",
            course=course,
            description="Course purchase: Secret Course",
            stripe_checkout_session_id="cs_test_private_001",
            status="completed",
            paid_at=timezone.now(),
        )

        # Log in as user_b and try to access user_a's payment
        url = reverse("payment-success") + "?session_id=cs_test_private_001"
        response = self.client_b.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # User B should NOT see User A's payment details
        assert "Secret Course" not in content
        assert "Purchase Details" not in content
        assert "Your payment has been processed" in content
