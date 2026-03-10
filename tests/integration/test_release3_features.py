"""Tests for FEAT-023 through FEAT-032 (Release 3: Monetization)."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.payments.models import (
    SubscriptionPlan,
    Subscription,
    Payment,
    Coupon,
    InstructorPayout,
    PackageDeal,
    AcademyTier,
)
from apps.scheduling.models import InstructorAvailability


@pytest.mark.integration
class TestStripePayments(TestCase):
    """FEAT-023: Course payments (stubbed Stripe)."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-stripe-iso",
            description="A test academy",
            email="rel3-stripe@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-stripe",
            email="owner-rel3-stripe@test.com",
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
            username="owner-rel3-stripe@test.com", password="testpass123"
        )

    def test_payment_model_fields(self):
        assert hasattr(Payment, "amount_cents")
        assert hasattr(Payment, "stripe_payment_intent_id")
        assert hasattr(Payment, "invoice_number")

    def test_payment_auto_invoice_number(self):
        payment = Payment.objects.create(
            student=self.owner,
            academy=self.academy,
            amount_cents=5000,
            payment_type="course",
        )
        assert payment.invoice_number.startswith("INV-")

    def test_payment_history_view(self):
        response = self.auth_client.get(reverse("payment-history"))
        assert response.status_code == 200


@pytest.mark.integration
class TestSubscriptionPlans(TestCase):
    """FEAT-024: Subscription plans."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-subplan-iso",
            description="A test academy",
            email="rel3-subplan@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-subplan",
            email="owner-rel3-subplan@test.com",
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
            username="owner-rel3-subplan@test.com", password="testpass123"
        )

    def test_subscription_plan_model(self):
        assert hasattr(SubscriptionPlan, "price_cents")
        assert hasattr(SubscriptionPlan, "billing_cycle")
        assert hasattr(SubscriptionPlan, "trial_days")

    def test_pricing_page_loads(self):
        response = self.auth_client.get(reverse("pricing"))
        assert response.status_code == 200

    def test_create_subscription(self):
        plan = SubscriptionPlan.objects.create(
            name="Monthly Plan",
            academy=self.academy,
            price_cents=2999,
            billing_cycle="monthly",
        )
        sub = Subscription.objects.create(
            student=self.owner,
            plan=plan,
            academy=self.academy,
        )
        assert sub.is_valid is True
        assert "Monthly Plan" in str(sub)

    def test_my_subscriptions_view(self):
        response = self.auth_client.get(reverse("my-subscriptions"))
        assert response.status_code == 200


@pytest.mark.integration
class TestFreeTrial(TestCase):
    """FEAT-025: Free trial period."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-trial-iso",
            description="A test academy",
            email="rel3-trial@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-trial",
            email="owner-rel3-trial@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def test_plan_with_trial_days(self):
        plan = SubscriptionPlan.objects.create(
            name="Trial Plan",
            academy=self.academy,
            price_cents=1999,
            trial_days=7,
        )
        assert plan.trial_days == 7

    def test_subscription_trialing_status(self):
        plan = SubscriptionPlan.objects.create(
            name="Trial Plan",
            academy=self.academy,
            price_cents=1999,
            trial_days=7,
        )
        sub = Subscription.objects.create(
            student=self.owner,
            plan=plan,
            academy=self.academy,
            status=Subscription.Status.TRIALING,
            trial_end=timezone.now() + timezone.timedelta(days=7),
        )
        assert sub.is_valid is True


@pytest.mark.integration
class TestCoupons(TestCase):
    """FEAT-026: Coupon codes and discounts."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-coupon-iso",
            description="A test academy",
            email="rel3-coupon@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-coupon",
            email="owner-rel3-coupon@test.com",
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
            username="owner-rel3-coupon@test.com", password="testpass123"
        )

    def test_coupon_model(self):
        assert hasattr(Coupon, "code")
        assert hasattr(Coupon, "discount_type")

    def test_coupon_validity(self):
        coupon = Coupon.objects.create(
            academy=self.academy,
            code="SAVE20",
            discount_type="percentage",
            discount_value=20,
        )
        assert coupon.is_valid is True
        assert "20%" in str(coupon)

    def test_expired_coupon_invalid(self):
        coupon = Coupon.objects.create(
            academy=self.academy,
            code="EXPIRED",
            discount_type="percentage",
            discount_value=10,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        assert coupon.is_valid is False

    def test_coupon_manage_view(self):
        response = self.auth_client.get(reverse("coupon-manage"))
        assert response.status_code == 200

    def test_create_coupon(self):
        response = self.auth_client.post(
            reverse("coupon-manage"),
            {
                "code": "NEWCODE",
                "discount_type": "percentage",
                "discount_value": "15",
                "max_uses": "100",
            },
        )
        assert response.status_code == 302
        assert Coupon.objects.filter(academy=self.academy, code="NEWCODE").exists()


@pytest.mark.integration
class TestInvoices(TestCase):
    """FEAT-027: Invoice generation."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-invoice-iso",
            description="A test academy",
            email="rel3-invoice@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-invoice",
            email="owner-rel3-invoice@test.com",
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
            username="owner-rel3-invoice@test.com", password="testpass123"
        )

    def test_invoice_detail_view(self):
        payment = Payment.objects.create(
            student=self.owner,
            academy=self.academy,
            amount_cents=5000,
            payment_type="course",
            status="completed",
            paid_at=timezone.now(),
        )
        response = self.auth_client.get(reverse("invoice-detail", args=[payment.pk]))
        assert response.status_code == 200
        assert payment.invoice_number.encode() in response.content


