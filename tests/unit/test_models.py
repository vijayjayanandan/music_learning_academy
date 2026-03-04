"""Model tests — properties, constraints, edge cases."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment, LessonProgress
from apps.payments.models import SubscriptionPlan, Subscription, Coupon, Payment


@pytest.mark.unit
class TestUserModel:
    def test_create_user(self, db):
        user = User.objects.create_user(
            username="test", email="test@test.com", password="pass123"
        )
        assert user.email == "test@test.com"
        assert user.check_password("pass123")
        assert user.USERNAME_FIELD == "email"

    def test_get_role_in_academy(self, owner_user, academy):
        assert owner_user.get_role_in(academy) == "owner"

    def test_get_role_in_unknown_academy(self, owner_user, db):
        other = Academy.objects.create(
            name="Other", slug="other", description="x",
            email="other@test.com", timezone="UTC",
        )
        assert owner_user.get_role_in(other) is None

    def test_get_academies(self, owner_user, academy):
        academies = owner_user.get_academies()
        assert academy in academies

    def test_wants_email_default_true(self, owner_user):
        assert owner_user.wants_email("session_reminder") is True

    def test_wants_email_disabled(self, owner_user):
        owner_user.email_preferences = {"session_reminder": False}
        owner_user.save()
        assert owner_user.wants_email("session_reminder") is False

    def test_str_returns_email(self, owner_user):
        assert str(owner_user) == "owner@test.com"


@pytest.mark.unit
class TestAcademyModel:
    def test_create_academy(self, academy):
        assert academy.name == "Test Music Academy"
        assert academy.slug == "test-academy"
        assert academy.is_active is True

    def test_str(self, academy):
        assert str(academy) == "Test Music Academy"


@pytest.mark.unit
class TestMembershipModel:
    def test_membership_role(self, owner_user, academy):
        membership = Membership.objects.get(user=owner_user, academy=academy)
        assert membership.role == "owner"

    def test_unique_user_academy(self, owner_user, academy):
        with pytest.raises(Exception):
            Membership.objects.create(
                user=owner_user, academy=academy, role="student"
            )


@pytest.mark.unit
class TestCourseModel:
    def test_create_course(self, db, academy, instructor_user):
        course = Course.objects.create(
            academy=academy,
            title="Piano 101",
            slug="piano-101",
            instructor=instructor_user,
            instrument="Piano",
            difficulty_level="beginner",
            is_published=True,
        )
        assert course.title == "Piano 101"
        assert course.lesson_count == 0
        assert course.enrolled_count == 0

    def test_lesson_ordering(self, db, academy, instructor_user):
        course = Course.objects.create(
            academy=academy, title="Test Course", slug="test-course",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", is_published=True,
        )
        lesson2 = Lesson.objects.create(
            academy=academy, course=course, title="Lesson 2", order=2,
        )
        lesson1 = Lesson.objects.create(
            academy=academy, course=course, title="Lesson 1", order=1,
        )
        lessons = list(course.lessons.all())
        assert lessons[0] == lesson1
        assert lessons[1] == lesson2

    def test_is_free_property(self, db, academy, instructor_user):
        free = Course.objects.create(
            academy=academy, title="Free", slug="free",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", price_cents=0,
        )
        paid = Course.objects.create(
            academy=academy, title="Paid", slug="paid",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", price_cents=2999,
        )
        assert free.is_free is True
        assert paid.is_free is False

    def test_price_display(self, db, academy, instructor_user):
        course = Course.objects.create(
            academy=academy, title="Priced", slug="priced",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", price_cents=2999,
        )
        assert course.price_display == "$29.99"

    def test_price_display_free(self, db, academy, instructor_user):
        course = Course.objects.create(
            academy=academy, title="Free Course", slug="free-course",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", price_cents=0,
        )
        assert course.price_display == "Free"


@pytest.mark.unit
class TestEnrollmentModel:
    def test_progress_percent_no_lessons(self, db, academy, instructor_user, student_user):
        course = Course.objects.create(
            academy=academy, title="Empty", slug="empty",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner",
        )
        enrollment = Enrollment.objects.create(
            student=student_user, course=course, academy=academy,
        )
        assert enrollment.progress_percent == 0

    def test_progress_percent_partial(self, db, academy, instructor_user, student_user):
        course = Course.objects.create(
            academy=academy, title="Progress Test", slug="progress-test",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner",
        )
        l1 = Lesson.objects.create(academy=academy, course=course, title="L1", order=1)
        l2 = Lesson.objects.create(academy=academy, course=course, title="L2", order=2)
        enrollment = Enrollment.objects.create(
            student=student_user, course=course, academy=academy,
        )
        LessonProgress.objects.create(
            enrollment=enrollment, lesson=l1, academy=academy, is_completed=True,
        )
        assert enrollment.progress_percent == 50

    def test_progress_percent_complete(self, db, academy, instructor_user, student_user):
        course = Course.objects.create(
            academy=academy, title="Complete", slug="complete",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner",
        )
        l1 = Lesson.objects.create(academy=academy, course=course, title="L1", order=1)
        enrollment = Enrollment.objects.create(
            student=student_user, course=course, academy=academy,
        )
        LessonProgress.objects.create(
            enrollment=enrollment, lesson=l1, academy=academy, is_completed=True,
        )
        assert enrollment.progress_percent == 100

    def test_unique_enrollment(self, db, academy, instructor_user, student_user):
        course = Course.objects.create(
            academy=academy, title="Unique", slug="unique",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner",
        )
        Enrollment.objects.create(
            student=student_user, course=course, academy=academy,
        )
        with pytest.raises(Exception):
            Enrollment.objects.create(
                student=student_user, course=course, academy=academy,
            )


@pytest.mark.unit
class TestCouponModel:
    def test_coupon_is_valid(self, db, academy):
        coupon = Coupon.objects.create(
            academy=academy, code="VALID20", discount_type="percentage",
            discount_value=20, is_active=True,
        )
        assert coupon.is_valid is True

    def test_coupon_expired(self, db, academy):
        coupon = Coupon.objects.create(
            academy=academy, code="EXPIRED", discount_type="percentage",
            discount_value=20, is_active=True,
            expires_at=timezone.now() - timedelta(days=1),
        )
        assert coupon.is_valid is False

    def test_coupon_max_uses_reached(self, db, academy):
        coupon = Coupon.objects.create(
            academy=academy, code="MAXED", discount_type="percentage",
            discount_value=20, is_active=True, max_uses=5, times_used=5,
        )
        assert coupon.is_valid is False

    def test_coupon_inactive(self, db, academy):
        coupon = Coupon.objects.create(
            academy=academy, code="INACTIVE", discount_type="percentage",
            discount_value=20, is_active=False,
        )
        assert coupon.is_valid is False

    def test_coupon_unlimited_uses(self, db, academy):
        coupon = Coupon.objects.create(
            academy=academy, code="UNLIMITED", discount_type="percentage",
            discount_value=20, is_active=True, max_uses=0, times_used=100,
        )
        assert coupon.is_valid is True

    def test_coupon_str_percentage(self, db, academy):
        coupon = Coupon.objects.create(
            academy=academy, code="PCT", discount_type="percentage",
            discount_value=20, is_active=True,
        )
        assert "20%" in str(coupon)

    def test_coupon_str_fixed(self, db, academy):
        coupon = Coupon.objects.create(
            academy=academy, code="FIXED", discount_type="fixed_amount",
            discount_value=1000, is_active=True,
        )
        assert "$10.00" in str(coupon)


@pytest.mark.unit
class TestSubscriptionModel:
    def test_is_valid_active(self, db, academy, student_user):
        plan = SubscriptionPlan.objects.create(
            academy=academy, name="Active Plan", price_cents=999,
            billing_cycle="monthly",
        )
        sub = Subscription.objects.create(
            academy=academy, student=student_user, plan=plan, status="active",
        )
        assert sub.is_valid is True

    def test_is_valid_trialing(self, db, academy, student_user):
        plan = SubscriptionPlan.objects.create(
            academy=academy, name="Trial Plan", price_cents=999,
            billing_cycle="monthly",
        )
        sub = Subscription.objects.create(
            academy=academy, student=student_user, plan=plan, status="trialing",
        )
        assert sub.is_valid is True

    def test_is_valid_cancelled(self, db, academy, student_user):
        plan = SubscriptionPlan.objects.create(
            academy=academy, name="Cancelled Plan", price_cents=999,
            billing_cycle="monthly",
        )
        sub = Subscription.objects.create(
            academy=academy, student=student_user, plan=plan, status="cancelled",
        )
        assert sub.is_valid is False


@pytest.mark.unit
class TestPaymentModel:
    def test_auto_invoice_number(self, db, academy, student_user):
        payment = Payment.objects.create(
            academy=academy, student=student_user,
            amount_cents=2999, payment_type="subscription",
            status="completed",
        )
        assert payment.invoice_number.startswith("INV-")
        assert len(payment.invoice_number) == 12  # INV- + 8 hex chars

    def test_amount_display(self, db, academy, student_user):
        payment = Payment.objects.create(
            academy=academy, student=student_user,
            amount_cents=2999, payment_type="subscription",
            status="completed",
        )
        assert payment.amount_display == "$29.99"
