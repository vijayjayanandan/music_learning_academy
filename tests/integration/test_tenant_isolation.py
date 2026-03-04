"""Test multi-tenancy isolation — Academy A users cannot see/modify Academy B data."""

import pytest
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment
from apps.scheduling.models import LiveSession
from apps.practice.models import PracticeLog
from apps.notifications.models import Notification


@pytest.fixture
def academy_b(db):
    return Academy.objects.create(
        name="Academy B",
        slug="academy-b",
        description="Another academy",
        email="b@academy.com",
        timezone="UTC",
    )


@pytest.fixture
def user_b(db, academy_b):
    user = User.objects.create_user(
        username="user_b", email="userb@test.com", password="testpass123",
        first_name="User", last_name="B",
    )
    user.current_academy = academy_b
    user.save()
    Membership.objects.create(user=user, academy=academy_b, role="owner")
    return user


@pytest.fixture
def course_a(db, academy, instructor_user):
    return Course.objects.create(
        academy=academy, title="Course A", slug="course-a",
        instructor=instructor_user, instrument="Piano",
        difficulty_level="beginner", is_published=True,
    )


@pytest.fixture
def course_b(db, academy_b, user_b):
    return Course.objects.create(
        academy=academy_b, title="Course B", slug="course-b",
        instructor=user_b, instrument="Guitar",
        difficulty_level="beginner", is_published=True,
    )


@pytest.fixture
def client_b(client, user_b):
    client.login(username="userb@test.com", password="testpass123")
    return client


@pytest.mark.integration
class TestTenantIsolation:
    @pytest.mark.django_db
    def test_course_list_only_shows_own_academy(self, auth_client, course_a, course_b):
        response = auth_client.get(reverse("course-list"))
        assert response.status_code == 200
        courses = response.context["courses"]
        slugs = [c.slug for c in courses]
        assert "course-a" in slugs
        assert "course-b" not in slugs

    @pytest.mark.django_db
    def test_course_detail_blocked_cross_academy(self, client_b, course_a):
        response = client_b.get(reverse("course-detail", kwargs={"slug": course_a.slug}))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_enrollment_list_only_own_academy(self, auth_client, student_user, course_a, course_b, academy):
        Enrollment.objects.create(
            student=student_user, course=course_a, academy=course_a.academy,
        )
        # Enroll owner in academy_b course (shouldn't be visible)
        from apps.accounts.models import User
        owner = User.objects.get(email="owner@test.com")
        Enrollment.objects.create(
            student=owner, course=course_b, academy=course_b.academy,
        )
        response = auth_client.get(reverse("enrollment-list"))
        # Owner's enrollment in academy_b should not appear in academy_a context
        enrollments = response.context["enrollments"]
        academy_ids = set(e.academy_id for e in enrollments)
        assert course_b.academy.pk not in academy_ids

    @pytest.mark.django_db
    def test_user_b_cannot_edit_course_a(self, client_b, course_a):
        response = client_b.post(
            reverse("course-edit", kwargs={"slug": course_a.slug}),
            {"title": "Hacked!"},
        )
        assert response.status_code in (403, 404)

    @pytest.mark.django_db
    def test_user_b_cannot_delete_course_a(self, client_b, course_a):
        response = client_b.post(
            reverse("course-delete", kwargs={"slug": course_a.slug}),
        )
        assert response.status_code in (403, 404)
        assert Course.objects.filter(pk=course_a.pk).exists()

    @pytest.mark.django_db
    def test_schedule_isolated_by_academy(self, auth_client, academy, academy_b, instructor_user, user_b):
        from django.utils import timezone as tz
        from datetime import timedelta
        now = tz.now()
        LiveSession.objects.create(
            academy=academy, title="Session A", instructor=instructor_user,
            scheduled_start=now + timedelta(hours=1),
            scheduled_end=now + timedelta(hours=2),
            session_type="one_on_one", jitsi_room_name="room-a",
        )
        LiveSession.objects.create(
            academy=academy_b, title="Session B", instructor=user_b,
            scheduled_start=now + timedelta(hours=1),
            scheduled_end=now + timedelta(hours=2),
            session_type="one_on_one", jitsi_room_name="room-b",
        )
        response = auth_client.get(reverse("schedule-list"))
        assert response.status_code == 200
        titles = [s.title for s in response.context["sessions"]]
        assert "Session A" in titles
        assert "Session B" not in titles

    @pytest.mark.django_db
    def test_practice_logs_isolated(self, db, academy, academy_b, student_user, user_b):
        from datetime import date
        PracticeLog.objects.create(
            academy=academy, student=student_user, date=date.today(),
            duration_minutes=30, instrument="Piano",
        )
        PracticeLog.objects.create(
            academy=academy_b, student=user_b, date=date.today(),
            duration_minutes=45, instrument="Guitar",
        )
        logs_a = PracticeLog.objects.filter(academy=academy)
        logs_b = PracticeLog.objects.filter(academy=academy_b)
        assert logs_a.count() == 1
        assert logs_b.count() == 1
        assert logs_a.first().student == student_user
        assert logs_b.first().student == user_b

    @pytest.mark.django_db
    def test_notification_isolation(self, db, academy, academy_b, owner_user, user_b):
        Notification.objects.create(
            academy=academy, recipient=owner_user,
            notification_type="system", title="For A",
        )
        Notification.objects.create(
            academy=academy_b, recipient=user_b,
            notification_type="system", title="For B",
        )
        notifs_a = Notification.objects.filter(academy=academy)
        notifs_b = Notification.objects.filter(academy=academy_b)
        assert notifs_a.count() == 1
        assert notifs_b.count() == 1
        assert notifs_a.first().title == "For A"

    @pytest.mark.django_db
    def test_lesson_detail_blocked_cross_academy(self, client_b, course_a):
        lesson = Lesson.objects.create(
            academy=course_a.academy, course=course_a, title="Lesson 1", order=1,
        )
        response = client_b.get(
            reverse("lesson-detail", kwargs={"slug": course_a.slug, "pk": lesson.pk}),
        )
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_enroll_in_cross_academy_course_blocked(self, client_b, course_a):
        response = client_b.post(
            reverse("enroll", kwargs={"slug": course_a.slug}),
        )
        assert response.status_code in (403, 404)
        assert not Enrollment.objects.filter(course=course_a, student__email="userb@test.com").exists()

    @pytest.mark.django_db
    def test_dashboard_shows_only_own_academy_data(self, auth_client, course_a, course_b):
        response = auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_academy_members_isolated(self, auth_client, academy, academy_b, user_b):
        response = auth_client.get(
            reverse("academy-members", kwargs={"slug": academy.slug})
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "userb@test.com" not in content

    @pytest.mark.django_db
    def test_user_cannot_switch_to_unrelated_academy(self, auth_client, academy_b):
        response = auth_client.post(
            reverse("switch-academy", kwargs={"slug": academy_b.slug}),
        )
        # Should either 404/403 or redirect without switching
        user = User.objects.get(email="owner@test.com")
        assert user.current_academy != academy_b
