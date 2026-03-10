"""Tests for the session reschedule workflow."""

import pytest
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.scheduling.models import (
    LiveSession,
    SessionAttendance,
    InstructorAvailability,
)


def _reschedule_data(hours_from_now=48):
    """Helper to generate valid reschedule POST data."""
    new_start = timezone.now() + timedelta(hours=hours_from_now)
    new_end = new_start + timedelta(hours=1)
    return {
        "new_start": new_start.strftime("%Y-%m-%dT%H:%M"),
        "new_end": new_end.strftime("%Y-%m-%dT%H:%M"),
        "reason": "Instructor conflict",
    }


@pytest.mark.integration
class TestRescheduleWorkflow(TestCase):
    """
    Uses setUpTestData to create shared DB objects ONCE for all tests.
    Django wraps each test method in a SAVEPOINT so test-specific writes
    are rolled back after each test, while the shared objects (Academy, User,
    LiveSession) persist for the whole class.
    """

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Reschedule Workflow Academy",
            slug="resched-workflow-iso",
            description="Academy for reschedule workflow tests",
            email="resched-workflow@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )

        cls.owner_user = User.objects.create_user(
            username="owner-resched-workflow",
            email="owner-resched-workflow@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner_user.current_academy = cls.academy
        cls.owner_user.save()
        Membership.objects.create(
            user=cls.owner_user, academy=cls.academy, role="owner"
        )

        cls.instructor_user = User.objects.create_user(
            username="instructor-resched-workflow",
            email="instructor-resched-workflow@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user,
            academy=cls.academy,
            role="instructor",
            instruments=["Piano"],
        )

        cls.student_user = User.objects.create_user(
            username="student-resched-workflow",
            email="student-resched-workflow@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user,
            academy=cls.academy,
            role="student",
            instruments=["Piano"],
            skill_level="beginner",
        )

        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=1)
        cls.live_session = LiveSession.objects.create(
            title="Piano Lesson",
            academy=cls.academy,
            instructor=cls.instructor_user,
            scheduled_start=start,
            scheduled_end=end,
            duration_minutes=60,
            session_type="one_on_one",
            room_name="test-room-resched-workflow-1",
            status=LiveSession.SessionStatus.SCHEDULED,
        )

        SessionAttendance.objects.create(
            session=cls.live_session,
            student=cls.student_user,
            academy=cls.academy,
        )

    def setUp(self):
        """Fresh HTTP clients for each test (no session bleed)."""
        self.instructor_client = Client()
        self.instructor_client.login(
            username="instructor-resched-workflow@test.com", password="testpass123"
        )
        self.owner_client = Client()
        self.owner_client.login(
            username="owner-resched-workflow@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-resched-workflow@test.com", password="testpass123"
        )
        # Reset session status to SCHEDULED before each test
        LiveSession.objects.filter(pk=self.live_session.pk).update(
            status=LiveSession.SessionStatus.SCHEDULED
        )
        # Remove any child sessions created by a previous test
        LiveSession.objects.filter(rescheduled_from=self.live_session).delete()

    def test_reschedule_creates_new_session(self):
        """Rescheduling a scheduled session creates a new session and marks old as rescheduled."""
        url = reverse("session-reschedule", args=[self.live_session.pk])
        data = _reschedule_data()
        response = self.instructor_client.post(url, data)

        # Old session should be marked as rescheduled
        self.live_session.refresh_from_db()
        assert self.live_session.status == LiveSession.SessionStatus.RESCHEDULED

        # New session should exist and link back
        new_session = LiveSession.objects.filter(
            rescheduled_from=self.live_session
        ).first()
        assert new_session is not None
        assert new_session.title == self.live_session.title
        assert new_session.instructor == self.live_session.instructor
        assert new_session.academy == self.academy
        assert new_session.status == LiveSession.SessionStatus.SCHEDULED

        # Should redirect to new session detail
        assert response.status_code == 302
        assert str(new_session.pk) in response.url

    def test_reschedule_transfers_registrations(self):
        """Registered students are transferred to the new session."""
        url = reverse("session-reschedule", args=[self.live_session.pk])
        data = _reschedule_data()
        self.instructor_client.post(url, data)

        new_session = LiveSession.objects.filter(
            rescheduled_from=self.live_session
        ).first()
        assert new_session is not None

        # Student should be registered on the new session
        assert SessionAttendance.objects.filter(
            session=new_session, student=self.student_user
        ).exists()

    def test_reschedule_preserves_original_time(self):
        """Original session keeps its original start/end times after rescheduling."""
        original_start = self.live_session.scheduled_start
        original_end = self.live_session.scheduled_end

        url = reverse("session-reschedule", args=[self.live_session.pk])
        data = _reschedule_data()
        self.instructor_client.post(url, data)

        self.live_session.refresh_from_db()
        assert self.live_session.scheduled_start == original_start
        assert self.live_session.scheduled_end == original_end

    def test_reschedule_blocked_for_non_scheduled(self):
        """Cannot reschedule a completed or cancelled session."""
        LiveSession.objects.filter(pk=self.live_session.pk).update(
            status=LiveSession.SessionStatus.COMPLETED
        )

        url = reverse("session-reschedule", args=[self.live_session.pk])
        response = self.instructor_client.get(url)

        # Should redirect back to detail page with an error
        assert response.status_code == 302
        assert reverse("session-detail", args=[self.live_session.pk]) in response.url

    def test_reschedule_overlap_blocked(self):
        """Cannot reschedule to a time that overlaps with another session."""
        # Create a conflicting session
        conflict_start = timezone.now() + timedelta(hours=72)
        conflict_end = conflict_start + timedelta(hours=1)
        LiveSession.objects.create(
            title="Conflicting Session",
            academy=self.academy,
            instructor=self.instructor_user,
            scheduled_start=conflict_start,
            scheduled_end=conflict_end,
            duration_minutes=60,
            session_type="one_on_one",
            room_name="test-room-resched-workflow-conflict",
            status=LiveSession.SessionStatus.SCHEDULED,
        )

        url = reverse("session-reschedule", args=[self.live_session.pk])
        # Try to reschedule to the exact same time as the conflict
        data = {
            "new_start": conflict_start.strftime("%Y-%m-%dT%H:%M"),
            "new_end": conflict_end.strftime("%Y-%m-%dT%H:%M"),
            "reason": "Testing overlap",
        }
        response = self.instructor_client.post(url, data)

        # Should re-render the form with an error, not redirect
        assert response.status_code == 200
        assert b"overlaps" in response.content

        # Original session should still be scheduled (not rescheduled)
        self.live_session.refresh_from_db()
        assert self.live_session.status == LiveSession.SessionStatus.SCHEDULED

    def test_reschedule_permission_instructor_own_only(self):
        """An instructor cannot reschedule another instructor's session."""
        # Create a second instructor
        other_instructor = User.objects.create_user(
            username="instructor2-resched-workflow",
            email="instructor2-resched-workflow@test.com",
            password="testpass123",
            first_name="Other",
            last_name="Instructor",
        )
        other_instructor.current_academy = self.academy
        other_instructor.save()
        Membership.objects.create(
            user=other_instructor, academy=self.academy, role="instructor"
        )

        other_client = Client()
        other_client.login(
            username="instructor2-resched-workflow@test.com", password="testpass123"
        )
        url = reverse("session-reschedule", args=[self.live_session.pk])
        response = other_client.get(url)
        assert response.status_code == 403

    def test_reschedule_permission_owner_any(self):
        """An owner can reschedule any instructor's session."""
        url = reverse("session-reschedule", args=[self.live_session.pk])
        response = self.owner_client.get(url)
        assert response.status_code == 200

        # Also test POST works
        data = _reschedule_data(hours_from_now=96)
        response = self.owner_client.post(url, data)
        assert response.status_code == 302

        self.live_session.refresh_from_db()
        assert self.live_session.status == LiveSession.SessionStatus.RESCHEDULED

    def test_rescheduled_session_shows_banner(self):
        """Session detail of a rescheduled session shows 'was rescheduled' alert."""
        url = reverse("session-reschedule", args=[self.live_session.pk])
        data = _reschedule_data()
        self.instructor_client.post(url, data)

        # View original (rescheduled) session detail
        detail_url = reverse("session-detail", args=[self.live_session.pk])
        response = self.instructor_client.get(detail_url)
        assert response.status_code == 200
        assert b"This session was rescheduled" in response.content

        # View new session detail — should show "rescheduled from" banner
        new_session = LiveSession.objects.filter(
            rescheduled_from=self.live_session
        ).first()
        new_detail_url = reverse("session-detail", args=[new_session.pk])
        response = self.instructor_client.get(new_detail_url)
        assert response.status_code == 200
        assert b"rescheduled from" in response.content

    def test_reschedule_student_cannot_access_group_session(self):
        """A student cannot reschedule group sessions."""
        # Create a group session
        start = timezone.now() + timedelta(days=3)
        group_session = LiveSession.objects.create(
            title="Group Masterclass",
            academy=self.academy,
            instructor=self.instructor_user,
            scheduled_start=start,
            scheduled_end=start + timedelta(hours=1),
            duration_minutes=60,
            session_type="group",
            room_name="test-room-resched-group",
            status=LiveSession.SessionStatus.SCHEDULED,
        )
        SessionAttendance.objects.create(
            session=group_session,
            student=self.student_user,
            academy=self.academy,
        )
        url = reverse("session-reschedule", args=[group_session.pk])
        response = self.student_client.get(url)
        assert response.status_code == 403


