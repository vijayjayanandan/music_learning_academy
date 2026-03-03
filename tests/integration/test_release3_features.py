"""Tests for FEAT-023 through FEAT-032 (Release 3: Monetization)."""
import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.payments.models import (
    SubscriptionPlan, Subscription, Payment, Coupon,
    InstructorPayout, PackageDeal, PackagePurchase, AcademyTier,
)
from apps.scheduling.models import InstructorAvailability


@pytest.mark.integration
class TestStripePayments:
    """FEAT-023: Course payments (stubbed Stripe)."""

    def test_payment_model_fields(self, db):
        assert hasattr(Payment, "amount_cents")
        assert hasattr(Payment, "stripe_payment_intent_id")
        assert hasattr(Payment, "invoice_number")

    def test_payment_auto_invoice_number(self, owner_user, academy, db):
        payment = Payment.objects.create(
            student=owner_user, academy=academy,
            amount_cents=5000, payment_type="course",
        )
        assert payment.invoice_number.startswith("INV-")

    def test_payment_history_view(self, auth_client):
        response = auth_client.get(reverse("payment-history"))
        assert response.status_code == 200


@pytest.mark.integration
class TestSubscriptionPlans:
    """FEAT-024: Subscription plans."""

    def test_subscription_plan_model(self, db):
        assert hasattr(SubscriptionPlan, "price_cents")
        assert hasattr(SubscriptionPlan, "billing_cycle")
        assert hasattr(SubscriptionPlan, "trial_days")

    def test_pricing_page_loads(self, auth_client):
        response = auth_client.get(reverse("pricing"))
        assert response.status_code == 200

    def test_create_subscription(self, owner_user, academy, db):
        plan = SubscriptionPlan.objects.create(
            name="Monthly Plan", academy=academy,
            price_cents=2999, billing_cycle="monthly",
        )
        sub = Subscription.objects.create(
            student=owner_user, plan=plan, academy=academy,
        )
        assert sub.is_valid is True
        assert "Monthly Plan" in str(sub)

    def test_my_subscriptions_view(self, auth_client):
        response = auth_client.get(reverse("my-subscriptions"))
        assert response.status_code == 200


@pytest.mark.integration
class TestFreeTrial:
    """FEAT-025: Free trial period."""

    def test_plan_with_trial_days(self, academy, db):
        plan = SubscriptionPlan.objects.create(
            name="Trial Plan", academy=academy,
            price_cents=1999, trial_days=7,
        )
        assert plan.trial_days == 7

    def test_subscription_trialing_status(self, owner_user, academy, db):
        plan = SubscriptionPlan.objects.create(
            name="Trial Plan", academy=academy,
            price_cents=1999, trial_days=7,
        )
        sub = Subscription.objects.create(
            student=owner_user, plan=plan, academy=academy,
            status=Subscription.Status.TRIALING,
            trial_end=timezone.now() + timezone.timedelta(days=7),
        )
        assert sub.is_valid is True


