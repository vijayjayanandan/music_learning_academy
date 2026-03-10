"""Tests for Celery tasks."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.payments.models import SubscriptionPlan, Subscription, Payment
from apps.scheduling.models import LiveSession


@pytest.fixture
def task_academy(db):
    return Academy.objects.create(
        name="Task Academy", slug="task-academy",
        description="Test", email="task@test.com", timezone="UTC",
    )


@pytest.fixture
def task_instructor(db, task_academy):
    user = User.objects.create_user(
        username="task_instructor", email="taskinst@test.com", password="testpass123",
    )
    user.current_academy = task_academy
    user.save()
    Membership.objects.create(user=user, academy=task_academy, role="instructor")
    return user


@pytest.fixture
def task_student(db, task_academy):
    user = User.objects.create_user(
        username="task_student", email="taskstu@test.com", password="testpass123",
    )
    user.current_academy = task_academy
    user.save()
    Membership.objects.create(user=user, academy=task_academy, role="student")
    return user


@pytest.mark.unit
class TestExpireTrials:
    @pytest.mark.django_db
    def test_expires_past_due_trials(self, task_academy, task_student):
        plan = SubscriptionPlan.objects.create(
            academy=task_academy, name="Trial Plan",
            price_cents=999, billing_cycle="monthly", trial_days=7,
        )
        sub = Subscription.objects.create(
            academy=task_academy, student=task_student, plan=plan,
            status="trialing", trial_end=timezone.now() - timedelta(hours=1),
        )
        from apps.payments.tasks import expire_trials
        count = expire_trials()
        assert count == 1
        sub.refresh_from_db()
        assert sub.status == "expired"

    @pytest.mark.django_db
    def test_does_not_expire_active_trials(self, task_academy, task_student):
        plan = SubscriptionPlan.objects.create(
            academy=task_academy, name="Active Trial Plan",
            price_cents=999, billing_cycle="monthly", trial_days=7,
        )
        Subscription.objects.create(
            academy=task_academy, student=task_student, plan=plan,
            status="trialing", trial_end=timezone.now() + timedelta(days=3),
        )
        from apps.payments.tasks import expire_trials
        count = expire_trials()
        assert count == 0

    @pytest.mark.django_db
    def test_does_not_expire_active_subscriptions(self, task_academy, task_student):
        plan = SubscriptionPlan.objects.create(
            academy=task_academy, name="Active Plan",
            price_cents=999, billing_cycle="monthly",
        )
        Subscription.objects.create(
            academy=task_academy, student=task_student, plan=plan,
            status="active",
        )
        from apps.payments.tasks import expire_trials
        count = expire_trials()
        assert count == 0


@pytest.mark.unit
class TestSendSessionReminders:
    @pytest.mark.django_db
    @patch("django.core.mail.send_mail")
    def test_sends_24h_reminder(self, mock_send_mail, task_academy, task_instructor):
        now = timezone.now()
        session = LiveSession.objects.create(
            academy=task_academy, title="Test Session",
            instructor=task_instructor,
            scheduled_start=now + timedelta(hours=24),
            scheduled_end=now + timedelta(hours=25),
            session_type="one_on_one",
            room_name="reminder-room",
            reminder_24h_sent=False,
        )
        from apps.scheduling.tasks import send_session_reminders
        count = send_session_reminders()
        session.refresh_from_db()
        assert session.reminder_24h_sent is True
        assert count >= 1

    @pytest.mark.django_db
    @patch("django.core.mail.send_mail")
    def test_does_not_resend_reminder(self, mock_send_mail, task_academy, task_instructor):
        now = timezone.now()
        LiveSession.objects.create(
            academy=task_academy, title="Already Reminded",
            instructor=task_instructor,
            scheduled_start=now + timedelta(hours=24),
            scheduled_end=now + timedelta(hours=25),
            session_type="one_on_one",
            room_name="reminded-room",
            reminder_24h_sent=True,
            reminder_1h_sent=True,
        )
        from apps.scheduling.tasks import send_session_reminders
        count = send_session_reminders()
        assert count == 0


@pytest.mark.unit
class TestSendPaymentConfirmationEmail:
    @pytest.mark.django_db
    @patch("django.core.mail.send_mail")
    def test_sends_email_for_valid_payment(self, mock_send_mail, task_academy, task_student):
        payment = Payment.objects.create(
            academy=task_academy, student=task_student,
            amount_cents=2999, payment_type="subscription",
            status="completed", paid_at=timezone.now(),
        )
        from apps.payments.tasks import send_payment_confirmation_email
        send_payment_confirmation_email(payment.pk)
        mock_send_mail.assert_called_once()

    @pytest.mark.django_db
    @patch("django.core.mail.send_mail")
    def test_handles_missing_payment(self, mock_send_mail):
        from apps.payments.tasks import send_payment_confirmation_email
        # Should not raise
        send_payment_confirmation_email(99999)
        mock_send_mail.assert_not_called()

    @pytest.mark.django_db
    @patch("django.core.mail.send_mail")
    def test_respects_email_preferences(self, mock_send_mail, task_academy, task_student):
        task_student.email_preferences = {"payment_confirmation": False}
        task_student.save()
        payment = Payment.objects.create(
            academy=task_academy, student=task_student,
            amount_cents=2999, payment_type="subscription",
            status="completed", paid_at=timezone.now(),
        )
        from apps.payments.tasks import send_payment_confirmation_email
        send_payment_confirmation_email(payment.pk)
        mock_send_mail.assert_not_called()
