"""Tests for lesson progress tracking on the lesson detail page.

Covers:
- Progress bar visibility for enrolled students
- Mark-complete button visibility (students only, not instructors)
- HTMX mark-complete from lesson detail returns correct partial
- Next-lesson CTA appears after marking complete
- Course completion celebration card on last lesson
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment, LessonProgress


@pytest.mark.integration
class TestLessonProgressBarForStudents(TestCase):
    """Test that enrolled students see progress bar and mark-complete button."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Progress Test Academy",
            slug="lpt-progress-iso",
            description="Academy for progress tests",
            email="lpt-progress@test.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="lpt-progress-inst",
            email="lpt-progress-inst@test.com",
            password="testpass123",
            first_name="Instructor",
            last_name="Test",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor,
            academy=cls.academy,
            role="instructor",
            instruments=["Piano"],
        )

        cls.student = User.objects.create_user(
            username="lpt-progress-student",
            email="lpt-progress-student@test.com",
            password="testpass123",
            first_name="Student",
            last_name="Test",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
        )

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Progress Test Course",
            slug="lpt-progress-course",
            description="A course for testing progress",
            instructor=cls.instructor,
            instrument="Piano",
            is_published=True,
        )
        cls.lesson1 = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="Lesson One",
            order=1,
            estimated_duration_minutes=30,
        )
        cls.lesson2 = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="Lesson Two",
            order=2,
            estimated_duration_minutes=45,
        )
        cls.lesson3 = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="Lesson Three",
            order=3,
            estimated_duration_minutes=60,
        )

        cls.enrollment = Enrollment.objects.create(
            student=cls.student,
            course=cls.course,
            academy=cls.academy,
            status="active",
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="lpt-progress-student@test.com", password="testpass123"
        )
        self.instructor_client = Client()
        self.instructor_client.login(
            username="lpt-progress-inst@test.com", password="testpass123"
        )

    def test_enrolled_student_sees_progress_bar(self):
        """Happy path: enrolled student sees progress bar and mark-complete button."""
        url = reverse(
            "lesson-detail",
            kwargs={"slug": self.course.slug, "pk": self.lesson1.pk},
        )
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        # Progress bar is present
        assert "Course Progress" in content
        assert "0 of 3 lessons completed" in content
        assert 'class="progress progress-primary w-full"' in content
        # Mark complete button is present
        assert "Mark Lesson Complete" in content

    def test_enrolled_student_sees_updated_progress_count(self):
        """After completing a lesson, the progress count updates."""
        LessonProgress.objects.create(
            enrollment=self.enrollment,
            lesson=self.lesson1,
            academy=self.academy,
            is_completed=True,
        )
        url = reverse(
            "lesson-detail",
            kwargs={"slug": self.course.slug, "pk": self.lesson2.pk},
        )
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "1 of 3 lessons completed" in content

    def test_completed_lesson_shows_completed_state(self):
        """When the current lesson is already completed, shows 'Lesson Completed' state."""
        LessonProgress.objects.create(
            enrollment=self.enrollment,
            lesson=self.lesson1,
            academy=self.academy,
            is_completed=True,
        )
        url = reverse(
            "lesson-detail",
            kwargs={"slug": self.course.slug, "pk": self.lesson1.pk},
        )
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Lesson Completed" in content
        assert "Mark as Incomplete" in content
        # Next lesson CTA should appear
        assert "Continue to the next lesson" in content

    def test_unenrolled_student_does_not_see_progress(self):
        """Student not enrolled in this course does not see progress bar."""
        other_student = User.objects.create_user(
            username="lpt-other-student",
            email="lpt-other-student@test.com",
            password="testpass123",
        )
        other_student.current_academy = self.academy
        other_student.save()
        Membership.objects.create(
            user=other_student, academy=self.academy, role="student"
        )
        other_client = Client()
        other_client.login(
            username="lpt-other-student@test.com", password="testpass123"
        )
        url = reverse(
            "lesson-detail",
            kwargs={"slug": self.course.slug, "pk": self.lesson1.pk},
        )
        response = other_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Course Progress" not in content
        assert "Mark Lesson Complete" not in content


