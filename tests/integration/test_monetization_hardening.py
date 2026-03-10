"""Integration tests for Sprint 7: Monetization Hardening.

Tests the refund workflow (request/approve/deny), grace period logic,
payout detail view with breakdown, and webhook handlers.

Covers:
- RefundRequestView: student request, validations, duplicate prevention
- RefundListView: owner-only, lists academy refunds
- RefundDetailView: owner sees all, student sees own
- RefundActionView: approve/deny with status transitions
- Grace period: invoice.payment_failed handler, expire_grace_periods task
- PayoutDetailView: access control, breakdown calculation
"""

from datetime import timedelta

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Membership, User
from apps.academies.models import Academy
from apps.payments.models import (
    AcademyTier,
    InstructorPayout,
    Payment,
    PlatformSubscription,
    Refund,
    Subscription,
    SubscriptionPlan,
)


# ===================================================================
# TestRefundRequest — student requests a refund
# ===================================================================


@pytest.mark.integration
class TestRefundRequest(TestCase):
    """Test student refund request flow."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Refund Request Academy",
            slug="mon-refundreq-iso",
            description="Test academy",
            email="mon-refundreq@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-mon-refundreq",
            email="owner-mon-refundreq@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-mon-refundreq",
            email="student-mon-refundreq@test.com",
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

        cls.completed_payment = Payment.objects.create(
            academy=cls.academy,
            student=cls.student,
            amount_cents=5000,
            status=Payment.Status.COMPLETED,
            payment_type=Payment.PaymentType.COURSE,
            paid_at=timezone.now(),
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-mon-refundreq@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-mon-refundreq@test.com", password="testpass123"
        )

    def test_student_can_view_refund_form(self):
        """Student should see the refund request form."""
        url = reverse("refund-request", args=[self.completed_payment.pk])
        response = self.student_client.get(url)
        assert response.status_code == 200
        assert "refund" in response.content.decode().lower()

    def test_student_can_submit_refund_request(self):
        """Student can submit a refund request with reason."""
        url = reverse("refund-request", args=[self.completed_payment.pk])
        response = self.student_client.post(url, {"reason": "Changed my mind"})
        assert response.status_code == 302
        assert Refund.objects.filter(payment=self.completed_payment).exists()
        refund = Refund.objects.get(payment=self.completed_payment)
        assert refund.status == "requested"
        assert refund.amount_cents == self.completed_payment.amount_cents

    def test_refund_requires_reason(self):
        """Empty reason should show error, not create refund."""
        url = reverse("refund-request", args=[self.completed_payment.pk])
        response = self.student_client.post(url, {"reason": ""})
        assert response.status_code == 200  # re-renders form
        assert not Refund.objects.filter(payment=self.completed_payment).exists()

    def test_duplicate_refund_prevented(self):
        """Cannot submit second refund for same payment if one is pending."""
        # Use a fresh payment so this test is independent of other test methods
        payment = Payment.objects.create(
            academy=self.academy,
            student=self.student,
            amount_cents=5000,
            status=Payment.Status.COMPLETED,
            payment_type=Payment.PaymentType.COURSE,
            paid_at=timezone.now(),
        )
        Refund.objects.create(
            academy=self.academy,
            payment=payment,
            requested_by=self.student,
            amount_cents=payment.amount_cents,
            reason="First request",
            status="requested",
        )
        url = reverse("refund-request", args=[payment.pk])
        response = self.student_client.post(url, {"reason": "Second request"})
        assert response.status_code == 302
        assert Refund.objects.filter(payment=payment).count() == 1

    def test_cannot_refund_failed_payment(self):
        """Failed payment should not be refundable."""
        payment = Payment.objects.create(
            academy=self.academy,
            student=self.student,
            amount_cents=3000,
            status=Payment.Status.FAILED,
            payment_type="course",
            paid_at=timezone.now(),
        )
        url = reverse("refund-request", args=[payment.pk])
        response = self.student_client.post(url, {"reason": "Want refund"})
        assert response.status_code == 302
        assert not Refund.objects.filter(payment=payment).exists()

    def test_other_student_cannot_request_refund(self):
        """Another student should not see someone else's payment."""
        other_student = User.objects.create_user(
            username="other-refundreq",
            email="other-refundreq@test.com",
            password="testpass123",
        )
        other_student.current_academy = self.academy
        other_student.save()
        Membership.objects.create(
            user=other_student, academy=self.academy, role="student"
        )
        client = Client()
        client.force_login(other_student)
        url = reverse("refund-request", args=[self.completed_payment.pk])
        response = client.get(url)
        assert response.status_code == 404


