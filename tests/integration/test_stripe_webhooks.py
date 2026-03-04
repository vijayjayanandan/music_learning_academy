"""Tests for Stripe webhook handling and stripe_service functions."""

import json
from unittest.mock import patch, MagicMock

import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.payments.models import (
    SubscriptionPlan, Subscription, Payment, PackageDeal, PackagePurchase,
)
from apps.payments.stripe_service import (
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
)


class StripeDict(dict):
    """Dict that also supports attribute access like Stripe objects."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


@pytest.fixture
def stripe_academy(db):
    return Academy.objects.create(
        name="Stripe Academy", slug="stripe-academy",
        description="Test", email="stripe@test.com", timezone="UTC",
    )


@pytest.fixture
def stripe_user(db, stripe_academy):
    user = User.objects.create_user(
        username="stripe_user", email="stripe@test.com", password="testpass123",
    )
    user.current_academy = stripe_academy
    user.save()
    Membership.objects.create(user=user, academy=stripe_academy, role="student")
    return user


@pytest.fixture
def stripe_plan(db, stripe_academy):
    return SubscriptionPlan.objects.create(
        academy=stripe_academy, name="Pro Plan",
        price_cents=2999, billing_cycle="monthly", is_active=True,
    )


@pytest.fixture
def stripe_course(db, stripe_academy, stripe_user):
    return Course.objects.create(
        academy=stripe_academy, title="Paid Course", slug="paid-course",
        instructor=stripe_user, instrument="Piano", difficulty_level="beginner",
        is_published=True, price_cents=4999,
    )


@pytest.fixture
def stripe_package(db, stripe_academy):
    return PackageDeal.objects.create(
        academy=stripe_academy, name="10 Sessions",
        price_cents=9999, total_credits=10, is_active=True,
    )


@pytest.mark.integration
class TestStripeWebhookView:
    @pytest.mark.django_db
    def test_webhook_rejects_missing_secret(self, client, settings):
        settings.STRIPE_WEBHOOK_SECRET = ""
        response = client.post(
            reverse("stripe-webhook"),
            data=b'{}',
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    @patch("apps.payments.stripe_service.stripe.Webhook.construct_event")
    def test_webhook_rejects_invalid_signature(self, mock_construct, client, settings):
        import stripe
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )
        response = client.post(
            reverse("stripe-webhook"),
            data=b'{"type":"test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid_sig",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    @patch("apps.payments.stripe_service.stripe.Webhook.construct_event")
    def test_webhook_handles_unknown_event(self, mock_construct, client, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_construct.return_value = {
            "type": "unknown.event",
            "data": {"object": {}},
        }
        response = client.post(
            reverse("stripe-webhook"),
            data=b'{}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_sig",
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestHandleCheckoutCompleted:
    @pytest.mark.django_db
    @patch("apps.payments.stripe_service.stripe.Subscription.retrieve")
    def test_subscription_checkout(self, mock_retrieve, stripe_user, stripe_academy, stripe_plan):
        mock_retrieve.return_value = {
            "status": "active",
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "trial_end": None,
        }
        session = StripeDict({
            "id": "cs_test_123",
            "metadata": {
                "payment_type": "subscription",
                "academy_id": str(stripe_academy.pk),
                "user_id": str(stripe_user.pk),
                "plan_id": str(stripe_plan.pk),
            },
            "subscription": "sub_test_123",
            "amount_total": 2999,
            "payment_intent": "pi_test_123",
        })
        handle_checkout_completed(session)
        assert Subscription.objects.filter(student=stripe_user, plan=stripe_plan).exists()
        assert Payment.objects.filter(
            student=stripe_user, payment_type="subscription",
        ).exists()

    @pytest.mark.django_db
    def test_course_checkout(self, stripe_user, stripe_academy, stripe_course):
        session = StripeDict({
            "id": "cs_test_456",
            "metadata": {
                "payment_type": "course",
                "academy_id": str(stripe_academy.pk),
                "user_id": str(stripe_user.pk),
                "course_slug": stripe_course.slug,
            },
            "amount_total": 4999,
            "payment_intent": "pi_test_456",
        })
        handle_checkout_completed(session)
        assert Payment.objects.filter(
            student=stripe_user, payment_type="course",
        ).exists()
        assert Enrollment.objects.filter(
            student=stripe_user, course=stripe_course, status="active",
        ).exists()

    @pytest.mark.django_db
    def test_package_checkout(self, stripe_user, stripe_academy, stripe_package):
        session = StripeDict({
            "id": "cs_test_789",
            "metadata": {
                "payment_type": "package",
                "academy_id": str(stripe_academy.pk),
                "user_id": str(stripe_user.pk),
                "package_id": str(stripe_package.pk),
            },
            "amount_total": 9999,
            "payment_intent": "pi_test_789",
        })
        handle_checkout_completed(session)
        assert Payment.objects.filter(
            student=stripe_user, payment_type="package",
        ).exists()
        purchase = PackagePurchase.objects.get(student=stripe_user)
        assert purchase.credits_remaining == 10

    @pytest.mark.django_db
    def test_missing_metadata_logs_error(self, stripe_user, stripe_academy):
        session = StripeDict({
            "id": "cs_test_bad",
            "metadata": {},
            "amount_total": 0,
        })
        # Should not raise
        handle_checkout_completed(session)
        assert Payment.objects.count() == 0

    @pytest.mark.django_db
    def test_nonexistent_user(self, stripe_academy):
        session = StripeDict({
            "id": "cs_test_nouser",
            "metadata": {
                "payment_type": "course",
                "academy_id": str(stripe_academy.pk),
                "user_id": "99999",
                "course_slug": "nonexistent",
            },
            "amount_total": 0,
        })
        handle_checkout_completed(session)
        assert Payment.objects.count() == 0

    @pytest.mark.django_db
    def test_coupon_usage_incremented(self, stripe_user, stripe_academy, stripe_course):
        from apps.payments.models import Coupon
        coupon = Coupon.objects.create(
            academy=stripe_academy, code="SAVE20",
            discount_type="percentage", discount_value=20,
            is_active=True, times_used=0,
        )
        session = StripeDict({
            "id": "cs_test_coupon",
            "metadata": {
                "payment_type": "course",
                "academy_id": str(stripe_academy.pk),
                "user_id": str(stripe_user.pk),
                "course_slug": stripe_course.slug,
                "coupon_code": "SAVE20",
            },
            "amount_total": 3999,
            "payment_intent": "pi_test_coupon",
        })
        handle_checkout_completed(session)
        coupon.refresh_from_db()
        assert coupon.times_used == 1


@pytest.mark.integration
class TestSubscriptionLifecycle:
    @pytest.mark.django_db
    def test_subscription_updated(self, stripe_user, stripe_academy, stripe_plan):
        sub = Subscription.objects.create(
            academy=stripe_academy, student=stripe_user, plan=stripe_plan,
            status="active", stripe_subscription_id="sub_lifecycle_1",
        )
        handle_subscription_updated({
            "id": "sub_lifecycle_1",
            "status": "past_due",
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "trial_end": None,
        })
        sub.refresh_from_db()
        assert sub.status == "past_due"

    @pytest.mark.django_db
    def test_subscription_deleted(self, stripe_user, stripe_academy, stripe_plan):
        sub = Subscription.objects.create(
            academy=stripe_academy, student=stripe_user, plan=stripe_plan,
            status="active", stripe_subscription_id="sub_lifecycle_2",
        )
        handle_subscription_deleted({"id": "sub_lifecycle_2"})
        sub.refresh_from_db()
        assert sub.status == "cancelled"
        assert sub.cancelled_at is not None

    @pytest.mark.django_db
    def test_subscription_updated_unknown_id(self):
        # Should not raise
        handle_subscription_updated({"id": "sub_unknown_999", "status": "active"})

    @pytest.mark.django_db
    def test_subscription_deleted_unknown_id(self):
        # Should not raise
        handle_subscription_deleted({"id": "sub_unknown_999"})
