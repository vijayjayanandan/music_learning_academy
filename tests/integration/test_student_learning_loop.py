"""Tests for the student learning loop features:
- Task 1: Lesson prev/next navigation
- Task 2: Post-enrollment redirect to first lesson
- Task 3: "Continue where you left off" on student dashboard
- Task 4: Lesson status display on enrollment detail
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson, PracticeAssignment
from apps.enrollments.models import Enrollment, LessonProgress, AssignmentSubmission


# ============================================================
# Task 1: Lesson prev/next navigation
# ============================================================


@pytest.mark.integration
class TestLessonNavigation(TestCase):
    """Tests for prev/next lesson navigation on lesson detail page."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="sll-nav-iso",
            description="A test academy",
            email="sll-nav-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="sll-nav-owner",
            email="sll-nav-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="sll-nav-instructor",
            email="sll-nav-instructor@test.com",
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

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Test Course",
            slug="sll-nav-test-course",
            description="A course for testing",
            instructor=cls.instructor,
            instrument="Piano",
            is_published=True,
        )
        cls.lesson1 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson One", order=1,
            estimated_duration_minutes=30,
        )
        cls.lesson2 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Two", order=2,
            estimated_duration_minutes=45,
        )
        cls.lesson3 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Three", order=3,
            estimated_duration_minutes=60,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="sll-nav-owner@test.com", password="testpass123")

    def test_lesson_shows_position_indicator(self):
        """Lesson page should show 'Lesson X of Y' indicator."""
        url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson2.pk})
        response = self.auth_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Lesson 2 of 3" in content

    def test_first_lesson_has_no_prev(self):
        """First lesson should not have a Previous Lesson link."""
        url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson1.pk})
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Previous Lesson" not in content
        assert "Next Lesson" in content

    def test_middle_lesson_has_both_nav(self):
        """Middle lesson should have both Previous and Next links."""
        url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson2.pk})
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Previous Lesson" in content
        assert "Next Lesson" in content

    def test_last_lesson_shows_back_to_course(self):
        """Last lesson should show 'Back to Course' instead of 'Next Lesson'."""
        url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson3.pk})
        response = self.auth_client.get(url)
        content = response.content.decode()
        assert "Previous Lesson" in content
        assert "Next Lesson" not in content
        assert "Back to Course" in content

    def test_context_has_navigation_data(self):
        """View context should include prev_lesson, next_lesson, lesson_number, total_lessons."""
        url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson2.pk})
        response = self.auth_client.get(url)
        assert response.context["lesson_number"] == 2
        assert response.context["total_lessons"] == 3
        assert response.context["prev_lesson"].pk == self.lesson1.pk
        assert response.context["next_lesson"].pk == self.lesson3.pk

    def test_unauthenticated_cannot_view_lesson(self):
        """Unauthenticated user should be redirected to login."""
        anon_client = Client()
        url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson1.pk})
        response = anon_client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


# ============================================================
# Task 2: Post-enrollment redirect to first lesson
# ============================================================


