"""Tests for session model enhancements, capacity validation, and double-booking overlap."""

import pytest
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.scheduling.models import LiveSession, SessionAttendance
from apps.scheduling.livekit_service import generate_room_name
from apps.accounts.models import User, Membership
from apps.academies.models import Academy


@pytest.mark.integration
class TestSessionStatusChoices(TestCase):
    """Verify all 8 session status choices exist on the model."""

    def test_session_status_choices_include_new_states(self):
        """All 8 status choices should be defined on LiveSession.SessionStatus."""
        status_values = [choice[0] for choice in LiveSession.SessionStatus.choices]
        assert "scheduled" in status_values
        assert "open_for_join" in status_values
        assert "in_progress" in status_values
        assert "completed" in status_values
        assert "cancelled" in status_values
        assert "rescheduled" in status_values
        assert "no_show_instructor" in status_values
        assert "no_show_student" in status_values
        assert len(status_values) == 8


@pytest.mark.integration
class TestRecordingStatusChoices(TestCase):
    """Verify all 5 recording status choices exist."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Recording Status Academy",
            slug="sess-recstatus-iso",
            description="A test academy",
            email="recstatus-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-recstatus-iso",
            email="instructor-recstatus-iso@test.com",
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

    def test_recording_status_choices(self):
        """All 5 recording status choices should be defined."""
        status_values = [choice[0] for choice in LiveSession.RecordingStatus.choices]
        assert "not_requested" in status_values
        assert "recording" in status_values
        assert "processing" in status_values
        assert "available" in status_values
        assert "failed" in status_values
        assert len(status_values) == 5

    def test_default_recording_status(self):
        """New sessions should default to 'not_requested' recording status."""
        session = LiveSession.objects.create(
            title="Test Session",
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            max_participants=5,
            room_name=generate_room_name(self.academy.slug, 888),
        )
        assert session.recording_status == "not_requested"


@pytest.mark.integration
class TestCapacityValidation(TestCase):
    """Tests for session registration capacity enforcement."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Capacity Validation Academy",
            slug="sess-capacity-iso",
            description="A test academy",
            email="capacity-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-capacity-iso",
            email="instructor-capacity-iso@test.com",
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
            username="student-capacity-iso",
            email="student-capacity-iso@test.com",
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

    def setUp(self):
        """Fresh client for each test."""
        self.client = Client()

    def _create_session(self, max_participants=1, room_suffix=999):
        return LiveSession.objects.create(
            title="Test Session",
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            max_participants=max_participants,
            room_name=generate_room_name(self.academy.slug, room_suffix),
        )

    def _create_student(self, username, email):
        user = User.objects.create_user(
            username=username,
            email=email,
            password="testpass123",
        )
        user.current_academy = self.academy
        user.save()
        Membership.objects.create(user=user, academy=self.academy, role="student")
        return user

    def test_register_blocked_when_session_full(self):
        """When max_participants=1 and 1 student is registered, another student cannot register."""
        session = self._create_session(max_participants=1, room_suffix=999)

        # Register first student
        student2 = self._create_student("student2-cap-iso", "student2-cap-iso@test.com")
        SessionAttendance.objects.create(
            session=session,
            student=student2,
            academy=self.academy,
        )

        # Try to register second student (self.student)
        self.client.login(
            username="student-capacity-iso@test.com", password="testpass123"
        )
        url = reverse("session-register", args=[session.pk])
        response = self.client.post(url)

        # Should redirect with error (session full)
        assert response.status_code == 302
        # Verify attendance was NOT created for self.student
        assert not SessionAttendance.objects.filter(
            session=session, student=self.student
        ).exists()

    def test_register_allowed_when_capacity_available(self):
        """When max_participants=2 and 1 is registered, second registration succeeds."""
        session = self._create_session(max_participants=2, room_suffix=998)

        # Register first student
        student2 = self._create_student(
            "student2b-cap-iso", "student2b-cap-iso@test.com"
        )
        SessionAttendance.objects.create(
            session=session,
            student=student2,
            academy=self.academy,
        )

        # Register second student (should succeed)
        self.client.login(
            username="student-capacity-iso@test.com", password="testpass123"
        )
        url = reverse("session-register", args=[session.pk])
        response = self.client.post(url)

        assert response.status_code == 302
        assert SessionAttendance.objects.filter(
            session=session, student=self.student
        ).exists()

    def test_register_unlimited_when_max_zero(self):
        """When max_participants=0 (unlimited), registration always succeeds."""
        session = self._create_session(max_participants=0, room_suffix=997)

        # Register 3 extra students
        for i in range(3):
            s = self._create_student(
                f"unlim-cap-iso-{i}", f"unlim-cap-iso-{i}@test.com"
            )
            SessionAttendance.objects.create(
                session=session, student=s, academy=self.academy
            )

        # 4th student (self.student) should still be able to register
        self.client.login(
            username="student-capacity-iso@test.com", password="testpass123"
        )
        url = reverse("session-register", args=[session.pk])
        response = self.client.post(url)

        assert response.status_code == 302
        assert SessionAttendance.objects.filter(
            session=session, student=self.student
        ).exists()

    def test_capacity_check_excludes_instructor(self):
        """Instructor joining via JoinSessionView doesn't count against max_participants.

        The instructor uses JoinSessionView (not RegisterForSessionView), so they
        don't create an attendance record. Only student registrations count.
        """
        session = self._create_session(max_participants=1, room_suffix=996)

        # Register self.student
        self.client.login(
            username="student-capacity-iso@test.com", password="testpass123"
        )
        url = reverse("session-register", args=[session.pk])
        response = self.client.post(url)

        assert response.status_code == 302
        assert SessionAttendance.objects.filter(
            session=session, student=self.student
        ).exists()
        # Only 1 attendance (the student), not the instructor
        assert session.attendances.count() == 1


