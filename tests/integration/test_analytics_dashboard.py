"""Integration tests for Sprint 6: Analytics & Decision Support.

Tests the owner analytics dashboard view, analytics service layer,
priority CTA logic, and the Analytics button on admin dashboard.

Covers:
- OwnerAnalyticsView access control (owner-only)
- Period selector (7d, 30d, 90d) and invalid values
- Analytics sections render (Revenue, Funnel, Learning Quality)
- Data freshness label
- Breadcrumbs and navigation
- RevenueAnalytics service (MRR, ARPU, revenue summary, trend)
- FunnelAnalytics service (funnel stages, enrollment breakdown)
- LearningAnalytics service (progress, completion, attendance)
- Priority CTA on admin dashboard
- Analytics button on admin dashboard
"""

from datetime import timedelta

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.dashboards.analytics import (
    FunnelAnalytics,
    LearningAnalytics,
    RevenueAnalytics,
)
from tests.factories import UserFactory


# ===================================================================
# TestAnalyticsAccessControl — owner-only, redirect for others
# ===================================================================


@pytest.mark.integration
class TestAnalyticsAccessControl(TestCase):
    """Verify only owners can access the analytics dashboard."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Analytics Access Academy",
            slug="analytics-access-academy",
            description="A test academy",
            email="analytics-access@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="analytics-access-owner",
            email="analytics-access-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="analytics-access-student",
            email="analytics-access-student@test.com",
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

        cls.instructor = User.objects.create_user(
            username="analytics-access-instructor",
            email="analytics-access-instructor@test.com",
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

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="analytics-access-owner@test.com", password="testpass123"
        )

    def test_owner_can_access_analytics(self):
        """Owner should get 200 on the analytics page."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        assert response.status_code == 200

    def test_student_redirected_from_analytics(self):
        """Students should be redirected away from analytics."""
        student_client = Client()
        student_client.login(
            username="analytics-access-student@test.com", password="testpass123"
        )
        url = reverse("owner-analytics")
        response = student_client.get(url)
        assert response.status_code == 302

    def test_instructor_redirected_from_analytics(self):
        """Instructors should be redirected away from analytics."""
        instructor_client = Client()
        instructor_client.login(
            username="analytics-access-instructor@test.com", password="testpass123"
        )
        url = reverse("owner-analytics")
        response = instructor_client.get(url)
        assert response.status_code == 302

    def test_anonymous_redirected_to_login(self):
        """Anonymous users should be redirected to login."""
        anon_client = Client()
        url = reverse("owner-analytics")
        response = anon_client.get(url)
        assert response.status_code == 302
        assert "login" in response.url or "accounts" in response.url


# ===================================================================
# TestAnalyticsPeriodSelector — days parameter validation
# ===================================================================


@pytest.mark.integration
class TestAnalyticsPeriodSelector(TestCase):
    """Verify the ?days= parameter handling."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Analytics Period Academy",
            slug="analytics-period-academy",
            description="A test academy",
            email="analytics-period@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="analytics-period-owner",
            email="analytics-period-owner@test.com",
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
            username="analytics-period-owner@test.com", password="testpass123"
        )

    def test_default_period_is_30_days(self):
        """Without ?days=, selected_days should be 30."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        assert response.context["selected_days"] == 30

    def test_7_day_period(self):
        """?days=7 should set selected_days to 7."""
        url = reverse("owner-analytics") + "?days=7"
        response = self.auth_client.get(url)
        assert response.context["selected_days"] == 7

    def test_90_day_period(self):
        """?days=90 should set selected_days to 90."""
        url = reverse("owner-analytics") + "?days=90"
        response = self.auth_client.get(url)
        assert response.context["selected_days"] == 90

    def test_invalid_period_defaults_to_30(self):
        """?days=15 (not in allowed set) should default to 30."""
        url = reverse("owner-analytics") + "?days=15"
        response = self.auth_client.get(url)
        assert response.context["selected_days"] == 30

    def test_non_numeric_period_defaults_to_30(self):
        """?days=abc should default to 30."""
        url = reverse("owner-analytics") + "?days=abc"
        response = self.auth_client.get(url)
        assert response.context["selected_days"] == 30


# ===================================================================
# TestAnalyticsContent — sections render correctly
# ===================================================================