@pytest.mark.integration
class TestPostEnrollmentRedirect(TestCase):
    """Tests for redirect to first lesson after enrollment."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="sll-enroll-iso",
            description="A test academy",
            email="sll-enroll-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="sll-enroll-instructor",
            email="sll-enroll-instructor@test.com",
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
            username="sll-enroll-student",
            email="sll-enroll-student@test.com",
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

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Test Course",
            slug="sll-enroll-test-course",
            description="A course for testing",
            instructor=cls.instructor,
            instrument="Piano",
            is_published=True,
        )
        cls.lesson1 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson One", order=1,
            estimated_duration_minutes=30,
        )
        cls.lesson2 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Two", order=2,
            estimated_duration_minutes=45,
        )
        cls.lesson3 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Three", order=3,
            estimated_duration_minutes=60,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(username="sll-enroll-student@test.com", password="testpass123")

    def test_enroll_redirects_to_first_lesson(self):
        """After enrolling, student should be redirected to the first lesson."""
        url = reverse("enroll", kwargs={"slug": self.course.slug})
        response = self.student_client.post(url)
        expected_url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson1.pk})
        assert response.status_code == 302
        assert expected_url in response.url

    def test_enroll_htmx_returns_hx_redirect(self):
        """HTMX enrollment should return HX-Redirect header to first lesson."""
        url = reverse("enroll", kwargs={"slug": self.course.slug})
        response = self.student_client.post(url, HTTP_HX_REQUEST="true")
        assert response.status_code == 204
        expected_url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson1.pk})
        assert response["HX-Redirect"] == expected_url

    def test_enroll_no_lessons_falls_back(self):
        """If course has no lessons, enrollment should fall back to course detail."""
        course = Course.objects.create(
            academy=self.academy, title="Empty Course", slug="sll-enroll-empty-course",
            description="No lessons", instructor=self.instructor,
            instrument="Piano", is_published=True,
        )
        url = reverse("enroll", kwargs={"slug": course.slug})
        response = self.student_client.post(url)
        assert response.status_code == 302
        assert reverse("course-detail", kwargs={"slug": course.slug}) in response.url

    def test_unauthenticated_cannot_enroll(self):
        """Unauthenticated user should not be able to enroll."""
        anon_client = Client()
        url = reverse("enroll", kwargs={"slug": self.course.slug})
        response = anon_client.post(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


# ============================================================
# Task 3: "Continue where you left off" on student dashboard
# ============================================================


@pytest.mark.integration
class TestContinueLearning(TestCase):
    """Tests for 'Continue where you left off' on student dashboard."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="sll-continue-iso",
            description="A test academy",
            email="sll-continue-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="sll-continue-instructor",
            email="sll-continue-instructor@test.com",
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
            username="sll-continue-student",
            email="sll-continue-student@test.com",
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

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Test Course",
            slug="sll-continue-test-course",
            description="A course for testing",
            instructor=cls.instructor,
            instrument="Piano",
            is_published=True,
        )
        cls.lesson1 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson One", order=1,
            estimated_duration_minutes=30,
        )
        cls.lesson2 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Two", order=2,
            estimated_duration_minutes=45,
        )
        cls.lesson3 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Three", order=3,
            estimated_duration_minutes=60,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(username="sll-continue-student@test.com", password="testpass123")

    def test_continue_learning_shows_first_incomplete_lesson(self):
        """Dashboard should show the first incomplete lesson."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        # Mark first lesson as complete
        LessonProgress.objects.create(
            academy=self.academy, enrollment=enrollment, lesson=self.lesson1, is_completed=True,
        )

        url = reverse("student-dashboard")
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Continue Learning" in content
        assert self.course.title in content
        assert self.lesson2.title in content

    def test_continue_learning_context_data(self):
        """Context should include continue_learning dict with correct data."""
        Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )

        url = reverse("student-dashboard")
        response = self.student_client.get(url)
        cl = response.context["continue_learning"]
        assert cl is not None
        assert cl["course_title"] == self.course.title
        assert cl["lesson_title"] == self.lesson1.title
        assert cl["progress_percent"] == 0
        expected_url = reverse("lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson1.pk})
        assert cl["lesson_url"] == expected_url

    def test_no_continue_learning_when_no_enrollments(self):
        """Dashboard should not show continue learning when student has no enrollments."""
        url = reverse("student-dashboard")
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Continue Learning" not in content

    def test_unauthenticated_redirects_from_dashboard(self):
        """Unauthenticated user should be redirected to login."""
        anon_client = Client()
        url = reverse("student-dashboard")
        response = anon_client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


# ============================================================
# Task 4: Lesson status display on enrollment detail
# ============================================================


@pytest.mark.integration
class TestLessonStatusDisplay(TestCase):
    """Tests for lesson status badges on enrollment detail page."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="sll-status-iso",
            description="A test academy",
            email="sll-status-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="sll-status-instructor",
            email="sll-status-instructor@test.com",
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
            username="sll-status-student",
            email="sll-status-student@test.com",
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

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Test Course",
            slug="sll-status-test-course",
            description="A course for testing",
            instructor=cls.instructor,
            instrument="Piano",
            is_published=True,
        )
        cls.lesson1 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson One", order=1,
            estimated_duration_minutes=30,
        )
        cls.lesson2 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Two", order=2,
            estimated_duration_minutes=45,
        )
        cls.lesson3 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Three", order=3,
            estimated_duration_minutes=60,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(username="sll-status-student@test.com", password="testpass123")

    def test_not_started_shows_badge(self):
        """Lessons with no progress should show 'Not started' badge."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        content = response.content.decode()
        assert "Not started" in content

    def test_completed_shows_badge(self):
        """Completed lessons should show 'Complete' badge."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        LessonProgress.objects.create(
            academy=self.academy, enrollment=enrollment, lesson=self.lesson1, is_completed=True,
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        content = response.content.decode()
        assert "Complete" in content

    def test_submitted_shows_badge(self):
        """Lessons with submitted assignments should show 'Submitted' badge."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        assignment = PracticeAssignment.objects.create(
            academy=self.academy, lesson=self.lesson1, title="Practice Scales",
            description="Practice all scales", assignment_type="practice",
        )
        AssignmentSubmission.objects.create(
            academy=self.academy, assignment=assignment, student=self.student,
            text_response="Done", status="submitted",
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        content = response.content.decode()
        assert "Submitted" in content

    def test_needs_revision_shows_badge(self):
        """Lessons with needs_revision submissions should show 'Needs Revision' badge."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        assignment = PracticeAssignment.objects.create(
            academy=self.academy, lesson=self.lesson1, title="Practice Scales",
            description="Practice all scales", assignment_type="practice",
        )
        AssignmentSubmission.objects.create(
            academy=self.academy, assignment=assignment, student=self.student,
            text_response="Done", status="needs_revision",
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        content = response.content.decode()
        assert "Needs Revision" in content

    def test_reviewed_shows_badge(self):
        """Lessons with reviewed submissions should show 'Reviewed' badge."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        assignment = PracticeAssignment.objects.create(
            academy=self.academy, lesson=self.lesson1, title="Practice Scales",
            description="Practice all scales", assignment_type="practice",
        )
        AssignmentSubmission.objects.create(
            academy=self.academy, assignment=assignment, student=self.student,
            text_response="Done", status="reviewed",
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        content = response.content.decode()
        assert "Reviewed" in content

    def test_other_student_cannot_view_enrollment(self):
        """Another student should not be able to view someone else's enrollment."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        other_user = User.objects.create_user(
            username="sll-status-other", email="sll-status-other@test.com", password="testpass123",
        )
        other_user.current_academy = self.academy
        other_user.save()
        Membership.objects.create(user=other_user, academy=self.academy, role="student")
        other_client = Client()
        other_client.login(username="sll-status-other@test.com", password="testpass123")
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = other_client.get(url)
        assert response.status_code == 404

    def test_lesson_data_in_context(self):
        """Context lesson_data items should have lesson and is_completed fields."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        lesson_data = response.context["lesson_data"]
        assert len(lesson_data) == 3
        for item in lesson_data:
            assert "lesson" in item
            assert "is_completed" in item
            assert item["is_completed"] is False


# ============================================================
# Task 5: Start/Continue Lesson CTA on enrollment detail
# ============================================================


@pytest.mark.integration
class TestEnrollmentDetailCTA(TestCase):
    """Tests for the Start/Continue Lesson CTA card on enrollment detail page."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="sll-cta-iso",
            description="A test academy",
            email="sll-cta-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="sll-cta-instructor",
            email="sll-cta-instructor@test.com",
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
            username="sll-cta-student",
            email="sll-cta-student@test.com",
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

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Test Course",
            slug="sll-cta-test-course",
            description="A course for testing",
            instructor=cls.instructor,
            instrument="Piano",
            is_published=True,
        )
        cls.lesson1 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson One", order=1,
            estimated_duration_minutes=30,
        )
        cls.lesson2 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Two", order=2,
            estimated_duration_minutes=45,
        )
        cls.lesson3 = Lesson.objects.create(
            academy=cls.academy, course=cls.course, title="Lesson Three", order=3,
            estimated_duration_minutes=60,
        )

    def setUp(self):
        self.student_client = Client()
        self.student_client.login(username="sll-cta-student@test.com", password="testpass123")

    def test_zero_progress_shows_start_cta(self):
        """At 0% progress, enrollment detail should show 'Start First Lesson' CTA."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Ready to Start?" in content
        assert "Start First Lesson" in content
        # Should link to the first lesson
        first_lesson_url = reverse(
            "lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson1.pk}
        )
        assert first_lesson_url in content

    def test_zero_progress_context_has_first_incomplete_lesson(self):
        """At 0% progress, context should have first_incomplete_lesson set to first lesson."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        assert response.context["first_incomplete_lesson"].pk == self.lesson1.pk
        assert response.context["progress_percent"] == 0

    def test_partial_progress_shows_continue_cta(self):
        """At partial progress, enrollment detail should show 'Continue Lesson' CTA."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        # Mark first lesson complete
        LessonProgress.objects.create(
            academy=self.academy, enrollment=enrollment, lesson=self.lesson1, is_completed=True,
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Continue Where You Left Off" in content
        assert "Continue Lesson" in content
        assert self.lesson2.title in content
        # Should NOT show start CTA
        assert "Start First Lesson" not in content
        # Should link to second lesson (first incomplete)
        second_lesson_url = reverse(
            "lesson-detail", kwargs={"slug": self.course.slug, "pk": self.lesson2.pk}
        )
        assert second_lesson_url in content

    def test_partial_progress_context_has_correct_lesson(self):
        """At partial progress, first_incomplete_lesson should be the next incomplete lesson."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        # Mark first two lessons complete
        LessonProgress.objects.create(
            academy=self.academy, enrollment=enrollment, lesson=self.lesson1, is_completed=True,
        )
        LessonProgress.objects.create(
            academy=self.academy, enrollment=enrollment, lesson=self.lesson2, is_completed=True,
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        # Should point to the third lesson (only remaining incomplete)
        assert response.context["first_incomplete_lesson"].pk == self.lesson3.pk
        assert response.context["progress_percent"] == 66  # 2/3 = 66%

    def test_complete_progress_shows_congratulations(self):
        """At 100% progress, enrollment detail should show congratulations message."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        # Mark all lessons complete
        for lesson in [self.lesson1, self.lesson2, self.lesson3]:
            LessonProgress.objects.create(
                academy=self.academy, enrollment=enrollment, lesson=lesson, is_completed=True,
            )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Congratulations!" in content
        assert "completed all lessons" in content
        assert "Browse More Courses" in content
        # Should NOT show start or continue CTAs
        assert "Start First Lesson" not in content
        assert "Continue Lesson" not in content

    def test_complete_progress_context_has_no_incomplete_lesson(self):
        """At 100% progress, first_incomplete_lesson should be None."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        for lesson in [self.lesson1, self.lesson2, self.lesson3]:
            LessonProgress.objects.create(
                academy=self.academy, enrollment=enrollment, lesson=lesson, is_completed=True,
            )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = self.student_client.get(url)
        assert response.context["first_incomplete_lesson"] is None
        assert response.context["progress_percent"] == 100

    def test_other_student_cannot_see_cta(self):
        """Another student should not be able to view enrollment detail (and thus the CTA)."""
        enrollment = Enrollment.objects.create(
            academy=self.academy, student=self.student, course=self.course,
        )
        other_user = User.objects.create_user(
            username="sll-cta-other", email="sll-cta-other@test.com", password="testpass123",
        )
        other_user.current_academy = self.academy
        other_user.save()
        Membership.objects.create(user=other_user, academy=self.academy, role="student")
        other_client = Client()
        other_client.login(username="sll-cta-other@test.com", password="testpass123")
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = other_client.get(url)
        assert response.status_code == 404
