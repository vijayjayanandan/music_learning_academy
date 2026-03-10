"""Tests for empty dashboard states (BUG-014, BUG-015).

Verifies that instructor and student dashboards show helpful onboarding
guidance when the user has no courses or enrollments, and that the normal
dashboard content appears when data exists.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from tests.factories import CourseFactory, EnrollmentFactory


@pytest.mark.integration
class TestInstructorDashboardEmptyState(TestCase):
    """BUG-014: Instructor dashboard should show getting-started guidance
    when the instructor has no courses."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Instructor Empty Academy",
            slug="empty-instructor-iso",
            description="A test academy",
            email="empty-instructor-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor_user = User.objects.create_user(
            username="instructor-empty-iso",
            email="instructor-empty-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user,
            academy=cls.academy,
            role="instructor",
            instruments=["Piano"],
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="instructor-empty-iso@test.com", password="testpass123")

    def test_shows_empty_state_when_no_courses(self):
        response = self.client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "instructor-empty-state" in content
        assert "Get started by creating your first course" in content
        assert "Create Your First Course" in content

    def test_empty_state_links_to_course_create(self):
        response = self.client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        course_create_url = reverse("course-create")
        assert course_create_url in content

    def test_shows_courses_when_they_exist(self):
        CourseFactory(
            academy=self.academy,
            instructor=self.instructor_user,
            title="Guitar Basics",
            is_published=True,
        )
        response = self.client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "instructor-empty-state" not in content
        assert "Guitar Basics" in content

    def test_no_empty_state_when_courses_exist(self):
        CourseFactory(
            academy=self.academy,
            instructor=self.instructor_user,
            title="Piano 101",
        )
        response = self.client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        assert "Get started by creating your first course" not in content


@pytest.mark.integration
class TestStudentDashboardEmptyState(TestCase):
    """BUG-015: Student dashboard should show getting-started guidance
    when the student has no enrollments."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Student Empty Academy",
            slug="empty-student-iso",
            description="A test academy",
            email="empty-student-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.student_user = User.objects.create_user(
            username="student-empty-iso",
            email="student-empty-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user,
            academy=cls.academy,
            role="student",
            instruments=["Piano"],
            skill_level="beginner",
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="student-empty-iso@test.com", password="testpass123")

    def test_shows_empty_state_when_no_enrollments(self):
        response = self.client.get(reverse("student-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "student-empty-state" in content
        assert "Start your musical journey" in content
        assert "Browse Available Courses" in content

    def test_empty_state_links_to_course_list(self):
        response = self.client.get(reverse("student-dashboard"))
        content = response.content.decode()

        course_list_url = reverse("course-list")
        assert course_list_url in content

    def test_shows_enrollments_when_they_exist(self):
        course = CourseFactory(academy=self.academy, title="Jazz Improvisation")
        EnrollmentFactory(
            academy=self.academy,
            student=self.student_user,
            course=course,
            status="active",
        )
        response = self.client.get(reverse("student-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "student-empty-state" not in content
        assert "Jazz Improvisation" in content

    def test_no_empty_state_when_enrolled(self):
        course = CourseFactory(academy=self.academy, title="Blues Guitar")
        EnrollmentFactory(
            academy=self.academy,
            student=self.student_user,
            course=course,
            status="active",
        )
        response = self.client.get(reverse("student-dashboard"))
        content = response.content.decode()

        assert "Start your musical journey" not in content


@pytest.mark.integration
class TestDashboardPermissions(TestCase):
    """Permission boundary tests for dashboard views."""

    def setUp(self):
        self.client = Client()

    def test_instructor_dashboard_unauthenticated_redirects_to_login(self):
        response = self.client.get(reverse("instructor-dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_student_dashboard_unauthenticated_redirects_to_login(self):
        response = self.client.get(reverse("student-dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url
