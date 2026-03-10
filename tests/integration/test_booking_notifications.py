"""Tests for booking/rescheduling notifications and reschedule limits.

Covers:
- Booking creates notifications for instructor + student
- Notification type and link correctness
- No duplicate notifications
- Reschedule notifications to attendees, instructor, and actor
- Reschedule self-notification suppression
- Reschedule limit enforcement (unlimited default, limit blocks, monthly reset)
- Reschedule limit applies only to students
- Remaining count shown on student reschedule page
"""

import datetime

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.academies.models import Academy
from apps.accounts.models import User, Membership
from apps.notifications.models import Notification
from apps.scheduling.models import LiveSession, SessionAttendance, InstructorAvailability


def _next_weekday(day_of_week):
    """Return the next date matching the given Python weekday (Mon=0 ... Sun=6)."""
    today = datetime.date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


def _reschedule_data(hours_from_now=48):
    """Helper to generate valid reschedule POST data for instructor/owner."""
    new_start = timezone.now() + datetime.timedelta(hours=hours_from_now)
    new_end = new_start + datetime.timedelta(hours=1)
    return {
        "new_start": new_start.strftime("%Y-%m-%dT%H:%M"),
        "new_end": new_end.strftime("%Y-%m-%dT%H:%M"),
        "reason": "Schedule conflict",
    }


