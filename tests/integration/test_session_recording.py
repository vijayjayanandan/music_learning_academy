"""Tests for session recording playback and post-session summary on session detail page."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.scheduling.models import LiveSession


def _make_live_session(academy, instructor, **kwargs):
    """Helper to create a LiveSession with required fields."""
    from itertools import count

    defaults = dict(
        title="Test Session",
        session_type="one_on_one",
        scheduled_start=timezone.now() + timezone.timedelta(hours=1),
        scheduled_end=timezone.now() + timezone.timedelta(hours=2),
    )
    defaults.update(kwargs)
    # room_name must be unique — derive from title + a counter suffix
    if "room_name" not in defaults:
        import uuid
        defaults["room_name"] = f"room-{uuid.uuid4().hex[:8]}"
    return LiveSession.objects.create(academy=academy, instructor=instructor, **defaults)


@pytest.mark.integration
class TestSessionRecordingPlayback(TestCase):
    """Happy-path tests for recording display on completed sessions."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Recording Playback Academy",
            slug="rec-playback-iso",
            description="A test academy",
            email="rec-playback-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rec-playback",
            email="owner-rec-playback@test.com",
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
            username="owner-rec-playback@test.com", password="testpass123"
        )

    def test_completed_session_with_recording_shows_video_player(self):
        """When a completed session has a recording_url, show an HTML5 video player."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="completed",
            recording_url="https://example.com/recordings/session-1.mp4",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Session Recording" in content
        assert '<video controls' in content
        assert "https://example.com/recordings/session-1.mp4" in content

    def test_completed_session_without_recording_shows_processing(self):
        """When a completed session has no recording_url, show a processing indicator."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="completed",
            recording_url="",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Session Recording" in content
        assert "Recording processing..." in content
        assert "loading-spinner" in content
        assert '<video' not in content

    def test_scheduled_session_hides_recording_section(self):
        """Scheduled sessions should not show the recording section at all."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="scheduled",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Session Recording" not in content
        assert "Recording processing..." not in content

    def test_in_progress_session_hides_recording_section(self):
        """In-progress sessions should not show the recording section."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="in_progress",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Session Recording" not in content


@pytest.mark.integration
class TestSessionNotes(TestCase):
    """Tests for session notes display."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Session Notes Academy",
            slug="rec-notes-iso",
            description="A test academy",
            email="rec-notes-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rec-notes",
            email="owner-rec-notes@test.com",
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
            username="owner-rec-notes@test.com", password="testpass123"
        )

    def test_session_notes_displayed_when_present(self):
        """Session notes should be shown in a card when they exist."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="completed",
            session_notes="Great progress on scales today.\nNeed to work on timing.",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Session Notes" in content
        assert "Great progress on scales today." in content
        assert "Need to work on timing." in content

    def test_session_notes_form_shown_for_instructor(self):
        """Session notes form should be shown for instructor/owner even when notes are empty."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="completed",
            session_notes="",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Session Notes" in content
        assert "Save Notes" in content


@pytest.mark.integration
class TestPostSessionLinks(TestCase):
    """Tests for post-session navigation links."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Post Session Links Academy",
            slug="rec-links-iso",
            description="A test academy",
            email="rec-links-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rec-links",
            email="owner-rec-links@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Test Course",
            slug="rec-links-course-iso",
            instructor=cls.owner,
            instrument="Piano",
            difficulty_level="beginner",
            is_published=True,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-rec-links@test.com", password="testpass123"
        )

    def test_completed_session_shows_next_steps(self):
        """Completed sessions should show the Next Steps section with links."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="completed",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Next Steps" in content
        assert "Log Practice" in content
        assert "View All Sessions" in content
        assert reverse("practice-log-create") in content
        assert reverse("schedule-list") in content

    def test_completed_session_with_course_shows_continue_learning(self):
        """Completed sessions linked to a course show a Continue Learning button."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="completed",
            course=self.course,
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Continue Learning" in content
        assert reverse("course-detail", args=[self.course.slug]) in content

    def test_completed_session_without_course_hides_continue_learning(self):
        """Completed sessions without a linked course should not show Continue Learning."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="completed",
            course=None,
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Continue Learning" not in content

    def test_scheduled_session_hides_next_steps(self):
        """Scheduled sessions should not show the Next Steps section."""
        session = _make_live_session(
            self.academy,
            self.owner,
            status="scheduled",
        )
        url = reverse("session-detail", args=[session.pk])
        response = self.auth_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Next Steps" not in content


@pytest.mark.integration
class TestSessionDetailPermissions(TestCase):
    """Permission boundary tests for session detail page."""

    @classmethod
    def setUpTestData(cls):
        # Primary academy + owner
        cls.academy = Academy.objects.create(
            name="Permissions Academy",
            slug="rec-perms-iso",
            description="A test academy",
            email="rec-perms-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-rec-perms",
            email="owner-rec-perms@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        # A separate academy whose sessions the primary owner must NOT access
        cls.other_academy = Academy.objects.create(
            name="Other Permissions Academy",
            slug="rec-perms-other-iso",
            description="Another academy",
            email="rec-perms-other-iso@academy.com",
            timezone="UTC",
        )
        cls.other_owner = User.objects.create_user(
            username="owner-rec-perms-other",
            email="owner-rec-perms-other@test.com",
            password="testpass123",
            first_name="Other",
            last_name="Owner",
        )
        cls.other_owner.current_academy = cls.other_academy
        cls.other_owner.save()
        Membership.objects.create(
            user=cls.other_owner, academy=cls.other_academy, role="owner"
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-rec-perms@test.com", password="testpass123"
        )
        self.anon_client = Client()

    def test_unauthenticated_user_redirected(self):
        """Unauthenticated users should be redirected to login."""
        session = _make_live_session(self.academy, self.owner)
        url = reverse("session-detail", args=[session.pk])
        response = self.anon_client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_other_academy_session_not_accessible(self):
        """Users cannot view sessions from a different academy (tenant isolation)."""
        other_session = _make_live_session(
            self.other_academy,
            self.other_owner,
            status="completed",
            recording_url="https://example.com/secret-recording.mp4",
        )
        url = reverse("session-detail", args=[other_session.pk])
        response = self.auth_client.get(url)

        # TenantMixin should return 404 for sessions in other academies
        assert response.status_code == 404