# ===================================================================
# TestRefundList — owner-only refund management
# ===================================================================


@pytest.mark.integration
class TestRefundList(TestCase):
    """Test owner refund list view."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Refund List Academy",
            slug="mon-refundlist-iso",
            description="Test academy",
            email="mon-refundlist@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-mon-refundlist",
            email="owner-mon-refundlist@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-mon-refundlist",
            email="student-mon-refundlist@test.com",
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

        cls.completed_payment = Payment.objects.create(
            academy=cls.academy,
            student=cls.student,
            amount_cents=5000,
            status=Payment.Status.COMPLETED,
            payment_type=Payment.PaymentType.COURSE,
            paid_at=timezone.now(),
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-mon-refundlist@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-mon-refundlist@test.com", password="testpass123"
        )

    def test_owner_can_view_refund_list(self):
        """Owner should get 200 on refund list."""
        url = reverse("refund-list")
        response = self.auth_client.get(url)
        assert response.status_code == 200

    def test_student_cannot_view_refund_list(self):
        """Student should get 403 on refund list."""
        url = reverse("refund-list")
        response = self.student_client.get(url)
        assert response.status_code == 403

    def test_refund_list_shows_refunds(self):
        """Refund list should display refund entries."""
        Refund.objects.create(
            academy=self.academy,
            payment=self.completed_payment,
            requested_by=self.student,
            amount_cents=5000,
            reason="Test reason",
            status="requested",
        )
        url = reverse("refund-list")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Test" in content  # student name or reason visible


# ===================================================================
# TestRefundAction — owner approve/deny
# ===================================================================


@pytest.mark.integration
class TestRefundAction(TestCase):
    """Test owner approve/deny refund actions."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Refund Action Academy",
            slug="mon-refundact-iso",
            description="Test academy",
            email="mon-refundact@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-mon-refundact",
            email="owner-mon-refundact@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-mon-refundact",
            email="student-mon-refundact@test.com",
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

        cls.completed_payment = Payment.objects.create(
            academy=cls.academy,
            student=cls.student,
            amount_cents=5000,
            status=Payment.Status.COMPLETED,
            payment_type=Payment.PaymentType.COURSE,
            paid_at=timezone.now(),
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-mon-refundact@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-mon-refundact@test.com", password="testpass123"
        )
        # Each test gets a fresh pending refund so mutations don't bleed across tests.
        self.pending_refund = Refund.objects.create(
            academy=self.academy,
            payment=self.completed_payment,
            requested_by=self.student,
            amount_cents=5000,
            reason="Want refund",
            status="requested",
        )

    def tearDown(self):
        # Remove the per-test refund to keep setUpTestData objects clean.
        Refund.objects.filter(pk=self.pending_refund.pk).delete()

    def test_owner_can_approve_refund(self):
        """Owner approving should set status to approved."""
        url = reverse("refund-action", args=[self.pending_refund.pk, "approve"])
        response = self.auth_client.post(url)
        assert response.status_code == 302
        self.pending_refund.refresh_from_db()
        assert self.pending_refund.status == "approved"
        assert self.pending_refund.processed_by is not None
        assert self.pending_refund.processed_at is not None

    def test_owner_can_deny_refund(self):
        """Owner denying with reason should set status to denied."""
        url = reverse("refund-action", args=[self.pending_refund.pk, "deny"])
        response = self.auth_client.post(
            url, {"denial_reason": "Outside refund window"}
        )
        assert response.status_code == 302
        self.pending_refund.refresh_from_db()
        assert self.pending_refund.status == "denied"
        assert self.pending_refund.denial_reason == "Outside refund window"

    def test_deny_requires_reason(self):
        """Denying without reason should redirect without changing status."""
        url = reverse("refund-action", args=[self.pending_refund.pk, "deny"])
        response = self.auth_client.post(url, {"denial_reason": ""})
        assert response.status_code == 302
        self.pending_refund.refresh_from_db()
        assert self.pending_refund.status == "requested"  # unchanged

    def test_cannot_process_already_processed(self):
        """Already processed refund should not be re-processed."""
        self.pending_refund.status = "approved"
        self.pending_refund.save()
        url = reverse("refund-action", args=[self.pending_refund.pk, "approve"])
        response = self.auth_client.post(url)
        assert response.status_code == 302  # redirects with warning

    def test_student_cannot_approve_refund(self):
        """Student should get 403 trying to approve."""
        url = reverse("refund-action", args=[self.pending_refund.pk, "approve"])
        response = self.student_client.post(url)
        assert response.status_code == 403

    def test_invalid_action_redirects(self):
        """Invalid action string should redirect with error."""
        url = reverse("refund-action", args=[self.pending_refund.pk, "cancel"])
        response = self.auth_client.post(url)
        assert response.status_code == 302


