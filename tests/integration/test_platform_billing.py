"""Tests for Sprint 3: Platform Billing Foundation.

Tests cover:
- PlatformSubscription model lifecycle
- FinancialAccount model
- Refund model workflow
- Trial expiry Celery task
- Trial reminder Celery task
- Owner dashboard financial overview
"""

from datetime import timedelta

import pytest
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Membership, User
from apps.academies.models import Academy
from apps.payments.models import (
    AcademyTier,
    FinancialAccount,
    Payment,
    PlatformSubscription,
    Refund,
    Subscription,
    SubscriptionPlan,
)


# ============================================================
# PlatformSubscription Model Tests
# ============================================================


@pytest.mark.integration
class TestPlatformSubscriptionModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-billing-model-iso",
            description="A test academy",
            email="billing-model-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-billing-model-iso",
            email="owner-billing-model-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.free_tier = AcademyTier.objects.create(
            name="Free",
            tier_level="free",
            price_cents=0,
            max_students=10,
            max_instructors=2,
            max_courses=5,
        )
        now = timezone.now()
        cls.platform_sub = PlatformSubscription.objects.create(
            academy=cls.academy,
            tier=cls.free_tier,
            status=PlatformSubscription.Status.TRIAL,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=14),
        )

    def test_status_choices_exist(self):
        choices = [c[0] for c in PlatformSubscription.Status.choices]
        assert "trial" in choices
        assert "active" in choices
        assert "past_due" in choices
        assert "grace" in choices
        assert "cancelled" in choices
        assert "expired" in choices

    def test_is_valid_trial(self):
        self.platform_sub.status = PlatformSubscription.Status.TRIAL
        assert self.platform_sub.is_valid is True

    def test_is_valid_active(self):
        self.platform_sub.status = PlatformSubscription.Status.ACTIVE
        assert self.platform_sub.is_valid is True

    def test_is_valid_grace(self):
        self.platform_sub.status = PlatformSubscription.Status.GRACE
        assert self.platform_sub.is_valid is True

    def test_is_not_valid_cancelled(self):
        self.platform_sub.status = PlatformSubscription.Status.CANCELLED
        assert self.platform_sub.is_valid is False

    def test_is_not_valid_expired(self):
        self.platform_sub.status = PlatformSubscription.Status.EXPIRED
        assert self.platform_sub.is_valid is False

    def test_is_not_valid_past_due(self):
        self.platform_sub.status = PlatformSubscription.Status.PAST_DUE
        assert self.platform_sub.is_valid is False

    def test_is_in_trial(self):
        self.platform_sub.status = PlatformSubscription.Status.TRIAL
        assert self.platform_sub.is_in_trial is True
        self.platform_sub.status = PlatformSubscription.Status.ACTIVE
        assert self.platform_sub.is_in_trial is False

    def test_days_until_trial_expires(self):
        self.platform_sub.trial_ends_at = timezone.now() + timedelta(days=7)
        days = self.platform_sub.days_until_trial_expires
        assert days is not None
        assert 6 <= days <= 7

    def test_days_until_trial_expires_not_in_trial(self):
        self.platform_sub.status = PlatformSubscription.Status.ACTIVE
        assert self.platform_sub.days_until_trial_expires is None

    def test_days_until_trial_expires_no_end_date(self):
        self.platform_sub.trial_ends_at = None
        assert self.platform_sub.days_until_trial_expires is None

    def test_days_until_trial_expired_returns_zero(self):
        self.platform_sub.trial_ends_at = timezone.now() - timedelta(days=1)
        days = self.platform_sub.days_until_trial_expires
        assert days == 0

    def test_str_representation(self):
        result = str(self.platform_sub)
        assert self.platform_sub.academy.name in result
        assert "trial" in result.lower()

    def test_one_to_one_with_academy(self):
        """Each academy can only have one platform subscription."""
        with pytest.raises(Exception):
            PlatformSubscription.objects.create(
                academy=self.academy,
                tier=self.free_tier,
                status=PlatformSubscription.Status.TRIAL,
            )

    def test_academy_reverse_relation(self):
        assert self.academy.platform_subscription == self.platform_sub