@pytest.mark.integration
class TestInstructorDoesNotSeeMarkComplete(TestCase):
    """Test that instructors see Edit Lesson, not Mark Complete."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Instructor Role Academy",
            slug="lpt-inst-iso",
            description="Academy for instructor role tests",
            email="lpt-inst@test.com",
            timezone="UTC",
            primary_instruments=["Guitar"],
            genres=["Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="lpt-inst-user",
            email="lpt-inst-user@test.com",
            password="testpass123",
            first_name="Instructor",
            last_name="Role",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor,
            academy=cls.academy,
            role="instructor",
            instruments=["Guitar"],
        )

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Instructor Test Course",
            slug="lpt-inst-course",
            description="Test course",
            instructor=cls.instructor,
            instrument="Guitar",
            is_published=True,
        )
        cls.lesson = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="Test Lesson",
            order=1,
            estimated_duration_minutes=30,
        )

    def setUp(self):
        self.instructor_client = Client()
        self.instructor_client.login(
            username="lpt-inst-user@test.com", password="testpass123"
        )

    def test_instructor_sees_edit_not_mark_complete(self):
        """Permission boundary: instructor sees Edit Lesson, NOT Mark Complete."""
        url = reverse(
            "lesson-detail",
            kwargs={"slug": self.course.slug, "pk": self.lesson.pk},
        )
        response = self.instructor_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        # Should see Edit Lesson
        assert "Edit Lesson" in content
        # Should NOT see progress tracking (those are for enrolled students)
        assert "Course Progress" not in content
        assert "Mark Lesson Complete" not in content


@pytest.mark.integration
class TestMarkCompleteFromLessonView(TestCase):
    """Test the HTMX mark-complete endpoint when called from lesson detail."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Mark Complete Academy",
            slug="lpt-mark-iso",
            description="Academy for mark-complete tests",
            email="lpt-mark@test.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="lpt-mark-inst",
            email="lpt-mark-inst@test.com",
            password="testpass123",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

        cls.student = User.objects.create_user(
            username="lpt-mark-student",
            email="lpt-mark-student@test.com",
            password="testpass123",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student, academy=cls.academy, role="student"
        )

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Mark Complete Course",
            slug="lpt-mark-course",
            instructor=cls.instructor,
            instrument="Piano",
            is_published=True,
        )
        cls.lesson1 = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="First Lesson",
            order=1,
            estimated_duration_minutes=30,
        )
        cls.lesson2 = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="Second Lesson",
            order=2,
            estimated_duration_minutes=45,
        )

        cls.enrollment = Enrollment.objects.create(
            student=cls.student,
            course=cls.course,
            academy=cls.academy,
            status="active",
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(
            username="lpt-mark-student@test.com", password="testpass123"
        )

    def test_mark_complete_from_lesson_returns_lesson_partial(self):
        """HTMX POST with ?from=lesson returns the lesson-complete section partial."""
        url = (
            reverse(
                "mark-lesson-complete",
                kwargs={"pk": self.enrollment.pk, "lesson_pk": self.lesson1.pk},
            )
            + "?from=lesson"
        )
        response = self.student_client.post(
            url,
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        # Should contain the lesson-complete section (not the enrollment progress row)
        assert "lesson-complete-section" in content
        # After marking complete, should show completed state
        assert "Lesson Completed" in content
        # Next lesson CTA should appear (lesson2 is next)
        assert "Continue to the next lesson" in content
        assert "Second Lesson" in content

    def test_mark_complete_without_from_returns_enrollment_partial(self):
        """HTMX POST without ?from=lesson returns the enrollment progress row partial."""
        url = reverse(
            "mark-lesson-complete",
            kwargs={"pk": self.enrollment.pk, "lesson_pk": self.lesson1.pk},
        )
        response = self.student_client.post(
            url,
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        # Should contain the enrollment progress row (not lesson-complete section)
        assert f'id="progress-{self.lesson1.pk}"' in content
        assert "lesson-complete-section" not in content

    def test_mark_complete_toggle_uncompletes_lesson(self):
        """Marking complete then marking incomplete toggles the state."""
        # First mark complete
        LessonProgress.objects.create(
            enrollment=self.enrollment,
            lesson=self.lesson1,
            academy=self.academy,
            is_completed=True,
        )
        url = (
            reverse(
                "mark-lesson-complete",
                kwargs={"pk": self.enrollment.pk, "lesson_pk": self.lesson1.pk},
            )
            + "?from=lesson"
        )
        response = self.student_client.post(
            url,
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        # Should toggle back to incomplete state
        assert "Mark Lesson Complete" in content
        # Verify DB state
        progress = LessonProgress.objects.get(
            enrollment=self.enrollment, lesson=self.lesson1
        )
        assert progress.is_completed is False

    def test_last_lesson_complete_shows_celebration(self):
        """Completing the last lesson shows celebration card."""
        # Mark lesson1 as complete first
        LessonProgress.objects.create(
            enrollment=self.enrollment,
            lesson=self.lesson1,
            academy=self.academy,
            is_completed=True,
        )
        # Now mark lesson2 (the last one) as complete via HTMX
        url = (
            reverse(
                "mark-lesson-complete",
                kwargs={"pk": self.enrollment.pk, "lesson_pk": self.lesson2.pk},
            )
            + "?from=lesson"
        )
        response = self.student_client.post(
            url,
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        # No "next lesson" CTA (this is the last lesson)
        assert "Continue to the next lesson" not in content
        # Should show congratulations
        assert "Congratulations" in content
        assert "completed all lessons" in content