@pytest.mark.integration
class TestBookingNotifications(TestCase):
    """Tests for notifications created when a session is booked."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Booking Notif Academy",
            slug="booking-notif-acad",
            description="For booking notification tests",
            email="booking-notif@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )

        cls.instructor_user = User.objects.create_user(
            username="bn-instructor",
            email="bn-instructor@test.com",
            password="testpass123",
            first_name="Sarah",
            last_name="Instructor",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user, academy=cls.academy, role="instructor",
            instruments=["Piano"],
        )

        cls.student_user = User.objects.create_user(
            username="bn-student",
            email="bn-student@test.com",
            password="testpass123",
            first_name="Alice",
            last_name="Student",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user, academy=cls.academy, role="student",
            instruments=["Piano"], skill_level="beginner",
        )

        # Instructor availability: Monday 10:00-11:00
        cls.slot = InstructorAvailability.objects.create(
            instructor=cls.instructor_user,
            academy=cls.academy,
            day_of_week=0,  # Monday
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            is_active=True,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="bn-student@test.com", password="testpass123")
        # Clear any notifications from previous tests
        Notification.objects.filter(academy=self.academy).delete()
        # Clean up any sessions created by previous tests
        LiveSession.objects.filter(academy=self.academy).delete()

    def _book_session(self):
        """Helper: book a session and return the response."""
        next_monday = _next_weekday(0)
        data = {
            "instructor": self.instructor_user.pk,
            "slot": self.slot.pk,
            "session_date": next_monday.strftime("%Y-%m-%d"),
        }
        return self.client.post(reverse("book-session"), data)

    def test_booking_notifies_instructor(self):
        """Booking creates a notification for the instructor."""
        self._book_session()
        notifs = Notification.objects.filter(
            recipient=self.instructor_user,
            academy=self.academy,
        )
        assert notifs.count() == 1
        assert "New Session Booked" in notifs.first().title
        assert "Alice Student" in notifs.first().message

    def test_booking_confirms_to_student(self):
        """Booking creates a confirmation notification for the student."""
        self._book_session()
        notifs = Notification.objects.filter(
            recipient=self.student_user,
            academy=self.academy,
        )
        assert notifs.count() == 1
        assert "Booking Confirmed" in notifs.first().title
        assert "Sarah Instructor" in notifs.first().message

    def test_booking_notification_has_link(self):
        """Notification link points to the session detail URL."""
        self._book_session()
        session = LiveSession.objects.filter(academy=self.academy).last()
        expected_link = reverse("session-detail", args=[session.pk])
        notifs = Notification.objects.filter(academy=self.academy)
        for notif in notifs:
            assert notif.link == expected_link

    def test_booking_notification_type(self):
        """Notification type is 'session_booked'."""
        self._book_session()
        notifs = Notification.objects.filter(academy=self.academy)
        for notif in notifs:
            assert notif.notification_type == "session_booked"

    def test_no_duplicate_notifications(self):
        """Booking creates exactly 2 notifications (instructor + student)."""
        self._book_session()
        count = Notification.objects.filter(academy=self.academy).count()
        assert count == 2


@pytest.mark.integration
class TestRescheduleNotifications(TestCase):
    """Tests for notifications created when a session is rescheduled."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Resched Notif Academy",
            slug="resched-notif-acad",
            description="For reschedule notification tests",
            email="resched-notif@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )

        cls.owner_user = User.objects.create_user(
            username="rn-owner",
            email="rn-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner_user.current_academy = cls.academy
        cls.owner_user.save()
        Membership.objects.create(user=cls.owner_user, academy=cls.academy, role="owner")

        cls.instructor_user = User.objects.create_user(
            username="rn-instructor",
            email="rn-instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user, academy=cls.academy, role="instructor",
            instruments=["Piano"],
        )

        cls.student_user = User.objects.create_user(
            username="rn-student",
            email="rn-student@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user, academy=cls.academy, role="student",
        )

        cls.student2_user = User.objects.create_user(
            username="rn-student2",
            email="rn-student2@test.com",
            password="testpass123",
            first_name="Second",
            last_name="Student",
        )
        cls.student2_user.current_academy = cls.academy
        cls.student2_user.save()
        Membership.objects.create(
            user=cls.student2_user, academy=cls.academy, role="student",
        )

        # Instructor availability for student reschedule
        cls.slot = InstructorAvailability.objects.create(
            instructor=cls.instructor_user,
            academy=cls.academy,
            day_of_week=2,  # Wednesday
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            is_active=True,
        )

    def setUp(self):
        # Create a fresh session for each test
        start = timezone.now() + datetime.timedelta(days=3)
        end = start + datetime.timedelta(hours=1)
        self.session = LiveSession.objects.create(
            title="Piano Lesson",
            academy=self.academy,
            instructor=self.instructor_user,
            scheduled_start=start,
            scheduled_end=end,
            duration_minutes=60,
            session_type="one_on_one",
            room_name=f"test-room-rn-{timezone.now().timestamp()}",
            status=LiveSession.SessionStatus.SCHEDULED,
        )
        # Register both students
        SessionAttendance.objects.create(
            session=self.session, student=self.student_user, academy=self.academy,
        )
        SessionAttendance.objects.create(
            session=self.session, student=self.student2_user, academy=self.academy,
        )
        # Clear notifications
        Notification.objects.filter(academy=self.academy).delete()

        self.instructor_client = Client()
        self.instructor_client.login(
            username="rn-instructor@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="rn-student@test.com", password="testpass123"
        )

    def test_instructor_reschedule_notifies_students(self):
        """Instructor rescheduling notifies all attendees (not the instructor)."""
        url = reverse("session-reschedule", args=[self.session.pk])
        data = _reschedule_data()
        self.instructor_client.post(url, data)

        # Both students should get notifications
        student1_notifs = Notification.objects.filter(
            recipient=self.student_user,
            notification_type="session_rescheduled",
            title="Session Rescheduled",
        )
        student2_notifs = Notification.objects.filter(
            recipient=self.student2_user,
            notification_type="session_rescheduled",
            title="Session Rescheduled",
        )
        assert student1_notifs.count() == 1
        assert student2_notifs.count() == 1

    def test_student_reschedule_notifies_instructor(self):
        """Student rescheduling notifies the instructor."""
        # Make it a one_on_one session with only one student for student reschedule
        SessionAttendance.objects.filter(
            session=self.session, student=self.student2_user
        ).delete()

        url = reverse("session-reschedule", args=[self.session.pk])
        next_wed = _next_weekday(2)
        data = {
            "slot": self.slot.pk,
            "session_date": next_wed.strftime("%Y-%m-%d"),
            "reason": "Conflict",
        }
        self.student_client.post(url, data)

        instructor_notifs = Notification.objects.filter(
            recipient=self.instructor_user,
            notification_type="session_rescheduled",
            title="Session Rescheduled",
        )
        assert instructor_notifs.count() == 1
        assert "Test Student" in instructor_notifs.first().message

    def test_reschedule_confirms_to_actor(self):
        """The person who rescheduled gets a confirmation notification."""
        url = reverse("session-reschedule", args=[self.session.pk])
        data = _reschedule_data()
        self.instructor_client.post(url, data)

        confirm_notifs = Notification.objects.filter(
            recipient=self.instructor_user,
            notification_type="session_rescheduled",
            title="Reschedule Confirmed",
        )
        assert confirm_notifs.count() == 1

    def test_reschedule_does_not_self_notify(self):
        """Instructor rescheduling doesn't get 'Session Rescheduled' (only confirmation)."""
        url = reverse("session-reschedule", args=[self.session.pk])
        data = _reschedule_data()
        self.instructor_client.post(url, data)

        # Instructor should NOT get a "Session Rescheduled" notification
        rescheduled_notifs = Notification.objects.filter(
            recipient=self.instructor_user,
            notification_type="session_rescheduled",
            title="Session Rescheduled",
        )
        assert rescheduled_notifs.count() == 0

        # But should get "Reschedule Confirmed"
        confirm_notifs = Notification.objects.filter(
            recipient=self.instructor_user,
            notification_type="session_rescheduled",
            title="Reschedule Confirmed",
        )
        assert confirm_notifs.count() == 1


@pytest.mark.integration
class TestRescheduleLimit(TestCase):
    """Tests for per-academy reschedule limit enforcement."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Resched Limit Academy",
            slug="resched-limit-acad",
            description="For reschedule limit tests",
            email="resched-limit@academy.com",
            timezone="UTC",
            primary_instruments=["Guitar"],
            genres=["Rock"],
        )

        cls.owner_user = User.objects.create_user(
            username="rl-owner",
            email="rl-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner_user.current_academy = cls.academy
        cls.owner_user.save()
        Membership.objects.create(user=cls.owner_user, academy=cls.academy, role="owner")

        cls.instructor_user = User.objects.create_user(
            username="rl-instructor",
            email="rl-instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user, academy=cls.academy, role="instructor",
            instruments=["Guitar"],
        )

        cls.student_user = User.objects.create_user(
            username="rl-student",
            email="rl-student@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user, academy=cls.academy, role="student",
        )

        # Instructor availability: Wednesday 14:00-15:00
        cls.slot = InstructorAvailability.objects.create(
            instructor=cls.instructor_user,
            academy=cls.academy,
            day_of_week=2,  # Wednesday
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            is_active=True,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="rl-student@test.com", password="testpass123"
        )
        self.instructor_client = Client()
        self.instructor_client.login(
            username="rl-instructor@test.com", password="testpass123"
        )
        self.owner_client = Client()
        self.owner_client.login(
            username="rl-owner@test.com", password="testpass123"
        )
        # Clean up sessions and reset academy features
        LiveSession.objects.filter(academy=self.academy).delete()
        Academy.objects.filter(pk=self.academy.pk).update(features={})

    def _create_session(self):
        """Create a fresh session with the student registered."""
        start = timezone.now() + datetime.timedelta(days=5)
        end = start + datetime.timedelta(hours=1)
        session = LiveSession.objects.create(
            title="Guitar Lesson",
            academy=self.academy,
            instructor=self.instructor_user,
            scheduled_start=start,
            scheduled_end=end,
            duration_minutes=60,
            session_type="one_on_one",
            room_name=f"test-room-rl-{timezone.now().timestamp()}-{LiveSession.objects.count()}",
            status=LiveSession.SessionStatus.SCHEDULED,
        )
        SessionAttendance.objects.create(
            session=session, student=self.student_user, academy=self.academy,
        )
        return session

    def _reschedule_as_student(self, session):
        """Reschedule the given session as a student using slot-based flow."""
        url = reverse("session-reschedule", args=[session.pk])
        next_wed = _next_weekday(2)
        data = {
            "slot": self.slot.pk,
            "session_date": next_wed.strftime("%Y-%m-%d"),
            "reason": "Conflict",
        }
        return self.student_client.post(url, data)

    def test_unlimited_by_default(self):
        """No limit when reschedule_limit_per_month is not set (default 0 = unlimited)."""
        session = self._create_session()
        url = reverse("session-reschedule", args=[session.pk])
        response = self.student_client.get(url)
        assert response.status_code == 200
        # No "remaining" text since unlimited
        assert b"reschedule" in response.content.lower()
        assert b"remaining" not in response.content.lower()

    def test_limit_blocks_after_max(self):
        """Student is blocked after reaching the reschedule limit."""
        # Set limit to 1
        Academy.objects.filter(pk=self.academy.pk).update(
            features={"reschedule_limit_per_month": 1}
        )

        # First reschedule: should succeed
        session1 = self._create_session()
        response = self._reschedule_as_student(session1)
        assert response.status_code == 302  # Redirect to new session

        # Second reschedule: should be blocked
        session2 = self._create_session()
        url = reverse("session-reschedule", args=[session2.pk])
        response = self.student_client.get(url)
        # Should redirect back to session detail with error
        assert response.status_code == 302
        assert reverse("session-detail", args=[session2.pk]) in response.url

    @freeze_time("2026-02-15 12:00:00")
    def test_limit_resets_monthly(self):
        """Reschedules from last month don't count toward this month's limit."""
        # Set limit to 1
        Academy.objects.filter(pk=self.academy.pk).update(
            features={"reschedule_limit_per_month": 1}
        )

        # Create a session that looks like it was rescheduled last month
        last_month_start = timezone.now() - datetime.timedelta(days=30)
        old_session = LiveSession.objects.create(
            title="Last Month Session",
            academy=self.academy,
            instructor=self.instructor_user,
            scheduled_start=last_month_start,
            scheduled_end=last_month_start + datetime.timedelta(hours=1),
            duration_minutes=60,
            session_type="one_on_one",
            room_name="test-room-rl-lastmonth",
            status=LiveSession.SessionStatus.RESCHEDULED,
        )
        # The rescheduled-to session was created last month
        rescheduled_session = LiveSession.objects.create(
            title="Last Month Session",
            academy=self.academy,
            instructor=self.instructor_user,
            scheduled_start=last_month_start + datetime.timedelta(days=7),
            scheduled_end=last_month_start + datetime.timedelta(days=7, hours=1),
            duration_minutes=60,
            session_type="one_on_one",
            room_name="test-room-rl-lastmonth-new",
            status=LiveSession.SessionStatus.SCHEDULED,
            rescheduled_from=old_session,
        )
        # Attendance is on the new session (transferred during reschedule)
        SessionAttendance.objects.create(
            session=rescheduled_session, student=self.student_user, academy=self.academy,
        )
        # Manually backdate the created_at to last month
        LiveSession.objects.filter(pk=rescheduled_session.pk).update(
            created_at=last_month_start
        )

        # Now this month, student should still be able to reschedule
        session = self._create_session()
        url = reverse("session-reschedule", args=[session.pk])
        response = self.student_client.get(url)
        assert response.status_code == 200  # Not blocked

    def test_limit_only_affects_students(self):
        """Instructors and owners are not subject to the reschedule limit."""
        # Set limit to 1
        Academy.objects.filter(pk=self.academy.pk).update(
            features={"reschedule_limit_per_month": 1}
        )

        # First reschedule by student (uses up the limit)
        session1 = self._create_session()
        self._reschedule_as_student(session1)

        # Instructor reschedule: should NOT be blocked
        session2 = self._create_session()
        url = reverse("session-reschedule", args=[session2.pk])
        data = _reschedule_data(hours_from_now=72)
        response = self.instructor_client.post(url, data)
        assert response.status_code == 302  # Success redirect

        # Owner reschedule: should NOT be blocked
        session3 = self._create_session()
        url = reverse("session-reschedule", args=[session3.pk])
        data = _reschedule_data(hours_from_now=96)
        response = self.owner_client.post(url, data)
        assert response.status_code == 302  # Success redirect

    def test_remaining_count_shown(self):
        """Student reschedule page shows the remaining reschedule count."""
        # Set limit to 3
        Academy.objects.filter(pk=self.academy.pk).update(
            features={"reschedule_limit_per_month": 3}
        )

        session = self._create_session()
        url = reverse("session-reschedule", args=[session.pk])
        response = self.student_client.get(url)
        content = response.content.decode()
        assert response.status_code == 200
        assert "3" in content
        assert "remaining" in content.lower()
