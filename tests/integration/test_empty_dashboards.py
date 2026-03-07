"""Tests for empty dashboard states (BUG-014, BUG-015).

Verifies that instructor and student dashboards show helpful onboarding
guidance when the user has no courses or enrollments, and that the normal
dashboard content appears when data exists.
"""

import pytest
from django.urls import reverse

from tests.factories import CourseFactory, EnrollmentFactory


@pytest.mark.integration
@pytest.mark.django_db
class TestInstructorDashboardEmptyState:
    """BUG-014: Instructor dashboard should show getting-started guidance
    when the instructor has no courses."""

    def test_shows_empty_state_when_no_courses(self, client, instructor_user, academy):
        client.login(username="instructor@test.com", password="testpass123")
        response = client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "instructor-empty-state" in content
        assert "Get started by creating your first course" in content
        assert "Create Your First Course" in content

    def test_empty_state_links_to_course_create(self, client, instructor_user, academy):
        client.login(username="instructor@test.com", password="testpass123")
        response = client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        course_create_url = reverse("course-create")
        assert course_create_url in content

    def test_shows_courses_when_they_exist(self, client, instructor_user, academy):
        CourseFactory(
            academy=academy,
            instructor=instructor_user,
            title="Guitar Basics",
            is_published=True,
        )
        client.login(username="instructor@test.com", password="testpass123")
        response = client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "instructor-empty-state" not in content
        assert "Guitar Basics" in content

    def test_no_empty_state_when_courses_exist(self, client, instructor_user, academy):
        CourseFactory(
            academy=academy,
            instructor=instructor_user,
            title="Piano 101",
        )
        client.login(username="instructor@test.com", password="testpass123")
        response = client.get(reverse("instructor-dashboard"))
        content = response.content.decode()

        assert "Get started by creating your first course" not in content


@pytest.mark.integration
@pytest.mark.django_db
class TestStudentDashboardEmptyState:
    """BUG-015: Student dashboard should show getting-started guidance
    when the student has no enrollments."""

    def test_shows_empty_state_when_no_enrollments(self, client, student_user, academy):
        client.login(username="student@test.com", password="testpass123")
        response = client.get(reverse("student-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "student-empty-state" in content
        assert "Start your musical journey" in content
        assert "Browse Available Courses" in content

    def test_empty_state_links_to_course_list(self, client, student_user, academy):
        client.login(username="student@test.com", password="testpass123")
        response = client.get(reverse("student-dashboard"))
        content = response.content.decode()

        course_list_url = reverse("course-list")
        assert course_list_url in content

    def test_shows_enrollments_when_they_exist(self, client, student_user, academy):
        course = CourseFactory(academy=academy, title="Jazz Improvisation")
        EnrollmentFactory(
            academy=academy,
            student=student_user,
            course=course,
            status="active",
        )
        client.login(username="student@test.com", password="testpass123")
        response = client.get(reverse("student-dashboard"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "student-empty-state" not in content
        assert "Jazz Improvisation" in content

    def test_no_empty_state_when_enrolled(self, client, student_user, academy):
        course = CourseFactory(academy=academy, title="Blues Guitar")
        EnrollmentFactory(
            academy=academy,
            student=student_user,
            course=course,
            status="active",
        )
        client.login(username="student@test.com", password="testpass123")
        response = client.get(reverse("student-dashboard"))
        content = response.content.decode()

        assert "Start your musical journey" not in content


@pytest.mark.integration
@pytest.mark.django_db
class TestDashboardPermissions:
    """Permission boundary tests for dashboard views."""

    def test_instructor_dashboard_unauthenticated_redirects_to_login(self, client):
        response = client.get(reverse("instructor-dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_student_dashboard_unauthenticated_redirects_to_login(self, client):
        response = client.get(reverse("student-dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url
