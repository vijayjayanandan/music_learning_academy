"""Tests for FEAT-033 through FEAT-042 (Release 4: Music-Specific)."""
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.courses.models import Course
from apps.music_tools.models import (
    EarTrainingExercise, EarTrainingScore, RecitalEvent,
    RecitalPerformer, PracticeAnalysis, RecordingArchive,
)
from apps.library.models import LibraryResource
from apps.scheduling.models import LiveSession


@pytest.mark.integration
class TestMetronome:
    """FEAT-033: Built-in metronome."""

    def test_metronome_page_loads(self, auth_client):
        response = auth_client.get(reverse("metronome"))
        assert response.status_code == 200
        assert b"Metronome" in response.content
        assert b"AudioContext" in response.content


@pytest.mark.integration
class TestTuner:
    """FEAT-034: Built-in tuner."""

    def test_tuner_page_loads(self, auth_client):
        response = auth_client.get(reverse("tuner"))
        assert response.status_code == 200
        assert b"Tuner" in response.content
        assert b"getUserMedia" in response.content


@pytest.mark.integration
class TestNotationRenderer:
    """FEAT-035: Music notation renderer."""

    def test_notation_page_loads(self, auth_client):
        response = auth_client.get(reverse("notation-renderer"))
        assert response.status_code == 200
        assert b"ABC" in response.content or b"notation" in response.content.lower()


@pytest.mark.integration
class TestEarTraining:
    """FEAT-036: Ear training exercises."""

    def test_ear_training_model(self, db):
        assert hasattr(EarTrainingExercise, "exercise_type")
        assert hasattr(EarTrainingExercise, "questions")

    def test_ear_training_list_loads(self, auth_client):
        response = auth_client.get(reverse("ear-training-list"))
        assert response.status_code == 200

    def test_ear_training_exercise_play(self, auth_client, academy, db):
        exercise = EarTrainingExercise.objects.create(
            title="Intervals Quiz",
            exercise_type="interval",
            academy=academy,
            difficulty=2,
            questions=[
                {"question": "What interval is this?", "options": ["3rd", "5th", "octave"], "answer": "5th"},
            ],
        )
        response = auth_client.get(reverse("ear-training-play", args=[exercise.pk]))
        assert response.status_code == 200
        assert b"Intervals Quiz" in response.content

    def test_submit_ear_training_score(self, auth_client, owner_user, academy, db):
        exercise = EarTrainingExercise.objects.create(
            title="Chord ID",
            exercise_type="chord",
            academy=academy,
            questions=[],
        )
        response = auth_client.post(reverse("ear-training-play", args=[exercise.pk]), {
            "score": "8",
            "total_questions": "10",
            "time_taken": "120",
        })
        assert response.status_code == 302
        score = EarTrainingScore.objects.get(student=owner_user, exercise=exercise)
        assert score.score == 8
        assert score.percentage == 80


@pytest.mark.integration
class TestVirtualRecitals:
    """FEAT-037: Virtual recital events."""

    def test_recital_model(self, db):
        assert hasattr(RecitalEvent, "jitsi_room_name")
        assert hasattr(RecitalEvent, "is_public")

    def test_recital_list_loads(self, auth_client):
        response = auth_client.get(reverse("recital-list"))
        assert response.status_code == 200

    def test_recital_detail(self, auth_client, academy, db):
        recital = RecitalEvent.objects.create(
            title="Spring Recital",
            academy=academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=2),
            jitsi_room_name="spring-recital-room",
        )
        response = auth_client.get(reverse("recital-detail", args=[recital.pk]))
        assert response.status_code == 200
        assert b"Spring Recital" in response.content

    def test_recital_create_page(self, auth_client):
        response = auth_client.get(reverse("recital-create"))
        assert response.status_code == 200


@pytest.mark.integration
class TestAIFeedback:
    """FEAT-038: AI practice feedback."""

    def test_practice_analysis_model(self, db):
        assert hasattr(PracticeAnalysis, "analysis_result")
        assert hasattr(PracticeAnalysis, "feedback")

    def test_analysis_page_loads(self, auth_client):
        response = auth_client.get(reverse("practice-analysis"))
        assert response.status_code == 200


@pytest.mark.integration
class TestRecordingArchive:
    """FEAT-039: Recording archive."""

    def test_recording_archive_model(self, db):
        assert hasattr(RecordingArchive, "title")
        assert hasattr(RecordingArchive, "recording")
        assert hasattr(RecordingArchive, "tags")

    def test_recording_archive_loads(self, auth_client):
        response = auth_client.get(reverse("recording-archive"))
        assert response.status_code == 200


@pytest.mark.integration
class TestCalendarSync:
    """FEAT-040: Google Calendar / Outlook sync."""

    def test_user_has_ical_fields(self, owner_user):
        assert hasattr(owner_user, "ical_feed_token")
        assert hasattr(owner_user, "google_calendar_token")

    def test_calendar_sync_page_loads(self, auth_client, owner_user):
        response = auth_client.get(reverse("calendar-sync"))
        assert response.status_code == 200
        owner_user.refresh_from_db()
        assert owner_user.ical_feed_token != ""

    def test_ical_feed_generates(self, client, owner_user, academy, db):
        owner_user.ical_feed_token = "test-token-123"
        owner_user.save(update_fields=["ical_feed_token"])
        response = client.get(reverse("ical-feed", args=["test-token-123"]))
        assert response.status_code == 200
        assert response["Content-Type"] == "text/calendar"
        assert b"BEGIN:VCALENDAR" in response.content


@pytest.mark.integration
class TestZoomMeetAlternative:
    """FEAT-041: Zoom/Google Meet as Jitsi alternative."""

    def test_livesession_has_video_platform(self, db):
        assert hasattr(LiveSession, "video_platform")
        assert hasattr(LiveSession, "external_meeting_url")

    def test_default_video_platform_is_jitsi(self, instructor_user, academy, db):
        session = LiveSession.objects.create(
            title="Test Session",
            instructor=instructor_user,
            academy=academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            jitsi_room_name="test-zoom-session",
        )
        assert session.video_platform == "jitsi"

    def test_zoom_platform(self, instructor_user, academy, db):
        session = LiveSession.objects.create(
            title="Zoom Session",
            instructor=instructor_user,
            academy=academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            jitsi_room_name="zoom-session-test",
            video_platform="zoom",
            external_meeting_url="https://zoom.us/j/123456",
        )
        assert session.video_platform == "zoom"
        assert session.external_meeting_url == "https://zoom.us/j/123456"


@pytest.mark.integration
class TestContentLibrary:
    """FEAT-042: Content library."""

    def test_library_resource_model(self, db):
        assert hasattr(LibraryResource, "resource_type")
        assert hasattr(LibraryResource, "tags")
        assert hasattr(LibraryResource, "download_count")

    def test_library_list_loads(self, auth_client):
        response = auth_client.get(reverse("library-list"))
        assert response.status_code == 200

    def test_library_upload_page_loads(self, auth_client):
        response = auth_client.get(reverse("library-upload"))
        assert response.status_code == 200
