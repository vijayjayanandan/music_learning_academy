"""Tests for Stripe webhook handling and stripe_service functions."""

import json
from unittest.mock import patch, MagicMock

import pytest
from django.test import TestCase, Client, override_settings
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


@pytest.mark.integration
class TestStripeWebhookView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Stripe Webhook Academy",
            slug="stripe-webhookview-iso",
            description="Test",
            email="stripe-webhookview@test.com",
            timezone="UTC",
        )
        cls.user = User.objects.create_user(
            username="stripe-webhookview-user",
            email="stripe-webhookview@test.com",
            password="testpass123",
        )
        cls.user.current_academy = cls.academy
        cls.user.save()
        Membership.objects.create(user=cls.user, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self.client.login(username="stripe-webhookview@test.com", password="testpass123")

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_webhook_rejects_missing_secret(self):
        response = self.client.post(
            reverse("stripe-webhook"),
            data=b'{}',
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("apps.payments.stripe_service.stripe.Webhook.construct_event")
    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
    def test_webhook_rejects_invalid_signature(self, mock_construct):
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )
        response = self.client.post(
            reverse("stripe-webhook"),
            data=b'{"type":"test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid_sig",
        )
        assert response.status_code == 400

    @patch("apps.payments.stripe_service.stripe.Webhook.construct_event")
    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
    def test_webhook_handles_unknown_event(self, mock_construct):
        mock_construct.return_value = {
            "type": "unknown.event",
            "data": {"object": {}},
        }
        response = self.client.post(
            reverse("stripe-webhook"),
            data=b'{}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_sig",
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestHandleCheckoutCompleted(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Checkout Academy",
            slug="stripe-checkout-iso",
            description="Test",
            email="stripe-checkout@test.com",
            timezone="UTC",
        )
        cls.user = User.objects.create_user(
            username="stripe-checkout-user",
            email="stripe-checkout@test.com",
            password="testpass123",
        )
        cls.user.current_academy = cls.academy
        cls.user.save()
        Membership.objects.create(user=cls.user, academy=cls.academy, role="student")

        cls.plan = SubscriptionPlan.objects.create(
            academy=cls.academy, name="Pro Plan",
            price_cents=2999, billing_cycle="monthly", is_active=True,
        )
        cls.course = Course.objects.create(
            academy=cls.academy, title="Paid Course", slug="paid-course-iso",
            instructor=cls.user, instrument="Piano", difficulty_level="beginner",
            is_published=True, price_cents=4999,
        )
        cls.package = PackageDeal.objects.create(
            academy=cls.academy, name="10 Sessions",
            price_cents=9999, total_credits=10, is_active=True,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="stripe-checkout@test.com", password="testpass123")

    @patch("apps.payments.stripe_service.stripe.Subscription.retrieve")
    def test_subscription_checkout(self, mock_retrieve):
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
                "academy_id": str(self.academy.pk),
                "user_id": str(self.user.pk),
                "plan_id": str(self.plan.pk),
            },
            "subscription": "sub_test_123",
            "amount_total": 2999,
            "payment_intent": "pi_test_123",
        })
        handle_checkout_completed(session)
        assert Subscription.objects.filter(student=self.user, plan=self.plan).exists()
        assert Payment.objects.filter(
            student=self.user, payment_type="subscription",
        ).exists()

    def test_course_checkout(self):
        session = StripeDict({
            "id": "cs_test_456",
            "metadata": {
                "payment_type": "course",
                "academy_id": str(self.academy.pk),
                "user_id": str(self.user.pk),
                "course_slug": self.course.slug,
            },
            "amount_total": 4999,
            "payment_intent": "pi_test_456",
        })
        handle_checkout_completed(session)
        assert Payment.objects.filter(
            student=self.user, payment_type="course",
        ).exists()
        assert Enrollment.objects.filter(
            student=self.user, course=self.course, status="active",
        ).exists()

    def test_package_checkout(self):
        session = StripeDict({
            "id": "cs_test_789",
            "metadata": {
                "payment_type": "package",
                "academy_id": str(self.academy.pk),
                "user_id": str(self.user.pk),
                "package_id": str(self.package.pk),
            },
            "amount_total": 9999,
            "payment_intent": "pi_test_789",
        })
        handle_checkout_completed(session)
        assert Payment.objects.filter(
            student=self.user, payment_type="package",
        ).exists()
        purchase = PackagePurchase.objects.get(student=self.user)
        assert purchase.credits_remaining == 10

    def test_missing_metadata_logs_error(self):
        session = StripeDict({
            "id": "cs_test_bad",
            "metadata": {},
            "amount_total": 0,
        })
        # Should not raise
        handle_checkout_completed(session)
        assert Payment.objects.filter(student=self.user).count() == 0

    def test_nonexistent_user(self):
        session = StripeDict({
            "id": "cs_test_nouser",
            "metadata": {
                "payment_type": "course",
                "academy_id": str(self.academy.pk),
                "user_id": "99999",
                "course_slug": "nonexistent",
            },
            "amount_total": 0,
        })
        handle_checkout_completed(session)
        assert Payment.objects.filter(student=self.user).count() == 0

    def test_coupon_usage_incremented(self):
        from apps.payments.models import Coupon
        coupon = Coupon.objects.create(
            academy=self.academy, code="SAVE20",
            discount_type="percentage", discount_value=20,
            is_active=True, times_used=0,
        )
        session = StripeDict({
            "id": "cs_test_coupon",
            "metadata": {
                "payment_type": "course",
                "academy_id": str(self.academy.pk),
                "user_id": str(self.user.pk),
                "course_slug": self.course.slug,
                "coupon_code": "SAVE20",
            },
            "amount_total": 3999,
            "payment_intent": "pi_test_coupon",
        })
        handle_checkout_completed(session)
        coupon.refresh_from_db()
        assert coupon.times_used == 1


@pytest.mark.integration
class TestSubscriptionLifecycle(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Lifecycle Academy",
            slug="stripe-lifecycle-iso",
            description="Test",
            email="stripe-lifecycle@test.com",
            timezone="UTC",
        )
        cls.user = User.objects.create_user(
            username="stripe-lifecycle-user",
            email="stripe-lifecycle@test.com",
            password="testpass123",
        )
        cls.user.current_academy = cls.academy
        cls.user.save()
        Membership.objects.create(user=cls.user, academy=cls.academy, role="student")

        cls.plan = SubscriptionPlan.objects.create(
            academy=cls.academy, name="Pro Plan",
            price_cents=2999, billing_cycle="monthly", is_active=True,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="stripe-lifecycle@test.com", password="testpass123")

    def test_subscription_updated(self):
        sub = Subscription.objects.create(
            academy=self.academy, student=self.user, plan=self.plan,
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

    def test_subscription_deleted(self):
        sub = Subscription.objects.create(
            academy=self.academy, student=self.user, plan=self.plan,
            status="active", stripe_subscription_id="sub_lifecycle_2",
        )
        handle_subscription_deleted({"id": "sub_lifecycle_2"})
        sub.refresh_from_db()
        assert sub.status == "cancelled"
        assert sub.cancelled_at is not None

    def test_subscription_updated_unknown_id(self):
        # Should not raise
        handle_subscription_updated({"id": "sub_unknown_999", "status": "active"})

    def test_subscription_deleted_unknown_id(self):
        # Should not raise
        handle_subscription_deleted({"id": "sub_unknown_999"})