# ============================================================
# FinancialAccount Model Tests
# ============================================================


@pytest.mark.integration
class TestFinancialAccountModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-billing-financial-iso",
            description="A test academy",
            email="billing-financial-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-billing-financial-iso",
            email="owner-billing-financial-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def test_status_choices_exist(self):
        choices = [c[0] for c in FinancialAccount.Status.choices]
        assert "not_started" in choices
        assert "pending" in choices
        assert "active" in choices
        assert "restricted" in choices
        assert "disabled" in choices

    def test_create_financial_account(self):
        account = FinancialAccount.objects.create(
            academy=self.academy,
            stripe_account_id="acct_test123",
            status=FinancialAccount.Status.ACTIVE,
            payouts_enabled=True,
            charges_enabled=True,
        )
        assert account.pk is not None
        assert account.payouts_enabled is True

    def test_default_status_not_started(self):
        account = FinancialAccount.objects.create(academy=self.academy)
        assert account.status == "not_started"
        assert account.payouts_enabled is False
        assert account.charges_enabled is False

    def test_str_representation(self):
        account = FinancialAccount.objects.create(academy=self.academy)
        result = str(account)
        assert self.academy.name in result
        assert "Stripe Connect" in result


# ============================================================
# Refund Model Tests
# ============================================================


@pytest.mark.integration
class TestRefundModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-billing-refund-iso",
            description="A test academy",
            email="billing-refund-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-billing-refund-iso",
            email="owner-billing-refund-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-billing-refund-iso",
            email="student-billing-refund-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student, academy=cls.academy, role="student",
            instruments=["Piano"], skill_level="beginner",
        )

        cls.payment = Payment.objects.create(
            academy=cls.academy,
            student=cls.student,
            amount_cents=5000,
            payment_type="course",
            status="completed",
            paid_at=timezone.now(),
        )

    def test_status_choices_exist(self):
        choices = [c[0] for c in Refund.Status.choices]
        assert "requested" in choices
        assert "approved" in choices
        assert "processing" in choices
        assert "completed" in choices
        assert "denied" in choices

    def test_create_refund_request(self):
        refund = Refund.objects.create(
            academy=self.academy,
            payment=self.payment,
            requested_by=self.student,
            amount_cents=5000,
            reason="Course did not meet expectations",
        )
        assert refund.status == "requested"
        assert refund.processed_at is None
        assert refund.processed_by is None

    def test_refund_approve_and_complete(self):
        refund = Refund.objects.create(
            academy=self.academy,
            payment=self.payment,
            requested_by=self.student,
            amount_cents=5000,
            reason="Duplicate charge",
        )
        # Approve
        refund.status = Refund.Status.APPROVED
        refund.save()
        assert refund.status == "approved"

        # Complete
        refund.status = Refund.Status.COMPLETED
        refund.processed_by = self.owner
        refund.processed_at = timezone.now()
        refund.stripe_refund_id = "re_test123"
        refund.save()
        assert refund.status == "completed"
        assert refund.processed_by == self.owner

    def test_refund_deny(self):
        refund = Refund.objects.create(
            academy=self.academy,
            payment=self.payment,
            requested_by=self.student,
            amount_cents=5000,
            reason="Want money back",
        )
        refund.status = Refund.Status.DENIED
        refund.processed_by = self.owner
        refund.processed_at = timezone.now()
        refund.denial_reason = "Outside refund window"
        refund.save()
        assert refund.status == "denied"
        assert refund.denial_reason == "Outside refund window"

    def test_str_representation(self):
        refund = Refund.objects.create(
            academy=self.academy,
            payment=self.payment,
            requested_by=self.student,
            amount_cents=5000,
            reason="Test",
        )
        result = str(refund)
        assert self.payment.invoice_number in result


# ============================================================
# Trial Expiry Celery Task Tests
# ============================================================


