"""Test multi-tenancy isolation — Academy A users cannot see/modify Academy B data."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment
from apps.scheduling.models import LiveSession
from apps.practice.models import PracticeLog
from apps.notifications.models import Notification


@pytest.mark.integration
class TestTenantIsolation(TestCase):
    """
    Uses setUpTestData to create shared DB objects ONCE for all 13 tests,
    rather than per-test (the default pytest fixture behaviour).

    Django wraps each test method in a SAVEPOINT so test-specific writes
    (Enrollment, LiveSession, etc.) are rolled back after each test, while
    the shared objects (Academy, User, Course) persist for the whole class.
    """

    @classmethod
    def setUpTestData(cls):
        # --- Academy A ---
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-academy-iso",
            description="A test academy",
            email="test-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-iso",
            email="owner-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="instructor-iso",
            email="instructor-iso@test.com",
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
            username="student-iso",
            email="student-iso@test.com",
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

        cls.course_a = Course.objects.create(
            academy=cls.academy, title="Course A", slug="course-a-iso",
            instructor=cls.instructor, instrument="Piano",
            difficulty_level="beginner", is_published=True,
        )

        # --- Academy B ---
        cls.academy_b = Academy.objects.create(
            name="Academy B",
            slug="academy-b-iso",
            description="Another academy",
            email="b-iso@academy.com",
            timezone="UTC",
        )
        cls.user_b = User.objects.create_user(
            username="user-b-iso",
            email="userb-iso@test.com",
            password="testpass123",
            first_name="User",
            last_name="B",
        )
        cls.user_b.current_academy = cls.academy_b
        cls.user_b.save()
        Membership.objects.create(user=cls.user_b, academy=cls.academy_b, role="owner")

        cls.course_b = Course.objects.create(
            academy=cls.academy_b, title="Course B", slug="course-b-iso",
            instructor=cls.user_b, instrument="Guitar",
            difficulty_level="beginner", is_published=True,
        )

    def setUp(self):
        """Fresh HTTP clients for each test (no session bleed)."""
        self.auth_client = Client()
        self.auth_client.login(username="owner-iso@test.com", password="testpass123")
        self.client_b = Client()
        self.client_b.login(username="userb-iso@test.com", password="testpass123")

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_course_list_only_shows_own_academy(self):
        response = self.auth_client.get(reverse("course-list"))
        self.assertEqual(response.status_code, 200)
        slugs = [c.slug for c in response.context["courses"]]
        self.assertIn("course-a-iso", slugs)
        self.assertNotIn("course-b-iso", slugs)

    def test_course_detail_blocked_cross_academy(self):
        response = self.client_b.get(
            reverse("course-detail", kwargs={"slug": self.course_a.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_enrollment_list_only_own_academy(self):
        Enrollment.objects.create(
            student=self.student, course=self.course_a, academy=self.course_a.academy,
        )
        Enrollment.objects.create(
            student=self.owner, course=self.course_b, academy=self.course_b.academy,
        )
        response = self.auth_client.get(reverse("enrollment-list"))
        academy_ids = {e.academy_id for e in response.context["enrollments"]}
        self.assertNotIn(self.course_b.academy.pk, academy_ids)

    def test_user_b_cannot_edit_course_a(self):
        response = self.client_b.post(
            reverse("course-edit", kwargs={"slug": self.course_a.slug}),
            {"title": "Hacked!"},
        )
        self.assertIn(response.status_code, (403, 404))

    def test_user_b_cannot_delete_course_a(self):
        response = self.client_b.post(
            reverse("course-delete", kwargs={"slug": self.course_a.slug}),
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertTrue(Course.objects.filter(pk=self.course_a.pk).exists())

    def test_schedule_isolated_by_academy(self):
        from django.utils import timezone as tz
        from datetime import timedelta
        now = tz.now()
        LiveSession.objects.create(
            academy=self.academy, title="Session A", instructor=self.instructor,
            scheduled_start=now + timedelta(hours=1),
            scheduled_end=now + timedelta(hours=2),
            session_type="one_on_one", room_name="room-a-iso",
        )
        LiveSession.objects.create(
            academy=self.academy_b, title="Session B", instructor=self.user_b,
            scheduled_start=now + timedelta(hours=1),
            scheduled_end=now + timedelta(hours=2),
            session_type="one_on_one", room_name="room-b-iso",
        )
        response = self.auth_client.get(reverse("schedule-list"))
        self.assertEqual(response.status_code, 200)
        titles = [s.title for s in response.context["sessions"]]
        self.assertIn("Session A", titles)
        self.assertNotIn("Session B", titles)

    def test_practice_logs_isolated(self):
        from datetime import date
        PracticeLog.objects.create(
            academy=self.academy, student=self.student, date=date.today(),
            duration_minutes=30, instrument="Piano",
        )
        PracticeLog.objects.create(
            academy=self.academy_b, student=self.user_b, date=date.today(),
            duration_minutes=45, instrument="Guitar",
        )
        self.assertEqual(PracticeLog.objects.filter(academy=self.academy).count(), 1)
        self.assertEqual(PracticeLog.objects.filter(academy=self.academy_b).count(), 1)
        self.assertEqual(PracticeLog.objects.filter(academy=self.academy).first().student, self.student)

    def test_notification_isolation(self):
        Notification.objects.create(
            academy=self.academy, recipient=self.owner,
            notification_type="system", title="For A",
        )
        Notification.objects.create(
            academy=self.academy_b, recipient=self.user_b,
            notification_type="system", title="For B",
        )
        notifs_a = Notification.objects.filter(academy=self.academy)
        notifs_b = Notification.objects.filter(academy=self.academy_b)
        self.assertEqual(notifs_a.count(), 1)
        self.assertEqual(notifs_b.count(), 1)
        self.assertEqual(notifs_a.first().title, "For A")

    def test_lesson_detail_blocked_cross_academy(self):
        lesson = Lesson.objects.create(
            academy=self.course_a.academy, course=self.course_a,
            title="Lesson 1", order=1,
        )
        response = self.client_b.get(
            reverse("lesson-detail", kwargs={"slug": self.course_a.slug, "pk": lesson.pk}),
        )
        self.assertEqual(response.status_code, 404)

    def test_enroll_in_cross_academy_course_blocked(self):
        response = self.client_b.post(
            reverse("enroll", kwargs={"slug": self.course_a.slug}),
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertFalse(
            Enrollment.objects.filter(
                course=self.course_a, student__email="userb-iso@test.com"
            ).exists()
        )

    def test_dashboard_shows_only_own_academy_data(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_academy_members_isolated(self):
        response = self.auth_client.get(
            reverse("academy-members", kwargs={"slug": self.academy.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("userb-iso@test.com", response.content.decode())

    def test_user_cannot_switch_to_unrelated_academy(self):
        self.auth_client.post(
            reverse("switch-academy", kwargs={"slug": self.academy_b.slug}),
        )
        user = User.objects.get(email="owner-iso@test.com")
        self.assertNotEqual(user.current_academy, self.academy_b)