@pytest.mark.integration
class TestCoupons:
    """FEAT-026: Coupon codes and discounts."""

    def test_coupon_model(self, db):
        assert hasattr(Coupon, "code")
        assert hasattr(Coupon, "discount_type")

    def test_coupon_validity(self, academy, db):
        coupon = Coupon.objects.create(
            academy=academy, code="SAVE20",
            discount_type="percentage", discount_value=20,
        )
        assert coupon.is_valid is True
        assert "20%" in str(coupon)

    def test_expired_coupon_invalid(self, academy, db):
        coupon = Coupon.objects.create(
            academy=academy, code="EXPIRED",
            discount_type="percentage", discount_value=10,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        assert coupon.is_valid is False

    def test_coupon_manage_view(self, auth_client):
        response = auth_client.get(reverse("coupon-manage"))
        assert response.status_code == 200

    def test_create_coupon(self, auth_client, academy):
        response = auth_client.post(reverse("coupon-manage"), {
            "code": "NEWCODE",
            "discount_type": "percentage",
            "discount_value": "15",
            "max_uses": "100",
        })
        assert response.status_code == 302
        assert Coupon.objects.filter(academy=academy, code="NEWCODE").exists()


@pytest.mark.integration
class TestInvoices:
    """FEAT-027: Invoice generation."""

    def test_invoice_detail_view(self, auth_client, owner_user, academy, db):
        payment = Payment.objects.create(
            student=owner_user, academy=academy,
            amount_cents=5000, payment_type="course",
            status="completed", paid_at=timezone.now(),
        )
        response = auth_client.get(reverse("invoice-detail", args=[payment.pk]))
        assert response.status_code == 200
        assert payment.invoice_number.encode() in response.content


@pytest.mark.integration
class TestInstructorPayouts:
    """FEAT-028: Instructor payout management."""

    def test_payout_model(self, db):
        assert hasattr(InstructorPayout, "amount_cents")
        assert hasattr(InstructorPayout, "period_start")

    def test_payout_list_view(self, auth_client):
        response = auth_client.get(reverse("payout-list"))
        assert response.status_code == 200


@pytest.mark.integration
class TestAcademyTiers:
    """FEAT-029: Academy subscription tiers."""

    def test_academy_tier_model(self, db):
        tier = AcademyTier.objects.create(
            name="Pro", tier_level="pro",
            price_cents=4999, max_students=100,
            max_instructors=10, max_courses=50,
        )
        assert "Pro" in str(tier)

    def test_tiers_page_loads(self, client, db):
        AcademyTier.objects.create(
            name="Free", tier_level="free",
            price_cents=0, max_students=10,
        )
        response = client.get(reverse("academy-tiers"))
        assert response.status_code == 200


@pytest.mark.integration
class TestAvailabilityAndBooking:
    """FEAT-030: Availability management + student self-booking."""

    def test_availability_model(self, db):
        assert hasattr(InstructorAvailability, "day_of_week")
        assert hasattr(InstructorAvailability, "start_time")

    def test_availability_manage_view(self, auth_client):
        response = auth_client.get(reverse("availability-manage"))
        assert response.status_code == 200

    def test_create_availability(self, auth_client, owner_user, academy, db):
        response = auth_client.post(reverse("availability-manage"), {
            "day_of_week": "1",
            "start_time": "09:00",
            "end_time": "17:00",
        })
        assert response.status_code == 302
        assert InstructorAvailability.objects.filter(instructor=owner_user).exists()

    def test_book_session_view(self, auth_client):
        response = auth_client.get(reverse("book-session"))
        assert response.status_code == 200


@pytest.mark.integration
class TestPackageDeals:
    """FEAT-031: Package deals."""

    def test_package_model(self, academy, db):
        pkg = PackageDeal.objects.create(
            name="10 Lesson Pack", academy=academy,
            price_cents=15000, total_credits=10,
        )
        assert pkg.total_credits == 10

    def test_my_packages_view(self, auth_client):
        response = auth_client.get(reverse("my-packages"))
        assert response.status_code == 200

    def test_purchase_package(self, auth_client, owner_user, academy, db):
        pkg = PackageDeal.objects.create(
            name="5 Lesson Pack", academy=academy,
            price_cents=8000, total_credits=5,
        )
        response = auth_client.post(reverse("package-purchase", args=[pkg.pk]))
        assert response.status_code == 302
        purchase = PackagePurchase.objects.get(student=owner_user, package=pkg)
        assert purchase.credits_remaining == 5


@pytest.mark.integration
class TestParentPortal:
    """FEAT-032: Parent/guardian portal."""

    def test_user_has_parent_fields(self, db):
        assert hasattr(User, "is_parent")
        assert hasattr(User, "parent")

    def test_parent_dashboard_loads(self, auth_client):
        response = auth_client.get(reverse("parent-dashboard"))
        assert response.status_code == 200

    def test_link_child(self, auth_client, owner_user, academy, db):
        child = User.objects.create_user(
            email="child@test.com", username="child", password="testpass123",
        )
        Membership.objects.create(user=child, academy=academy, role="student")
        response = auth_client.post(reverse("link-child"), {
            "child_email": "child@test.com",
        })
        assert response.status_code == 302
        child.refresh_from_db()
        assert child.parent == owner_user
        owner_user.refresh_from_db()
        assert owner_user.is_parent is True
