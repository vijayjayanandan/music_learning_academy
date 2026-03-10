"""Tests for FEAT-033 through FEAT-042 (Release 4: Music-Specific)."""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.music_tools.models import (
    EarTrainingExercise, EarTrainingScore, RecitalEvent,
    RecitalPerformer, PracticeAnalysis, RecordingArchive,
)
from apps.library.models import LibraryResource
from apps.scheduling.models import LiveSession


@pytest.mark.integration
class TestMetronome(TestCase):
    """FEAT-033: Built-in metronome."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Metronome Academy",
            slug="rel4-metronome-iso",
            description="A test academy",
            email="metronome-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="metronome-owner-iso",
            email="metronome-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="metronome-owner-iso@test.com", password="testpass123")

    def test_metronome_page_loads(self):
        response = self.auth_client.get(reverse("metronome"))
        assert response.status_code == 200
        assert b"Metronome" in response.content
        assert b"AudioContext" in response.content


@pytest.mark.integration
class TestTuner(TestCase):
    """FEAT-034: Built-in tuner."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Tuner Academy",
            slug="rel4-tuner-iso",
            description="A test academy",
            email="tuner-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Guitar"],
            genres=["Rock"],
        )
        cls.owner = User.objects.create_user(
            username="tuner-owner-iso",
            email="tuner-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="tuner-owner-iso@test.com", password="testpass123")

    def test_tuner_page_loads(self):
        response = self.auth_client.get(reverse("tuner"))
        assert response.status_code == 200
        assert b"Tuner" in response.content
        assert b"getUserMedia" in response.content


@pytest.mark.integration
class TestNotationRenderer(TestCase):
    """FEAT-035: Music notation renderer."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Notation Academy",
            slug="rel4-notation-iso",
            description="A test academy",
            email="notation-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Violin"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="notation-owner-iso",
            email="notation-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="notation-owner-iso@test.com", password="testpass123")

    def test_notation_page_loads(self):
        response = self.auth_client.get(reverse("notation-renderer"))
        assert response.status_code == 200
        assert b"ABC" in response.content or b"notation" in response.content.lower()


@pytest.mark.integration
class TestEarTraining(TestCase):
    """FEAT-036: Ear training exercises."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Ear Training Academy",
            slug="rel4-eartraining-iso",
            description="A test academy",
            email="eartraining-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="eartraining-owner-iso",
            email="eartraining-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="eartraining-owner-iso@test.com", password="testpass123")

    def test_ear_training_model(self):
        assert hasattr(EarTrainingExercise, "exercise_type")
        assert hasattr(EarTrainingExercise, "questions")

    def test_ear_training_list_loads(self):
        response = self.auth_client.get(reverse("ear-training-list"))
        assert response.status_code == 200

    def test_ear_training_exercise_play(self):
        exercise = EarTrainingExercise.objects.create(
            title="Intervals Quiz",
            exercise_type="interval",
            academy=self.academy,
            difficulty=2,
            questions=[
                {"question": "What interval is this?", "options": ["3rd", "5th", "octave"], "answer": "5th"},
            ],
        )
        response = self.auth_client.get(reverse("ear-training-play", args=[exercise.pk]))
        assert response.status_code == 200
        assert b"Intervals Quiz" in response.content

    def test_submit_ear_training_score(self):
        exercise = EarTrainingExercise.objects.create(
            title="Chord ID",
            exercise_type="chord",
            academy=self.academy,
            questions=[],
        )
        response = self.auth_client.post(reverse("ear-training-play", args=[exercise.pk]), {
            "score": "8",
            "total_questions": "10",
            "time_taken": "120",
        })
        assert response.status_code == 302
        score = EarTrainingScore.objects.get(student=self.owner, exercise=exercise)
        assert score.score == 8
        assert score.percentage == 80


@pytest.mark.integration
class TestVirtualRecitals(TestCase):
    """FEAT-037: Virtual recital events."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Recital Academy",
            slug="rel4-recital-iso",
            description="A test academy",
            email="recital-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="recital-owner-iso",
            email="recital-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="recital-owner-iso@test.com", password="testpass123")

    def test_recital_model(self):
        assert hasattr(RecitalEvent, "room_name")
        assert hasattr(RecitalEvent, "is_public")

    def test_recital_list_loads(self):
        response = self.auth_client.get(reverse("recital-list"))
        assert response.status_code == 200

    def test_recital_detail(self):
        recital = RecitalEvent.objects.create(
            title="Spring Recital",
            academy=self.academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=2),
            room_name="spring-recital-room",
        )
        response = self.auth_client.get(reverse("recital-detail", args=[recital.pk]))
        assert response.status_code == 200
        assert b"Spring Recital" in response.content

    def test_recital_create_page(self):
        response = self.auth_client.get(reverse("recital-create"))
        assert response.status_code == 200


@pytest.mark.integration
class TestAIFeedback(TestCase):
    """FEAT-038: AI practice feedback."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="AI Feedback Academy",
            slug="rel4-aifeedback-iso",
            description="A test academy",
            email="aifeedback-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="aifeedback-owner-iso",
            email="aifeedback-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="aifeedback-owner-iso@test.com", password="testpass123")

    def test_practice_analysis_model(self):
        assert hasattr(PracticeAnalysis, "analysis_result")
        assert hasattr(PracticeAnalysis, "feedback")

    def test_analysis_page_loads(self):
        response = self.auth_client.get(reverse("practice-analysis"))
        assert response.status_code == 200


@pytest.mark.integration
class TestRecordingArchive(TestCase):
    """FEAT-039: Recording archive."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Recording Academy",
            slug="rel4-recording-iso",
            description="A test academy",
            email="recording-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="recording-owner-iso",
            email="recording-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="recording-owner-iso@test.com", password="testpass123")

    def test_recording_archive_model(self):
        assert hasattr(RecordingArchive, "title")
        assert hasattr(RecordingArchive, "recording")
        assert hasattr(RecordingArchive, "tags")

    def test_recording_archive_loads(self):
        response = self.auth_client.get(reverse("recording-archive"))
        assert response.status_code == 200


@pytest.mark.integration
class TestCalendarSync(TestCase):
    """FEAT-040: Google Calendar / Outlook sync."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Calendar Academy",
            slug="rel4-calendar-iso",
            description="A test academy",
            email="calendar-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="calendar-owner-iso",
            email="calendar-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="calendar-owner-iso@test.com", password="testpass123")
        self.anon_client = Client()

    def test_user_has_ical_fields(self):
        assert hasattr(self.owner, "ical_feed_token")
        assert hasattr(self.owner, "google_calendar_token")

    def test_calendar_sync_page_loads(self):
        response = self.auth_client.get(reverse("calendar-sync"))
        assert response.status_code == 200
        self.owner.refresh_from_db()
        assert self.owner.ical_feed_token != ""

    def test_ical_feed_generates(self):
        self.owner.ical_feed_token = "test-token-123"
        self.owner.save(update_fields=["ical_feed_token"])
        response = self.anon_client.get(reverse("ical-feed", args=["test-token-123"]))
        assert response.status_code == 200
        assert response["Content-Type"] == "text/calendar"
        assert b"BEGIN:VCALENDAR" in response.content


@pytest.mark.integration
class TestZoomMeetAlternative(TestCase):
    """FEAT-041: Zoom/Google Meet as Jitsi alternative."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Zoom Academy",
            slug="rel4-zoom-iso",
            description="A test academy",
            email="zoom-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Guitar"],
            genres=["Rock"],
        )
        cls.instructor = User.objects.create_user(
            username="zoom-instructor-iso",
            email="zoom-instructor-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor",
            instruments=["Guitar"],
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="zoom-instructor-iso@test.com", password="testpass123")

    def test_livesession_has_video_platform(self):
        assert hasattr(LiveSession, "video_platform")
        assert hasattr(LiveSession, "external_meeting_url")

    def test_default_video_platform_is_livekit(self):
        session = LiveSession.objects.create(
            title="Test Session",
            instructor=self.instructor,
            academy=self.academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            room_name="test-zoom-session",
        )
        assert session.video_platform == "livekit"

    def test_zoom_platform(self):
        session = LiveSession.objects.create(
            title="Zoom Session",
            instructor=self.instructor,
            academy=self.academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            room_name="zoom-session-test",
            video_platform="zoom",
            external_meeting_url="https://zoom.us/j/123456",
        )
        assert session.video_platform == "zoom"
        assert session.external_meeting_url == "https://zoom.us/j/123456"


@pytest.mark.integration
class TestContentLibrary(TestCase):
    """FEAT-042: Content library."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Library Academy",
            slug="rel4-library-iso",
            description="A test academy",
            email="library-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="library-owner-iso",
            email="library-owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="library-owner-iso@test.com", password="testpass123")

    def test_library_resource_model(self):
        assert hasattr(LibraryResource, "resource_type")
        assert hasattr(LibraryResource, "tags")
        assert hasattr(LibraryResource, "download_count")

    def test_library_list_loads(self):
        response = self.auth_client.get(reverse("library-list"))
        assert response.status_code == 200

    def test_library_upload_page_loads(self):
        response = self.auth_client.get(reverse("library-upload"))
        assert response.status_code == 200