# ===================================================================
# TestRefundDetail — viewing refund details
# ===================================================================


@pytest.mark.integration
class TestRefundDetail(TestCase):
    """Test refund detail view access control."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Refund Detail Academy",
            slug="mon-refunddet-iso",
            description="Test academy",
            email="mon-refunddet@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-mon-refunddet",
            email="owner-mon-refunddet@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-mon-refunddet",
            email="student-mon-refunddet@test.com",
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

        cls.completed_payment = Payment.objects.create(
            academy=cls.academy,
            student=cls.student,
            amount_cents=5000,
            status=Payment.Status.COMPLETED,
            payment_type=Payment.PaymentType.COURSE,
            paid_at=timezone.now(),
        )
        cls.refund = Refund.objects.create(
            academy=cls.academy,
            payment=cls.completed_payment,
            requested_by=cls.student,
            amount_cents=5000,
            reason="Want refund",
            status="requested",
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-mon-refunddet@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-mon-refunddet@test.com", password="testpass123"
        )

    def test_owner_can_view_any_refund(self):
        """Owner should see refund detail."""
        url = reverse("refund-detail", args=[self.refund.pk])
        response = self.auth_client.get(url)
        assert response.status_code == 200

    def test_student_can_view_own_refund(self):
        """Student should see their own refund detail."""
        url = reverse("refund-detail", args=[self.refund.pk])
        response = self.student_client.get(url)
        assert response.status_code == 200

    def test_other_student_cannot_view_refund(self):
        """Another student should get 404 for someone else's refund."""
        other = User.objects.create_user(
            username="other-mon-refunddet",
            email="other-mon-refunddet@test.com",
            password="testpass123",
        )
        other.current_academy = self.academy
        other.save()
        Membership.objects.create(user=other, academy=self.academy, role="student")
        client = Client()
        client.force_login(other)
        url = reverse("refund-detail", args=[self.refund.pk])
        response = client.get(url)
        assert response.status_code == 404


# ===================================================================
# TestGracePeriod — invoice.payment_failed webhook + expiry task
# ===================================================================