@pytest.mark.integration
class TestAnalyticsContent(TestCase):
    """Verify the analytics dashboard renders expected content."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Analytics Content Academy",
            slug="analytics-content-academy",
            description="A test academy",
            email="analytics-content@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="analytics-content-owner",
            email="analytics-content-owner@test.com",
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
            username="analytics-content-owner@test.com", password="testpass123"
        )

    def test_page_title(self):
        """Page should have Analytics in the title."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Analytics" in content

    def test_breadcrumbs_present(self):
        """Breadcrumbs should link back to Dashboard."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Dashboard" in content
        assert reverse("admin-dashboard") in content

    def test_revenue_section_present(self):
        """Revenue section should render."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Revenue" in content
        assert "Monthly Recurring Revenue" in content

    def test_funnel_section_present(self):
        """Funnel section should render."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Funnel" in content
        assert "Joined" in content
        assert "Enrolled" in content

    def test_learning_quality_section_present(self):
        """Learning Quality section should render."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Learning Quality" in content
        assert "Completion Rate" in content

    def test_data_freshness_label(self):
        """Data freshness label should be present."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Data as of" in content

    def test_period_selector_buttons(self):
        """Period selector should show 7/30/90 day buttons."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "7 days" in content
        assert "30 days" in content
        assert "90 days" in content

    def test_context_has_required_keys(self):
        """View context should contain all analytics data."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        ctx = response.context
        assert "mrr" in ctx
        assert "mrr_display" in ctx
        assert "arpu" in ctx
        assert "arpu_display" in ctx
        assert "revenue_summary" in ctx
        assert "revenue_trend" in ctx
        assert "funnel" in ctx
        assert "enrollment_breakdown" in ctx
        assert "learning" in ctx
        assert "data_freshness" in ctx

    def test_enrollment_breakdown_present(self):
        """Enrollment breakdown stats should render."""
        url = reverse("owner-analytics")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Enrollment Status" in content


# ===================================================================
# TestRevenueAnalytics — service layer unit-level tests
# ===================================================================


@pytest.mark.integration
class TestRevenueAnalytics(TestCase):
    """Test RevenueAnalytics service methods."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Revenue Analytics Academy",
            slug="revenue-analytics-academy",
            description="A test academy",
            email="revenue-analytics@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="revenue-analytics-owner",
            email="revenue-analytics-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def test_mrr_returns_integer(self):
        """MRR should return an integer (cents)."""
        result = RevenueAnalytics.get_mrr(self.academy)
        assert isinstance(result, int)

    def test_mrr_zero_with_no_subscriptions(self):
        """MRR should be 0 when there are no active subscriptions."""
        result = RevenueAnalytics.get_mrr(self.academy)
        assert result == 0

    def test_arpu_zero_with_no_students(self):
        """ARPU should be 0 when there are no students."""
        result = RevenueAnalytics.get_arpu(self.academy)
        assert result == 0

    def test_revenue_summary_structure(self):
        """Revenue summary should return expected dict keys."""
        result = RevenueAnalytics.get_revenue_summary(self.academy)
        assert "total_cents" in result
        assert "total_display" in result
        assert "by_type" in result
        assert "completed_count" in result
        assert "refund_count" in result
        assert "refund_rate" in result
        assert "failed_count" in result

    def test_revenue_summary_empty_academy(self):
        """Empty academy should have zero revenue."""
        result = RevenueAnalytics.get_revenue_summary(self.academy)
        assert result["total_cents"] == 0
        assert result["completed_count"] == 0

    def test_revenue_trend_returns_list(self):
        """Revenue trend should return a list of monthly entries."""
        result = RevenueAnalytics.get_revenue_trend(self.academy, months=3)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_revenue_trend_entry_structure(self):
        """Each trend entry should have month, total_cents, display."""
        result = RevenueAnalytics.get_revenue_trend(self.academy, months=3)
        for entry in result:
            assert "month" in entry
            assert "total_cents" in entry
            assert "display" in entry


# ===================================================================
# TestFunnelAnalytics — service layer unit-level tests
# ===================================================================


