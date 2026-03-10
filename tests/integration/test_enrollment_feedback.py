"""Tests for enrollment success toast messages."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment


@pytest.mark.integration
class TestEnrollmentSuccessMessages(TestCase):
    """Test that enrolling in a course sets the correct success message."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Feedback Test Academy",
            slug="feedback-test-iso",
            description="Test",
            email="feedback@test.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.student = User.objects.create_user(
            username="feedback-student",
            email="feedback-student@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(user=cls.student, academy=cls.academy, role="student")

        cls.instructor = User.objects.create_user(
            username="feedback-instructor",
            email="feedback-instructor@test.com",
            password="testpass123",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

        # Course with lessons
        cls.course_with_lessons = Course.objects.create(
            academy=cls.academy,
            title="Guitar Basics",
            slug="guitar-basics",
            description="Learn guitar",
            instructor=cls.instructor,
            instrument="Guitar",
            difficulty_level="beginner",
            is_published=True,
            price_cents=0,
        )
        cls.lesson = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course_with_lessons,
            title="First Lesson",
            order=1,
        )

        # Course without lessons
        cls.course_no_lessons = Course.objects.create(
            academy=cls.academy,
            title="Piano Intro",
            slug="piano-intro",
            description="Learn piano",
            instructor=cls.instructor,
            instrument="Piano",
            difficulty_level="beginner",
            is_published=True,
            price_cents=0,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="feedback-student@test.com", password="testpass123")

    def test_enroll_with_lessons_shows_start_message(self):
        """Happy path: enrolling in a course with lessons shows 'Start with your first lesson' message."""
        url = reverse("enroll", kwargs={"slug": self.course_with_lessons.slug})
        response = self.client.post(url, follow=True)

        msgs = list(get_messages(response.wsgi_request))
        assert len(msgs) == 1
        assert msgs[0].tags == "success"
        assert "You're enrolled in Guitar Basics" in str(msgs[0])
        assert "Start with your first lesson" in str(msgs[0])

    def test_enroll_without_lessons_shows_instructor_message(self):
        """Boundary: enrolling in a course with no lessons shows 'instructor will add lessons' message."""
        url = reverse("enroll", kwargs={"slug": self.course_no_lessons.slug})
        response = self.client.post(url, follow=True)

        msgs = list(get_messages(response.wsgi_request))
        assert len(msgs) == 1
        assert msgs[0].tags == "success"
        assert "You're enrolled in Piano Intro" in str(msgs[0])
        assert "Your instructor will add lessons soon" in str(msgs[0])

    def test_enroll_already_enrolled_no_message(self):
        """Re-enrolling in the same course does not produce a success message."""
        # Create an existing enrollment
        Enrollment.objects.create(
            student=self.student,
            course=self.course_with_lessons,
            academy=self.academy,
        )
        url = reverse("enroll", kwargs={"slug": self.course_with_lessons.slug})
        response = self.client.post(url, follow=True)

        msgs = list(get_messages(response.wsgi_request))
        assert len(msgs) == 0

    def test_enroll_redirects_to_first_lesson(self):
        """After enrolling in a course with lessons, redirects to the first lesson."""
        url = reverse("enroll", kwargs={"slug": self.course_with_lessons.slug})
        response = self.client.post(url)

        expected_url = reverse(
            "lesson-detail",
            kwargs={
                "slug": self.course_with_lessons.slug,
                "pk": self.lesson.pk,
            },
        )
        assert response.status_code == 302
        assert response.url == expected_url

    def test_enroll_no_lessons_redirects_to_course_detail(self):
        """After enrolling in a course without lessons, redirects to course detail."""
        url = reverse("enroll", kwargs={"slug": self.course_no_lessons.slug})
        response = self.client.post(url)

        expected_url = reverse(
            "course-detail",
            kwargs={"slug": self.course_no_lessons.slug},
        )
        assert response.status_code == 302
        assert response.url == expected_url
