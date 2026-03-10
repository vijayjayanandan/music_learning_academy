"""Integration tests for the 3-step course creation wizard."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course


@pytest.mark.integration
class TestCourseWizardHappyPath(TestCase):
    """Test creating a course through the wizard form (single POST)."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Wizard Academy",
            slug="wizard-happy-iso",
            description="Test academy",
            email="wizard-happy@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="wizard-happy-owner",
            email="wizard-happy-owner@test.com",
            password="testpass123",
            first_name="Wizard",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="wizard-happy-owner@test.com", password="testpass123"
        )

    def test_course_create_get_returns_wizard(self):
        """GET course-create should return the 3-step wizard template."""
        response = self.auth_client.get(reverse("course-create"))
        assert response.status_code == 200
        content = response.content.decode()
        # Check for wizard step indicators
        assert 'id="step-indicator-1"' in content
        assert 'id="step-indicator-2"' in content
        assert 'id="step-indicator-3"' in content
        # Check for wizard step panels
        assert 'id="wizard-step-1"' in content
        assert 'id="wizard-step-2"' in content
        assert 'id="wizard-step-3"' in content
        # Check JS is loaded
        assert "course_wizard.js" in content

    def test_course_create_post_valid_data_creates_course(self):
        """POST with valid data creates a course and redirects to detail."""
        url = reverse("course-create")
        data = {
            "title": "Piano Fundamentals",
            "instrument": "Piano",
            "difficulty_level": "beginner",
            "genre": "Classical",
            "description": "Learn the basics of piano.",
            "prerequisites": "",
            "estimated_duration_weeks": 8,
            "max_students": 20,
        }
        response = self.auth_client.post(url, data)
        # Should redirect to course detail
        assert response.status_code == 302

        # Verify course was created
        course = Course.objects.get(title="Piano Fundamentals")
        assert course.academy == self.academy
        assert course.instructor == self.owner
        assert course.instrument == "Piano"
        assert course.difficulty_level == "beginner"
        assert course.slug == "piano-fundamentals"
        assert course.is_published is False

        # Redirect should point to course detail
        assert response.url == reverse("course-detail", kwargs={"slug": course.slug})

    def test_course_create_sets_success_message(self):
        """After creating a course, a success message should be set."""
        url = reverse("course-create")
        data = {
            "title": "Guitar Basics",
            "instrument": "Guitar",
            "difficulty_level": "beginner",
            "genre": "Rock",
            "description": "Learn guitar from scratch.",
            "estimated_duration_weeks": 6,
            "max_students": 15,
        }
        response = self.auth_client.post(url, data, follow=True)
        assert response.status_code == 200

        # Check for success message
        messages = list(response.context["messages"])
        assert len(messages) >= 1
        assert "Course created" in str(messages[0])
        assert "first lesson" in str(messages[0])

    def test_course_create_with_publish(self):
        """Course can be created with is_published=True."""
        url = reverse("course-create")
        data = {
            "title": "Advanced Jazz Theory",
            "instrument": "Piano",
            "difficulty_level": "advanced",
            "genre": "Jazz",
            "description": "Deep dive into jazz theory.",
            "estimated_duration_weeks": 12,
            "max_students": 10,
            "is_published": "on",
        }
        response = self.auth_client.post(url, data)
        assert response.status_code == 302

        course = Course.objects.get(title="Advanced Jazz Theory")
        assert course.is_published is True
        assert course.published_at is not None


@pytest.mark.integration
class TestCourseWizardPermissions(TestCase):
    """Test that students cannot access the course creation wizard."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Wizard Perm Academy",
            slug="wizard-perm-iso",
            description="Test academy",
            email="wizard-perm@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.student = User.objects.create_user(
            username="wizard-perm-student",
            email="wizard-perm-student@test.com",
            password="testpass123",
            first_name="Student",
            last_name="User",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="wizard-perm-student@test.com", password="testpass123"
        )
        self.anon_client = Client()

    def test_student_cannot_access_course_create(self):
        """Students should be forbidden from creating courses."""
        response = self.student_client.get(reverse("course-create"))
        assert response.status_code in (302, 403)

    def test_student_cannot_post_course_create(self):
        """Students should be forbidden from POST to course-create."""
        url = reverse("course-create")
        data = {
            "title": "Hack Course",
            "instrument": "Hacking",
            "difficulty_level": "beginner",
            "description": "This should not be created.",
            "estimated_duration_weeks": 1,
            "max_students": 1,
        }
        response = self.student_client.post(url, data)
        assert response.status_code in (302, 403)
        assert not Course.objects.filter(title="Hack Course").exists()

    def test_anonymous_user_redirected_from_course_create(self):
        """Anonymous users should be redirected to login."""
        response = self.anon_client.get(reverse("course-create"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.integration
class TestCourseDetailFirstLessonCTA(TestCase):
    """Test the 'Add Your First Lesson' CTA on course detail page."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="CTA Academy",
            slug="wizard-cta-iso",
            description="Test academy",
            email="wizard-cta@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="wizard-cta-owner",
            email="wizard-cta-owner@test.com",
            password="testpass123",
            first_name="CTA",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="wizard-cta-student",
            email="wizard-cta-student@test.com",
            password="testpass123",
            first_name="CTA",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
        )

        cls.course_no_lessons = Course.objects.create(
            academy=cls.academy,
            title="Empty Course",
            slug="wizard-cta-empty",
            instructor=cls.owner,
            instrument="Piano",
            difficulty_level="beginner",
            description="A course with no lessons.",
            is_published=True,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="wizard-cta-owner@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="wizard-cta-student@test.com", password="testpass123"
        )

    def test_instructor_sees_first_lesson_cta_when_no_lessons(self):
        """When a course has zero lessons, the instructor/owner sees the CTA."""
        url = reverse("course-detail", kwargs={"slug": self.course_no_lessons.slug})
        response = self.auth_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Add Your First Lesson" in content

    def test_student_does_not_see_first_lesson_cta(self):
        """Students should not see the 'Add Your First Lesson' CTA."""
        url = reverse("course-detail", kwargs={"slug": self.course_no_lessons.slug})
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Add Your First Lesson" not in content
