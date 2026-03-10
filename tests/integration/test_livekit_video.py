"""Integration tests for LiveKit video sessions."""

import pytest
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.scheduling.models import LiveSession


@pytest.mark.integration
class TestJoinSessionLivekitConfig(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Video Academy",
            slug="lk-joinconfig-iso",
            email="video-joinconfig@test.com",
            timezone="UTC",
        )
        cls.instructor = User.objects.create_user(
            username="vid_instructor_joinconfig",
            email="vidinst-joinconfig@test.com",
            password="testpass123",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

        cls.student = User.objects.create_user(
            username="vid_student_joinconfig",
            email="vidstu-joinconfig@test.com",
            password="testpass123",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(user=cls.student, academy=cls.academy, role="student")

        cls.session = LiveSession.objects.create(
            academy=cls.academy,
            title="Test Video Session",
            instructor=cls.instructor,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timezone.timedelta(hours=1),
            room_name="test-video-room-joinconfig",
        )

    def setUp(self):
        self.instructor_client = Client()
        self.instructor_client.login(
            username="vidinst-joinconfig@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="vidstu-joinconfig@test.com", password="testpass123"
        )

    @override_settings(
        LIVEKIT_URL="wss://test.livekit.cloud",
        LIVEKIT_API_KEY="test-key",
        LIVEKIT_API_SECRET="test-secret-that-is-long-enough-for-jwt",
    )
    def test_join_session_returns_livekit_config(self):
        response = self.instructor_client.get(
            reverse("session-join", kwargs={"pk": self.session.pk})
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "livekit-app" in content
        assert "data-config" in content

    def test_student_cannot_join_without_registration(self):
        response = self.student_client.get(
            reverse("session-join", kwargs={"pk": self.session.pk})
        )
        assert response.status_code == 403