@pytest.mark.integration
class TestDoubleBookingOverlap(TestCase):
    """Tests for double-booking overlap detection."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Double Booking Academy",
            slug="sess-doublebooking-iso",
            description="A test academy",
            email="doublebooking-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-doublebooking-iso",
            email="owner-doublebooking-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        """Fresh authenticated client for each test."""
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-doublebooking-iso@test.com", password="testpass123"
        )

    def _create_session(self, start_offset_hours, end_offset_hours, room_suffix):
        return LiveSession.objects.create(
            title="Test Session",
            academy=self.academy,
            instructor=self.owner,
            scheduled_start=timezone.now() + timedelta(hours=start_offset_hours),
            scheduled_end=timezone.now() + timedelta(hours=end_offset_hours),
            max_participants=5,
            room_name=generate_room_name(self.academy.slug, room_suffix),
            status="scheduled",
        )

    def test_double_booking_overlap_blocked(self):
        """Creating a session that overlaps with an existing one should be blocked via SessionCreateView."""
        # Existing session from 2-3 hours from now
        self._create_session(2, 3, room_suffix=100)

        # Try to create session from 2:30-3:30 (overlaps)
        url = reverse("session-create")
        start = timezone.now() + timedelta(hours=2, minutes=30)
        end = timezone.now() + timedelta(hours=3, minutes=30)
        data = {
            "title": "Overlapping Session",
            "scheduled_start": start.strftime("%Y-%m-%dT%H:%M"),
            "scheduled_end": end.strftime("%Y-%m-%dT%H:%M"),
            "session_type": "one_on_one",
            "max_participants": 1,
            "duration_minutes": 60,
        }
        response = self.auth_client.post(url, data)

        # Should return form with error (not redirect)
        assert response.status_code == 200
        content = response.content.decode()
        assert "overlaps" in content.lower()

    def test_non_overlapping_sessions_allowed(self):
        """Creating a session that does NOT overlap should succeed."""
        # Existing session from 2-3 hours from now
        self._create_session(2, 3, room_suffix=200)

        # Create session starting well after existing ends (4-5 hours, clear gap)
        url = reverse("session-create")
        start = timezone.now() + timedelta(hours=4)
        end = timezone.now() + timedelta(hours=5)
        data = {
            "title": "Non-Overlapping Session",
            "scheduled_start": start.strftime("%Y-%m-%dT%H:%M"),
            "scheduled_end": end.strftime("%Y-%m-%dT%H:%M"),
            "session_type": "one_on_one",
            "max_participants": 1,
            "duration_minutes": 60,
        }
        response = self.auth_client.post(url, data)

        # Should redirect (session created successfully)
        assert response.status_code == 302

    def test_session_create_double_booking_overlap(self):
        """SessionCreateView.form_valid returns form error when time overlaps."""
        # Create existing session from 5-6 hours from now
        self._create_session(5, 6, room_suffix=300)

        # Try to create session from 5:15-5:45 (fully inside existing)
        url = reverse("session-create")
        start = timezone.now() + timedelta(hours=5, minutes=15)
        end = timezone.now() + timedelta(hours=5, minutes=45)
        data = {
            "title": "Inside Overlap Session",
            "scheduled_start": start.strftime("%Y-%m-%dT%H:%M"),
            "scheduled_end": end.strftime("%Y-%m-%dT%H:%M"),
            "session_type": "group",
            "max_participants": 5,
            "duration_minutes": 30,
        }
        response = self.auth_client.post(url, data)

        assert response.status_code == 200
        content = response.content.decode()
        assert "overlaps" in content.lower()


@pytest.mark.integration
class TestRecordingStatusViews(TestCase):
    """Tests for recording views setting recording_status field."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Recording Views Academy",
            slug="sess-recviews-iso",
            description="A test academy",
            email="recviews-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-recviews-iso",
            email="instructor-recviews-iso@test.com",
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
        """Fresh client for each test."""
        self.client = Client()

    def _create_session(self, room_suffix=500):
        return LiveSession.objects.create(
            title="Recording Test Session",
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            max_participants=5,
            room_name=generate_room_name(self.academy.slug, room_suffix),
            status="in_progress",
        )

    @patch("apps.scheduling.views.async_to_sync")
    def test_start_recording_sets_recording_status(self, mock_async_to_sync):
        """StartRecordingView should set recording_status to 'recording' on success."""
        mock_async_to_sync.return_value = lambda *a, **kw: "test-egress-id"
        session = self._create_session(room_suffix=501)

        self.client.login(
            username="instructor-recviews-iso@test.com", password="testpass123"
        )
        url = reverse("session-start-recording", args=[session.pk])
        response = self.client.post(url)

        assert response.status_code == 200
        session.refresh_from_db()
        assert session.recording_status == "recording"

    @patch("apps.scheduling.views.async_to_sync")
    def test_stop_recording_sets_processing_status(self, mock_async_to_sync):
        """StopRecordingView should set recording_status to 'processing' on success."""
        mock_async_to_sync.return_value = lambda *a, **kw: None
        session = self._create_session(room_suffix=502)
        session.recording_status = "recording"
        session.save()

        # Set the egress cache key so stop recording finds it
        from django.core.cache import cache

        cache.set(f"egress_{session.pk}", "test-egress-id", timeout=7200)

        self.client.login(
            username="instructor-recviews-iso@test.com", password="testpass123"
        )
        url = reverse("session-stop-recording", args=[session.pk])
        response = self.client.post(url)

        assert response.status_code == 200
        session.refresh_from_db()
        assert session.recording_status == "processing"

    @patch("apps.scheduling.views.async_to_sync")
    def test_start_recording_sets_failed_on_error(self, mock_async_to_sync):
        """StartRecordingView should set recording_status to 'failed' on exception."""
        mock_async_to_sync.return_value = lambda *a, **kw: (_ for _ in ()).throw(
            Exception("LiveKit error")
        )
        session = self._create_session(room_suffix=503)

        self.client.login(
            username="instructor-recviews-iso@test.com", password="testpass123"
        )
        url = reverse("session-start-recording", args=[session.pk])
        response = self.client.post(url)

        assert response.status_code == 500
        session.refresh_from_db()
        assert session.recording_status == "failed"