@pytest.mark.integration
class TestGracePeriod(TestCase):
    """Test grace period logic for payment failures."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Grace Period Academy",
            slug="mon-grace-iso",
            description="Test academy",
            email="mon-grace@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-mon-grace",
            email="owner-mon-grace@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.tier = AcademyTier.objects.create(
            name="Pro",
            tier_level="pro",
            price_cents=2900,
            max_students=100,
            max_instructors=10,
            max_courses=50,
        )

    def setUp(self):
        # No HTTP clients needed for these tests — they exercise service functions directly.
        pass

    def test_payment_failed_triggers_grace_period(self):
        """invoice.payment_failed should move platform sub to grace."""
        from apps.payments.stripe_service import handle_invoice_payment_failed

        platform_sub = PlatformSubscription.objects.create(
            academy=self.academy,
            tier=self.tier,
            status=PlatformSubscription.Status.ACTIVE,
            stripe_subscription_id="sub_test_grace_123",
        )

        handle_invoice_payment_failed(
            {
                "subscription": "sub_test_grace_123",
            }
        )

        platform_sub.refresh_from_db()
        assert platform_sub.status == "grace"
        assert platform_sub.grace_period_ends_at is not None

    def test_grace_period_is_7_days(self):
        """Grace period should be approximately 7 days from now."""
        from apps.payments.stripe_service import handle_invoice_payment_failed

        platform_sub = PlatformSubscription.objects.create(
            academy=self.academy,
            tier=self.tier,
            status=PlatformSubscription.Status.ACTIVE,
            stripe_subscription_id="sub_test_grace_456",
        )

        handle_invoice_payment_failed({"subscription": "sub_test_grace_456"})

        platform_sub.refresh_from_db()
        days_until = (platform_sub.grace_period_ends_at - timezone.now()).days
        assert 6 <= days_until <= 7

    def test_student_sub_marked_past_due_on_failure(self):
        """Student subscription should be marked past_due on payment failure."""
        from apps.payments.stripe_service import handle_invoice_payment_failed

        plan = SubscriptionPlan.objects.create(
            academy=self.academy,
            name="Monthly",
            price_cents=999,
            billing_cycle="monthly",
        )
        sub_student = User.objects.create_user(
            username="sub-student-mon-grace",
            email="sub-student-mon-grace@test.com",
            password="test123",
        )
        sub = Subscription.objects.create(
            academy=self.academy,
            student=sub_student,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_student_grace_789",
        )

        handle_invoice_payment_failed({"subscription": "sub_student_grace_789"})

        sub.refresh_from_db()
        assert sub.status == "past_due"

    def test_expire_grace_periods_task(self):
        """expire_grace_periods should expire subscriptions past grace."""
        from apps.payments.tasks import expire_grace_periods

        PlatformSubscription.objects.create(
            academy=self.academy,
            tier=self.tier,
            status=PlatformSubscription.Status.GRACE,
            grace_period_ends_at=timezone.now() - timedelta(hours=1),
        )

        count = expire_grace_periods()
        assert count == 1

        sub = PlatformSubscription.objects.filter(
            academy=self.academy,
            status="expired",
        ).first()
        assert sub is not None
        assert sub.status == "expired"

    def test_active_grace_not_expired(self):
        """Grace period not yet past should not be expired."""
        from apps.payments.tasks import expire_grace_periods

        PlatformSubscription.objects.create(
            academy=self.academy,
            tier=self.tier,
            status=PlatformSubscription.Status.GRACE,
            grace_period_ends_at=timezone.now() + timedelta(days=3),
        )

        count = expire_grace_periods()
        assert count == 0


# ===================================================================
# TestPayoutDetail — payout detail view with breakdown
# ===================================================================


@pytest.mark.integration
class TestPayoutDetail(TestCase):
    """Test payout detail view access control and breakdown."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Payout Detail Academy",
            slug="mon-payout-iso",
            description="Test academy",
            email="mon-payout@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-mon-payout",
            email="owner-mon-payout@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="instructor-mon-payout",
            email="instructor-mon-payout@test.com",
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
            username="student-mon-payout",
            email="student-mon-payout@test.com",
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

        cls.payout = InstructorPayout.objects.create(
            academy=cls.academy,
            instructor=cls.instructor,
            amount_cents=10000,
            period_start=timezone.now().date() - timedelta(days=30),
            period_end=timezone.now().date(),
            status="completed",
            paid_at=timezone.now(),
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-mon-payout@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-mon-payout@test.com", password="testpass123"
        )

    def test_owner_can_view_payout_detail(self):
        """Owner should see payout detail."""
        url = reverse("payout-detail", args=[self.payout.pk])
        response = self.auth_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Payout" in content
        assert "Breakdown" in content or "Financial" in content

    def test_instructor_can_view_own_payout(self):
        """Instructor should see their own payout detail."""
        client = Client()
        client.login(username="instructor-mon-payout@test.com", password="testpass123")
        url = reverse("payout-detail", args=[self.payout.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_student_cannot_view_payout(self):
        """Student should get 403 on payout detail."""
        url = reverse("payout-detail", args=[self.payout.pk])
        response = self.student_client.get(url)
        assert response.status_code == 403

    def test_instructor_cannot_view_other_payout(self):
        """Instructor should not see another instructor's payout."""
        other_instructor = User.objects.create_user(
            username="other-inst-mon-payout",
            email="other-inst-mon-payout@test.com",
            password="testpass123",
        )
        other_instructor.current_academy = self.academy
        other_instructor.save()
        Membership.objects.create(
            user=other_instructor, academy=self.academy, role="instructor"
        )
        client = Client()
        client.force_login(other_instructor)
        url = reverse("payout-detail", args=[self.payout.pk])
        response = client.get(url)
        assert response.status_code == 403

    def test_payout_detail_shows_breakdown_values(self):
        """Payout detail should contain breakdown amounts."""
        url = reverse("payout-detail", args=[self.payout.pk])
        response = self.auth_client.get(url)
        content = response.content.decode()
        # Net payout should be displayed
        assert "$100.00" in content  # 10000 cents = $100.00


# ===================================================================
# TestAdminDashboardRefundButton — Refunds button on dashboard
# ===================================================================


@pytest.mark.integration
class TestAdminDashboardRefundButton(TestCase):
    """Test Refunds button on admin dashboard."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Dashboard Refund Academy",
            slug="mon-dashrefund-iso",
            description="Test academy",
            email="mon-dashrefund@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-mon-dashrefund",
            email="owner-mon-dashrefund@test.com",
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
            username="owner-mon-dashrefund@test.com", password="testpass123"
        )

    def test_refund_button_present(self):
        """Admin dashboard should have a Refunds button."""
        url = reverse("admin-dashboard")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert reverse("refund-list") in content
