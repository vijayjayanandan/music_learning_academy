import uuid
from datetime import timedelta

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Invitation, Membership, User
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson, PracticeAssignment
from apps.enrollments.models import AssignmentSubmission
from apps.scheduling.livekit_service import generate_room_name
from apps.scheduling.models import LiveSession


@pytest.mark.integration
class TestAdminDashboardAlerts(TestCase):
    """Test dashboard alerts separation from metrics."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Alerts Test Academy",
            slug="alerts-academy-iso",
            description="Academy for dashboard alert tests",
            email="alerts-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-alerts-iso",
            email="owner-alerts-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="instructor-alerts-iso",
            email="instructor-alerts-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor",
            instruments=["Piano"],
        )

        cls.student = User.objects.create_user(
            username="student-alerts-iso",
            email="student-alerts-iso@test.com",
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
        self.auth_client.login(username="owner-alerts-iso@test.com", password="testpass123")
        self.student_client = Client()
        self.student_client.login(username="student-alerts-iso@test.com", password="testpass123")

    def test_no_alerts_when_nothing_pending(self):
        """Dashboard shows no alerts section when everything is clear."""
        response = self.auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200
        assert len(response.context.get("alerts", [])) == 0

    def test_overdue_submission_alert(self):
        """Submissions waiting >48h trigger an alert."""
        course = Course.objects.create(
            title="Test Course",
            academy=self.academy,
            instructor=self.instructor,
            slug="test-course-alerts-overdue",
            description="A test course for alerts",
        )
        lesson = Lesson.objects.create(
            title="Lesson 1", course=course, order=1, academy=self.academy,
        )
        assignment = PracticeAssignment.objects.create(
            lesson=lesson,
            title="Practice",
            description="Practice assignment",
            academy=self.academy,
        )
        sub = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=self.student,
            academy=self.academy,
            status="submitted",
        )
        # Backdate the submission to >48h ago using created_at
        AssignmentSubmission.objects.filter(pk=sub.pk).update(
            created_at=timezone.now() - timedelta(hours=50),
        )

        response = self.auth_client.get(reverse("admin-dashboard"))
        alerts = response.context.get("alerts", [])
        assert any("overdue" in a["title"] for a in alerts)

    def test_session_starting_soon_alert(self):
        """Session starting within 1 hour triggers alert."""
        LiveSession.objects.create(
            title="Soon Session",
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=timezone.now() + timedelta(minutes=30),
            scheduled_end=timezone.now() + timedelta(minutes=90),
            room_name=generate_room_name(self.academy.slug, 8888),
        )

        response = self.auth_client.get(reverse("admin-dashboard"))
        alerts = response.context.get("alerts", [])
        assert any("starting soon" in a["title"] for a in alerts)

    def test_cancelled_session_alert(self):
        """Cancelled session today triggers alert."""
        LiveSession.objects.create(
            title="Cancelled Session",
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=timezone.now() + timedelta(hours=2),
            scheduled_end=timezone.now() + timedelta(hours=3),
            status="cancelled",
            room_name=generate_room_name(self.academy.slug, 7777),
        )

        response = self.auth_client.get(reverse("admin-dashboard"))
        alerts = response.context.get("alerts", [])
        assert any("cancelled" in a["title"] for a in alerts)

    def test_pending_invitation_alert(self):
        """Pending invitations trigger an alert."""
        Invitation.objects.create(
            academy=self.academy,
            email="newinstructor-alerts@test.com",
            role="instructor",
            token=uuid.uuid4().hex,
            invited_by=self.owner,
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.auth_client.get(reverse("admin-dashboard"))
        alerts = response.context.get("alerts", [])
        assert any("invitation" in a["title"] for a in alerts)

    def test_alerts_sorted_by_priority(self):
        """Multiple alerts should be sorted by priority (lower = more urgent)."""
        # Create a soon session (priority 3) and a pending invite (priority 5)
        LiveSession.objects.create(
            title="Soon Session",
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=timezone.now() + timedelta(minutes=30),
            scheduled_end=timezone.now() + timedelta(minutes=90),
            room_name=generate_room_name(self.academy.slug, 6666),
        )
        Invitation.objects.create(
            academy=self.academy,
            email="another-alerts@test.com",
            role="student",
            token=uuid.uuid4().hex,
            invited_by=self.owner,
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.auth_client.get(reverse("admin-dashboard"))
        alerts = response.context.get("alerts", [])
        assert len(alerts) >= 2
        # First alert should have lower/equal priority number than second
        assert alerts[0]["priority"] <= alerts[1]["priority"]

    def test_student_cannot_see_admin_dashboard(self):
        """Students should be redirected away from admin dashboard."""
        response = self.student_client.get(reverse("admin-dashboard"))
        assert response.status_code == 302  # Redirected

    def test_alerts_section_not_shown_when_empty(self):
        """When no alerts, the 'Needs Attention' section should not appear."""
        response = self.auth_client.get(reverse("admin-dashboard"))
        content = response.content.decode()
        assert "Needs Attention" not in content

    def test_expired_invitation_not_counted(self):
        """Expired invitations should NOT trigger an alert."""
        Invitation.objects.create(
            academy=self.academy,
            email="expired-alerts@test.com",
            role="student",
            token=uuid.uuid4().hex,
            invited_by=self.owner,
            expires_at=timezone.now() - timedelta(days=1),  # Already expired
        )

        response = self.auth_client.get(reverse("admin-dashboard"))
        alerts = response.context.get("alerts", [])
        assert not any("invitation" in a["title"] for a in alerts)

    def test_accepted_invitation_not_counted(self):
        """Already-accepted invitations should NOT trigger an alert."""
        Invitation.objects.create(
            academy=self.academy,
            email="accepted-alerts@test.com",
            role="student",
            token=uuid.uuid4().hex,
            invited_by=self.owner,
            accepted=True,
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.auth_client.get(reverse("admin-dashboard"))
        alerts = response.context.get("alerts", [])
        assert not any("invitation" in a["title"] for a in alerts)