@pytest.mark.integration
class TestInstructorPayouts(TestCase):
    """FEAT-028: Instructor payout management."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-payout-iso",
            description="A test academy",
            email="rel3-payout@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-payout",
            email="owner-rel3-payout@test.com",
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
            username="owner-rel3-payout@test.com", password="testpass123"
        )

    def test_payout_model(self):
        assert hasattr(InstructorPayout, "amount_cents")
        assert hasattr(InstructorPayout, "period_start")

    def test_payout_list_view(self):
        response = self.auth_client.get(reverse("payout-list"))
        assert response.status_code == 200


@pytest.mark.integration
class TestAcademyTiers(TestCase):
    """FEAT-029: Academy subscription tiers."""

    def test_academy_tier_model(self):
        tier = AcademyTier.objects.create(
            name="Pro",
            tier_level="pro",
            price_cents=4999,
            max_students=100,
            max_instructors=10,
            max_courses=50,
        )
        assert "Pro" in str(tier)

    def test_tiers_page_loads(self):
        AcademyTier.objects.create(
            name="Free",
            tier_level="free",
            price_cents=0,
            max_students=10,
        )
        anon_client = Client()
        response = anon_client.get(reverse("academy-tiers"))
        assert response.status_code == 200


@pytest.mark.integration
class TestAvailabilityAndBooking(TestCase):
    """FEAT-030: Availability management + student self-booking."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-avail-iso",
            description="A test academy",
            email="rel3-avail@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-avail",
            email="owner-rel3-avail@test.com",
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
            username="owner-rel3-avail@test.com", password="testpass123"
        )

    def test_availability_model(self):
        assert hasattr(InstructorAvailability, "day_of_week")
        assert hasattr(InstructorAvailability, "start_time")

    def test_availability_manage_view(self):
        response = self.auth_client.get(reverse("availability-manage"))
        assert response.status_code == 200

    def test_create_availability(self):
        response = self.auth_client.post(
            reverse("availability-manage"),
            {
                "day_of_week": "1",
                "start_time": "09:00",
                "end_time": "17:00",
            },
        )
        assert response.status_code == 302
        assert InstructorAvailability.objects.filter(instructor=self.owner).exists()

    def test_book_session_view(self):
        response = self.auth_client.get(reverse("book-session"))
        assert response.status_code == 200


@pytest.mark.integration
class TestPackageDeals(TestCase):
    """FEAT-031: Package deals."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-pkg-iso",
            description="A test academy",
            email="rel3-pkg@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-pkg",
            email="owner-rel3-pkg@test.com",
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
            username="owner-rel3-pkg@test.com", password="testpass123"
        )

    def test_package_model(self):
        pkg = PackageDeal.objects.create(
            name="10 Lesson Pack",
            academy=self.academy,
            price_cents=15000,
            total_credits=10,
        )
        assert pkg.total_credits == 10

    def test_my_packages_view(self):
        response = self.auth_client.get(reverse("my-packages"))
        assert response.status_code == 200

    def test_purchase_package_redirects_or_errors(self):
        """Package purchase now goes through Stripe checkout; POST redirects to Stripe or pricing on error."""
        pkg = PackageDeal.objects.create(
            name="5 Lesson Pack",
            academy=self.academy,
            price_cents=8000,
            total_credits=5,
        )
        response = self.auth_client.post(reverse("package-purchase", args=[pkg.pk]))
        # Redirects to Stripe checkout URL (302) or back to pricing on Stripe API error
        assert response.status_code == 302


@pytest.mark.integration
class TestParentPortal(TestCase):
    """FEAT-032: Parent/guardian portal."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel3-parent-iso",
            description="A test academy",
            email="rel3-parent@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rel3-parent",
            email="owner-rel3-parent@test.com",
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
            username="owner-rel3-parent@test.com", password="testpass123"
        )

    def test_user_has_parent_fields(self):
        assert hasattr(User, "is_parent")
        assert hasattr(User, "parent")

    def test_parent_dashboard_loads(self):
        response = self.auth_client.get(reverse("parent-dashboard"))
        assert response.status_code == 200

    def test_link_child(self):
        child = User.objects.create_user(
            email="child-rel3-parent@test.com",
            username="child-rel3-parent",
            password="testpass123",
        )
        Membership.objects.create(user=child, academy=self.academy, role="student")
        response = self.auth_client.post(
            reverse("link-child"),
            {
                "child_email": "child-rel3-parent@test.com",
            },
        )
        assert response.status_code == 302
        child.refresh_from_db()
        assert child.parent == self.owner
        self.owner.refresh_from_db()
        assert self.owner.is_parent is True
