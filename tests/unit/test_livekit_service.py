"""Tests for LiveKit service layer."""

import pytest
from django.test import override_settings

from apps.scheduling.livekit_service import (
    generate_room_name,
    generate_access_token,
    get_livekit_config,
)


@pytest.mark.unit
class TestGenerateRoomName:
    def test_returns_string(self):
        result = generate_room_name("test-academy", "session-1")
        assert isinstance(result, str)

    def test_prefixed_with_mla(self):
        result = generate_room_name("test-academy", "session-1")
        assert result.startswith("mla-test-academy-")

    def test_deterministic(self):
        r1 = generate_room_name("test-academy", "session-1")
        r2 = generate_room_name("test-academy", "session-1")
        assert r1 == r2

    def test_unique_per_input(self):
        r1 = generate_room_name("academy-a", "session-1")
        r2 = generate_room_name("academy-b", "session-1")
        assert r1 != r2

    def test_unique_per_session(self):
        r1 = generate_room_name("test-academy", "session-1")
        r2 = generate_room_name("test-academy", "session-2")
        assert r1 != r2


@pytest.mark.unit
class TestGenerateAccessToken:
    @override_settings(
        LIVEKIT_API_KEY="test-key",
        LIVEKIT_API_SECRET="test-secret-that-is-long-enough-for-jwt",
    )
    def test_returns_jwt_string(self):
        token = generate_access_token("room-1", "user-1", "Test User")
        assert isinstance(token, str)
        assert len(token) > 0

    @override_settings(
        LIVEKIT_API_KEY="test-key",
        LIVEKIT_API_SECRET="test-secret-that-is-long-enough-for-jwt",
    )
    def test_works_for_instructor(self):
        token = generate_access_token(
            "room-1", "user-1", "Instructor", is_instructor=True
        )
        assert isinstance(token, str)
        assert len(token) > 0

    @override_settings(
        LIVEKIT_API_KEY="test-key",
        LIVEKIT_API_SECRET="test-secret-that-is-long-enough-for-jwt",
    )
    def test_works_for_student(self):
        token = generate_access_token(
            "room-1", "user-2", "Student", is_instructor=False
        )
        assert isinstance(token, str)
        assert len(token) > 0


@pytest.mark.unit
class TestGetLivekitConfig:
    @override_settings(
        LIVEKIT_URL="wss://test.livekit.cloud",
        LIVEKIT_API_KEY="test-key",
        LIVEKIT_API_SECRET="test-secret-that-is-long-enough-for-jwt",
    )
    @pytest.mark.django_db
    def test_contains_required_keys(self):
        from apps.accounts.models import User
        from apps.academies.models import Academy
        from apps.scheduling.models import LiveSession
        from django.utils import timezone

        academy = Academy.objects.create(
            name="Test",
            slug="test",
            email="t@t.com",
            timezone="UTC",
        )
        instructor = User.objects.create_user(
            username="inst",
            email="inst@test.com",
            password="pass",
        )
        User.objects.create_user(
            username="stu",
            email="stu@test.com",
            password="pass",
        )
        session = LiveSession.objects.create(
            academy=academy,
            title="Test",
            instructor=instructor,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now(),
            room_name="test-room",
        )

        config = get_livekit_config(session, instructor)
        assert "wsUrl" in config
        assert "token" in config
        assert "roomName" in config
        assert "isInstructor" in config
        assert "startMuted" in config
        assert "participantName" in config
        assert config["wsUrl"] == "wss://test.livekit.cloud"
        assert config["roomName"] == "test-room"

    @override_settings(
        LIVEKIT_URL="wss://test.livekit.cloud",
        LIVEKIT_API_KEY="test-key",
        LIVEKIT_API_SECRET="test-secret-that-is-long-enough-for-jwt",
    )
    @pytest.mark.django_db
    def test_instructor_not_muted(self):
        from apps.accounts.models import User
        from apps.academies.models import Academy
        from apps.scheduling.models import LiveSession
        from django.utils import timezone

        academy = Academy.objects.create(
            name="Test2",
            slug="test2",
            email="t2@t.com",
            timezone="UTC",
        )
        instructor = User.objects.create_user(
            username="inst2",
            email="inst2@test.com",
            password="pass",
        )
        session = LiveSession.objects.create(
            academy=academy,
            title="Test",
            instructor=instructor,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now(),
            room_name="test-room-2",
        )
        config = get_livekit_config(session, instructor)
        assert config["isInstructor"] is True
        assert config["startMuted"] is False

    @override_settings(
        LIVEKIT_URL="wss://test.livekit.cloud",
        LIVEKIT_API_KEY="test-key",
        LIVEKIT_API_SECRET="test-secret-that-is-long-enough-for-jwt",
    )
    @pytest.mark.django_db
    def test_student_muted(self):
        from apps.accounts.models import User
        from apps.academies.models import Academy
        from apps.scheduling.models import LiveSession
        from django.utils import timezone

        academy = Academy.objects.create(
            name="Test3",
            slug="test3",
            email="t3@t.com",
            timezone="UTC",
        )
        instructor = User.objects.create_user(
            username="inst3",
            email="inst3@test.com",
            password="pass",
        )
        student = User.objects.create_user(
            username="stu3",
            email="stu3@test.com",
            password="pass",
        )
        session = LiveSession.objects.create(
            academy=academy,
            title="Test",
            instructor=instructor,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now(),
            room_name="test-room-3",
        )
        config = get_livekit_config(session, student)
        assert config["isInstructor"] is False
        assert config["startMuted"] is True


@pytest.mark.unit
class TestLivekitPermissions:
    @override_settings(LIVEKIT_API_KEY="", LIVEKIT_API_SECRET="")
    def test_generate_room_name_works_without_credentials(self):
        # Room name generation doesn't need LiveKit credentials
        result = generate_room_name("test", "1")
        assert result.startswith("mla-test-")