@pytest.mark.integration
class TestFunnelAnalytics(TestCase):
    """Test FunnelAnalytics service methods."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Funnel Analytics Academy",
            slug="funnel-analytics-academy",
            description="A test academy",
            email="funnel-analytics@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="funnel-analytics-owner",
            email="funnel-analytics-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def test_funnel_structure(self):
        """Funnel should return expected dict keys."""
        result = FunnelAnalytics.get_funnel(self.academy)
        assert "members_joined" in result
        assert "enrolled" in result
        assert "started_learning" in result
        assert "retained_30d" in result
        assert "join_to_enroll_rate" in result
        assert "enroll_to_learn_rate" in result
        assert "learn_to_retain_rate" in result
        assert "period_days" in result

    def test_funnel_empty_academy(self):
        """Empty academy should have all zeros."""
        result = FunnelAnalytics.get_funnel(self.academy)
        assert result["members_joined"] == 0
        assert result["enrolled"] == 0

    def test_funnel_respects_period(self):
        """Funnel period_days should match requested days."""
        result = FunnelAnalytics.get_funnel(self.academy, days=7)
        assert result["period_days"] == 7

    def test_enrollment_breakdown_structure(self):
        """Enrollment breakdown should have status keys."""
        result = FunnelAnalytics.get_enrollment_breakdown(self.academy)
        assert "active" in result
        assert "completed" in result
        assert "dropped" in result
        assert "paused" in result
        assert "total" in result

    def test_enrollment_breakdown_total_is_sum(self):
        """Total should equal sum of all statuses."""
        result = FunnelAnalytics.get_enrollment_breakdown(self.academy)
        expected = (
            result["active"]
            + result["completed"]
            + result["dropped"]
            + result["paused"]
        )
        assert result["total"] == expected


# ===================================================================
# TestLearningAnalytics — service layer unit-level tests
# ===================================================================


@pytest.mark.integration
class TestLearningAnalytics(TestCase):
    """Test LearningAnalytics service methods."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Learning Analytics Academy",
            slug="learning-analytics-academy",
            description="A test academy",
            email="learning-analytics@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="learning-analytics-owner",
            email="learning-analytics-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def test_metrics_structure(self):
        """Learning metrics should return expected dict keys."""
        result = LearningAnalytics.get_metrics(self.academy)
        assert "avg_progress" in result
        assert "completion_rate" in result
        assert "total_reviewed" in result
        assert "attendance_rate" in result
        assert "no_show_rate" in result
        assert "total_sessions_completed" in result

    def test_metrics_empty_academy(self):
        """Empty academy should have zero metrics."""
        result = LearningAnalytics.get_metrics(self.academy)
        assert result["avg_progress"] == 0
        assert result["completion_rate"] == 0
        assert result["attendance_rate"] == 0


# ===================================================================
# TestPriorityCTA — priority CTA on admin dashboard
# ===================================================================


@pytest.mark.integration
class TestPriorityCTA(TestCase):
    """Test priority CTA logic on admin dashboard."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Priority CTA Academy",
            slug="priority-cta-academy",
            description="A test academy",
            email="priority-cta@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="priority-cta-owner",
            email="priority-cta-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="priority-cta-instructor",
            email="priority-cta-instructor@test.com",
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

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="priority-cta-owner@test.com", password="testpass123"
        )

    def test_no_cta_for_healthy_academy(self):
        """Healthy academy should not show priority CTA."""
        url = reverse("admin-dashboard")
        response = self.auth_client.get(url)
        assert response.context["priority_cta"] is None

    def test_overdue_reviews_trigger_cta(self):
        """Overdue assignment reviews should trigger student risk CTA."""
        from apps.courses.models import Course, Lesson, PracticeAssignment
        from apps.enrollments.models import AssignmentSubmission

        course = Course.objects.create(
            academy=self.academy,
            title="Test Course",
            slug="test-course-cta",
            instructor=self.instructor,
        )
        lesson = Lesson.objects.create(
            course=course,
            academy=self.academy,
            title="Lesson 1",
            content="Content",
            order=1,
        )
        assignment = PracticeAssignment.objects.create(
            lesson=lesson,
            academy=self.academy,
            title="HW1",
            assignment_type="practice",
            due_date=timezone.now() + timedelta(days=7),
        )

        student = UserFactory(email="cta-student@test.com")
        Membership.objects.create(user=student, academy=self.academy, role="student")

        sub = AssignmentSubmission.objects.create(
            academy=self.academy,
            assignment=assignment,
            student=student,
            status="submitted",
        )
        # Backdate to >48h ago
        AssignmentSubmission.objects.filter(pk=sub.pk).update(
            created_at=timezone.now() - timedelta(hours=50)
        )

        url = reverse("admin-dashboard")
        response = self.auth_client.get(url)
        cta = response.context["priority_cta"]
        assert cta is not None
        assert cta["type"] == "student"
        assert "submission" in cta["message"].lower()


# ===================================================================
# TestAnalyticsButtonOnDashboard — button exists and links correctly
# ===================================================================


@pytest.mark.integration
class TestAnalyticsButtonOnDashboard(TestCase):
    """Test Analytics button appears on admin dashboard."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Analytics Button Academy",
            slug="analytics-button-academy",
            description="A test academy",
            email="analytics-button@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="analytics-button-owner",
            email="analytics-button-owner@test.com",
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
            username="analytics-button-owner@test.com", password="testpass123"
        )

    def test_analytics_button_present(self):
        """Admin dashboard should have an Analytics button."""
        url = reverse("admin-dashboard")
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert reverse("owner-analytics") in content
        assert "Analytics" in content