@pytest.mark.integration
class TestExpirePlatformTrials(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-billing-expiry-iso",
            description="A test academy",
            email="billing-expiry-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-billing-expiry-iso",
            email="owner-billing-expiry-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.free_tier = AcademyTier.objects.create(
            name="Free",
            tier_level="free",
            price_cents=0,
            max_students=10,
            max_instructors=2,
            max_courses=5,
        )
        now = timezone.now()
        cls.platform_sub = PlatformSubscription.objects.create(
            academy=cls.academy,
            tier=cls.free_tier,
            status=PlatformSubscription.Status.TRIAL,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=14),
        )

    def test_expires_past_due_trials(self):
        self.platform_sub.trial_ends_at = timezone.now() - timedelta(hours=1)
        self.platform_sub.save()

        from apps.payments.tasks import expire_platform_trials
        count = expire_platform_trials()
        assert count == 1

        self.platform_sub.refresh_from_db()
        assert self.platform_sub.status == PlatformSubscription.Status.EXPIRED

    def test_does_not_expire_active_trials(self):
        self.platform_sub.trial_ends_at = timezone.now() + timedelta(days=7)
        self.platform_sub.status = PlatformSubscription.Status.TRIAL
        self.platform_sub.save()

        from apps.payments.tasks import expire_platform_trials
        count = expire_platform_trials()
        assert count == 0

        self.platform_sub.refresh_from_db()
        assert self.platform_sub.status == PlatformSubscription.Status.TRIAL

    def test_does_not_expire_stripe_managed(self):
        """Trials with a Stripe subscription ID should be managed by Stripe."""
        self.platform_sub.trial_ends_at = timezone.now() - timedelta(hours=1)
        self.platform_sub.status = PlatformSubscription.Status.TRIAL
        self.platform_sub.stripe_subscription_id = "sub_test123"
        self.platform_sub.save()

        from apps.payments.tasks import expire_platform_trials
        count = expire_platform_trials()
        assert count == 0

        self.platform_sub.refresh_from_db()
        assert self.platform_sub.status == PlatformSubscription.Status.TRIAL

    def test_does_not_touch_non_trial_subscriptions(self):
        self.platform_sub.status = PlatformSubscription.Status.ACTIVE
        self.platform_sub.stripe_subscription_id = ""
        self.platform_sub.save()

        from apps.payments.tasks import expire_platform_trials
        count = expire_platform_trials()
        assert count == 0


# ============================================================
# Trial Reminder Email Tests
# ============================================================


@pytest.mark.integration
class TestTrialReminderEmails(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-billing-reminder-iso",
            description="A test academy",
            email="billing-reminder-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-billing-reminder-iso",
            email="owner-billing-reminder-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.free_tier = AcademyTier.objects.create(
            name="Free",
            tier_level="free",
            price_cents=0,
            max_students=10,
            max_instructors=2,
            max_courses=5,
        )
        now = timezone.now()
        cls.platform_sub = PlatformSubscription.objects.create(
            academy=cls.academy,
            tier=cls.free_tier,
            status=PlatformSubscription.Status.TRIAL,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=14),
        )

    def test_sends_7d_reminder(self):
        self.platform_sub.trial_ends_at = timezone.now() + timedelta(days=5)
        self.platform_sub.trial_reminder_7d_sent = False
        self.platform_sub.save()

        from apps.payments.tasks import send_trial_reminder_emails
        count = send_trial_reminder_emails()
        assert count >= 1
        assert len(mail.outbox) >= 1
        assert "7 days" in mail.outbox[0].subject

        self.platform_sub.refresh_from_db()
        assert self.platform_sub.trial_reminder_7d_sent is True

    def test_does_not_resend_reminder(self):
        self.platform_sub.trial_ends_at = timezone.now() + timedelta(days=5)
        self.platform_sub.trial_reminder_7d_sent = True
        self.platform_sub.save()

        from apps.payments.tasks import send_trial_reminder_emails
        count = send_trial_reminder_emails()
        # Should not send 7d reminder again, but may send 3d
        for email in mail.outbox:
            assert "7 days" not in email.subject or count == 0

    def test_sends_1d_reminder(self):
        self.platform_sub.trial_ends_at = timezone.now() + timedelta(hours=12)
        self.platform_sub.trial_reminder_7d_sent = True
        self.platform_sub.trial_reminder_3d_sent = True
        self.platform_sub.trial_reminder_1d_sent = False
        self.platform_sub.save()

        from apps.payments.tasks import send_trial_reminder_emails
        count = send_trial_reminder_emails()
        assert count >= 1

        self.platform_sub.refresh_from_db()
        assert self.platform_sub.trial_reminder_1d_sent is True

    def test_no_reminders_for_active_subscriptions(self):
        self.platform_sub.status = PlatformSubscription.Status.ACTIVE
        self.platform_sub.save()

        from apps.payments.tasks import send_trial_reminder_emails
        count = send_trial_reminder_emails()
        assert count == 0

    def test_no_reminders_for_expired_trials(self):
        self.platform_sub.trial_ends_at = timezone.now() - timedelta(days=1)
        self.platform_sub.status = PlatformSubscription.Status.TRIAL
        self.platform_sub.save()

        from apps.payments.tasks import send_trial_reminder_emails
        count = send_trial_reminder_emails()
        assert count == 0