def _next_weekday(day_of_week):
    """Return the next date matching the given Python weekday (Mon=0)."""
    import datetime

    today = datetime.date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


@pytest.mark.integration
class TestStudentReschedule(TestCase):
    """Tests for student self-reschedule of one_on_one sessions."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Student Reschedule Academy",
            slug="stu-resched-acad",
            description="For student reschedule tests",
            email="stu-resched@academy.com",
            timezone="UTC",
            primary_instruments=["Guitar"],
            genres=["Rock"],
        )
        cls.instructor_user = User.objects.create_user(
            username="instr-stu-resched",
            email="instr-stu-resched@test.com",
            password="testpass123",
            first_name="Instr",
            last_name="Resched",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user,
            academy=cls.academy,
            role="instructor",
            instruments=["Guitar"],
        )

        cls.student_user = User.objects.create_user(
            username="stu-resched",
            email="stu-resched@test.com",
            password="testpass123",
            first_name="Stu",
            last_name="Resched",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user,
            academy=cls.academy,
            role="student",
        )

        # Instructor availability: e.g., Wednesday 14:00-15:00
        cls.slot = InstructorAvailability.objects.create(
            instructor=cls.instructor_user,
            academy=cls.academy,
            day_of_week=2,  # Wednesday
            start_time="14:00",
            end_time="15:00",
            is_active=True,
        )

        # Existing one_on_one session (far enough in future for 24h notice)
        start = timezone.now() + timedelta(days=5)
        end = start + timedelta(hours=1)
        cls.session = LiveSession.objects.create(
            title="Guitar Lesson",
            academy=cls.academy,
            instructor=cls.instructor_user,
            scheduled_start=start,
            scheduled_end=end,
            duration_minutes=60,
            session_type="one_on_one",
            room_name="test-room-stu-resched-1",
            status=LiveSession.SessionStatus.SCHEDULED,
        )
        SessionAttendance.objects.create(
            session=cls.session,
            student=cls.student_user,
            academy=cls.academy,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="stu-resched@test.com", password="testpass123")
        # Reset session state
        LiveSession.objects.filter(pk=self.session.pk).update(
            status=LiveSession.SessionStatus.SCHEDULED
        )
        LiveSession.objects.filter(rescheduled_from=self.session).delete()

    def test_student_can_access_reschedule_for_own_one_on_one(self):
        """Student can GET reschedule page for their one_on_one session."""
        url = reverse("session-reschedule", args=[self.session.pk])
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Pick a New Time" in response.content

    def test_student_sees_instructor_slots(self):
        """Reschedule page shows the instructor's availability slots."""
        url = reverse("session-reschedule", args=[self.session.pk])
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Wednesday" in response.content

    def test_student_reschedule_creates_new_session(self):
        """Student can reschedule to a new slot + date."""
        url = reverse("session-reschedule", args=[self.session.pk])
        next_wed = _next_weekday(2)  # Wednesday
        data = {
            "slot": self.slot.pk,
            "session_date": next_wed.strftime("%Y-%m-%d"),
            "reason": "Schedule conflict",
        }
        response = self.client.post(url, data)
        assert response.status_code == 302

        # Old session should be rescheduled
        self.session.refresh_from_db()
        assert self.session.status == LiveSession.SessionStatus.RESCHEDULED

        # New session should exist
        new_session = LiveSession.objects.filter(rescheduled_from=self.session).first()
        assert new_session is not None
        assert new_session.title == "Guitar Lesson"
        assert new_session.instructor == self.instructor_user

    def test_student_reschedule_transfers_attendance(self):
        """Student's attendance is transferred to the new session."""
        url = reverse("session-reschedule", args=[self.session.pk])
        next_wed = _next_weekday(2)
        data = {"slot": self.slot.pk, "session_date": next_wed.strftime("%Y-%m-%d")}
        self.client.post(url, data)

        new_session = LiveSession.objects.filter(rescheduled_from=self.session).first()
        assert SessionAttendance.objects.filter(
            session=new_session, student=self.student_user
        ).exists()

    def test_student_reschedule_rejects_wrong_day(self):
        """Student can't pick a date that doesn't match the slot's day of week."""
        url = reverse("session-reschedule", args=[self.session.pk])
        next_thu = _next_weekday(3)  # Thursday, but slot is Wednesday
        data = {"slot": self.slot.pk, "session_date": next_thu.strftime("%Y-%m-%d")}
        response = self.client.post(url, data)
        assert response.status_code == 200
        assert b"Wednesday" in response.content  # Error mentions expected day

    def test_student_reschedule_24h_notice(self):
        """Student can't reschedule within 24 hours of session start."""
        # Move session start to 12 hours from now
        soon_start = timezone.now() + timedelta(hours=12)
        LiveSession.objects.filter(pk=self.session.pk).update(
            scheduled_start=soon_start,
            scheduled_end=soon_start + timedelta(hours=1),
        )
        url = reverse("session-reschedule", args=[self.session.pk])
        response = self.client.get(url)
        # Should redirect back with error (24h notice)
        assert response.status_code == 302

    def test_student_cannot_reschedule_other_students_session(self):
        """Student can't reschedule a session they're not registered for."""
        other_student = User.objects.create_user(
            username="other-stu-resched",
            email="other-stu-resched@test.com",
            password="testpass123",
        )
        other_student.current_academy = self.academy
        other_student.save()
        Membership.objects.create(
            user=other_student,
            academy=self.academy,
            role="student",
        )
        other_client = Client()
        other_client.login(
            username="other-stu-resched@test.com", password="testpass123"
        )

        url = reverse("session-reschedule", args=[self.session.pk])
        response = other_client.get(url)
        assert response.status_code == 403