# ============================================================
# Owner Dashboard Financial Overview Tests
# ============================================================


@pytest.mark.integration
class TestOwnerDashboardFinancial(TestCase):
    """Tests that require a platform subscription to exist."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-billing-dashboard-iso",
            description="A test academy",
            email="billing-dashboard-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-billing-dashboard-iso",
            email="owner-billing-dashboard-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-billing-dashboard-iso",
            email="student-billing-dashboard-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student, academy=cls.academy, role="student",
            instruments=["Piano"], skill_level="beginner",
        )

        cls.free_tier = AcademyTier.objects.create(
            name="Free",
            tier_level="free",
            price_cents=0,
            max_students=10,
            max_instructors=2,
            max_courses=5,
        )
        now = timezone.now()
        cls.platform_sub = PlatformSubscription.objects.create(
            academy=cls.academy,
            tier=cls.free_tier,
            status=PlatformSubscription.Status.TRIAL,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=14),
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-billing-dashboard-iso@test.com",
            password="testpass123",
        )

    def test_dashboard_shows_platform_subscription(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200
        assert "Platform Subscription" in response.content.decode()

    def test_dashboard_shows_trial_countdown(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        content = response.content.decode()
        assert "days left in trial" in content

    def test_dashboard_shows_revenue(self):
        # Create a completed payment this month
        Payment.objects.create(
            academy=self.academy,
            student=self.student,
            amount_cents=5000,
            payment_type="course",
            status="completed",
            paid_at=timezone.now(),
        )
        response = self.auth_client.get(reverse("admin-dashboard"))
        content = response.content.decode()
        assert "$50.00" in content
        assert "Revenue this month" in content

    def test_dashboard_shows_zero_revenue(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        content = response.content.decode()
        assert "$0.00" in content

    def test_dashboard_shows_active_subscriptions_count(self):
        plan = SubscriptionPlan.objects.create(
            academy=self.academy,
            name="Monthly",
            price_cents=2999,
        )
        Subscription.objects.create(
            academy=self.academy,
            student=self.student,
            plan=plan,
            status="active",
        )
        response = self.auth_client.get(reverse("admin-dashboard"))
        content = response.content.decode()
        assert "Active subscriptions" in content


@pytest.mark.integration
class TestOwnerDashboardNoSubscription(TestCase):
    """Tests for dashboard behaviour when NO platform subscription exists."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-billing-nosub-iso",
            description="A test academy",
            email="billing-nosub-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-billing-nosub-iso",
            email="owner-billing-nosub-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-billing-nosub-iso",
            email="student-billing-nosub-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student, academy=cls.academy, role="student",
            instruments=["Piano"], skill_level="beginner",
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-billing-nosub-iso@test.com",
            password="testpass123",
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-billing-nosub-iso@test.com",
            password="testpass123",
        )

    def test_dashboard_no_subscription_empty_state(self):
        # No PlatformSubscription created for this academy
        response = self.auth_client.get(reverse("admin-dashboard"))
        content = response.content.decode()
        assert "No active subscription" in content

    def test_non_owner_cannot_access_admin_dashboard(self):
        response = self.student_client.get(reverse("admin-dashboard"))
        assert response.status_code == 302  # Redirect away
