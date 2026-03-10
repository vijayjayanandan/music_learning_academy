"""Tests for student UX: empty states, priority CTA, course detail sections.

Verifies that each page shows a helpful empty state with icon, heading,
context text, and a CTA button instead of bare "No X" text.
Also tests the priority CTA system on the student dashboard and
"What You'll Learn" / prerequisites sections on course detail.
"""

from datetime import timedelta

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.enrollments.models import AssignmentSubmission, Enrollment
from apps.scheduling.models import SessionAttendance
from tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    LessonFactory,
    LiveSessionFactory,
    PracticeAssignmentFactory,
)


@pytest.mark.integration
class TestLibraryEmptyState(TestCase):
    """Library list page should show a rich empty state when no resources exist."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-library",
            description="A test academy",
            email="test-ux-library@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-ux-library",
            email="owner-ux-library@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="owner-ux-library@test.com", password="testpass123")

    def test_empty_library_returns_200(self):
        response = self.auth_client.get(reverse("library-list"))
        assert response.status_code == 200

    def test_empty_library_shows_heading_and_cta(self):
        response = self.auth_client.get(reverse("library-list"))
        content = response.content.decode()

        assert "No Resources Yet" in content
        assert "Browse Courses" in content
        assert reverse("course-list") in content

    def test_empty_library_no_bare_text(self):
        response = self.auth_client.get(reverse("library-list"))
        content = response.content.decode()

        assert "No resources found." not in content

    def test_unauthenticated_redirects(self):
        anon_client = Client()
        response = anon_client.get(reverse("library-list"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.integration
class TestNotificationsEmptyState(TestCase):
    """Notifications list page should show a rich empty state when no notifications exist."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-notifications",
            description="A test academy",
            email="test-ux-notifications@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-ux-notif",
            email="owner-ux-notif@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="owner-ux-notif@test.com", password="testpass123")

    def test_empty_notifications_returns_200(self):
        response = self.auth_client.get(reverse("notification-list"))
        assert response.status_code == 200

    def test_empty_notifications_shows_heading_and_cta(self):
        response = self.auth_client.get(reverse("notification-list"))
        content = response.content.decode()

        assert "All Caught Up" in content
        assert "Go to Dashboard" in content
        assert reverse("dashboard") in content

    def test_empty_notifications_no_bare_text(self):
        response = self.auth_client.get(reverse("notification-list"))
        content = response.content.decode()

        assert "No notifications." not in content

    def test_unauthenticated_redirects(self):
        anon_client = Client()
        response = anon_client.get(reverse("notification-list"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.integration
class TestPricingEmptyState(TestCase):
    """Pricing page should show a rich empty state when no plans exist."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-pricing",
            description="A test academy",
            email="test-ux-pricing@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-ux-pricing",
            email="owner-ux-pricing@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="owner-ux-pricing@test.com", password="testpass123")

    def test_empty_pricing_returns_200(self):
        response = self.auth_client.get(reverse("pricing"))
        assert response.status_code == 200

    def test_empty_pricing_shows_heading_and_cta(self):
        response = self.auth_client.get(reverse("pricing"))
        content = response.content.decode()

        assert "No Plans Available Yet" in content
        assert "Browse Courses" in content
        assert reverse("course-list") in content

    def test_empty_pricing_no_bare_text(self):
        response = self.auth_client.get(reverse("pricing"))
        content = response.content.decode()

        assert "No subscription plans available yet." not in content

    def test_unauthenticated_redirects(self):
        anon_client = Client()
        response = anon_client.get(reverse("pricing"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.integration
class TestCourseDetailLearningOutcomes(TestCase):
    """Course detail page should show 'What You'll Learn' when learning_outcomes is set."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-course-detail",
            description="A test academy",
            email="test-ux-course-detail@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-ux-cd",
            email="owner-ux-cd@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="owner-ux-cd@test.com", password="testpass123")

    def test_shows_what_youll_learn_with_outcomes(self):
        course = CourseFactory(
            academy=self.academy,
            instructor=self.owner,
            learning_outcomes=["Read sheet music", "Play basic chords", "Understand rhythm"],
        )
        url = reverse("course-detail", kwargs={"slug": course.slug})
        response = self.auth_client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "What You&#x27;ll Learn" in content or "What You'll Learn" in content
        assert "Read sheet music" in content
        assert "Play basic chords" in content
        assert "Understand rhythm" in content

    def test_hides_what_youll_learn_when_empty(self):
        course = CourseFactory(
            academy=self.academy,
            instructor=self.owner,
            learning_outcomes=[],
        )
        url = reverse("course-detail", kwargs={"slug": course.slug})
        response = self.auth_client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "What You&#x27;ll Learn" not in content
        assert "What You'll Learn" not in content

    def test_shows_prerequisites_when_set(self):
        course = CourseFactory(
            academy=self.academy,
            instructor=self.owner,
            prerequisites="Basic knowledge of music theory and ability to read treble clef.",
        )
        url = reverse("course-detail", kwargs={"slug": course.slug})
        response = self.auth_client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Prerequisites" in content
        assert "Basic knowledge of music theory" in content
        assert "alert-info" in content

    def test_hides_prerequisites_when_empty(self):
        course = CourseFactory(
            academy=self.academy,
            instructor=self.owner,
            prerequisites="",
        )
        url = reverse("course-detail", kwargs={"slug": course.slug})
        response = self.auth_client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "alert-info" not in content

    def test_unauthenticated_redirects(self):
        course = CourseFactory(academy=self.academy)
        url = reverse("course-detail", kwargs={"slug": course.slug})
        anon_client = Client()
        response = anon_client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.integration
class TestStudentPriorityCTA(TestCase):
    """Student dashboard shows a single highest-priority CTA card."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-priority-cta",
            description="A test academy",
            email="test-ux-priority-cta@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-ux-cta",
            email="instructor-ux-cta@test.com",
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
            username="student-ux-cta",
            email="student-ux-cta@test.com",
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

    def setUp(self):
        self.client = Client()

    def _get_dashboard(self):
        """Helper: log in as student and GET the student dashboard."""
        self.client.force_login(self.student)
        return self.client.get(reverse("student-dashboard"))

    def test_no_enrollments_shows_browse_courses_cta(self):
        """Student with no enrollments sees 'Browse Courses' CTA (priority 5)."""
        response = self._get_dashboard()
        assert response.status_code == 200
        content = response.content.decode()
        assert "Browse Courses" in content
        assert "priority-cta" in content
        cta = response.context["priority_cta"]
        assert cta["type"] == "browse"
        assert cta["color"] == "primary"
        assert reverse("course-list") in cta["url"]

    def test_active_enrollment_shows_continue_learning_cta(self):
        """Student with active enrollment (incomplete lessons) sees 'Continue Learning' CTA (priority 4)."""
        course = CourseFactory(academy=self.academy, instructor=self.instructor)
        LessonFactory(course=course, academy=self.academy)
        EnrollmentFactory(academy=self.academy, student=self.student, course=course)

        response = self._get_dashboard()
        assert response.status_code == 200
        cta = response.context["priority_cta"]
        assert cta["type"] == "continue"
        assert cta["title"] == "Continue Learning"
        assert course.title in cta["subtitle"]

    def test_imminent_session_shows_join_session_cta(self):
        """Student with a session starting within 30 min sees 'Join Session Now' CTA (priority 1)."""
        # Also create an enrollment so priority 4 would otherwise apply
        course = CourseFactory(academy=self.academy, instructor=self.instructor)
        LessonFactory(course=course, academy=self.academy)
        EnrollmentFactory(academy=self.academy, student=self.student, course=course)

        # Create a session starting 10 minutes from now
        now = timezone.now()
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=now + timedelta(minutes=10),
            scheduled_end=now + timedelta(minutes=70),
            status="scheduled",
        )
        # Register the student for this session
        SessionAttendance.objects.create(
            academy=self.academy,
            session=session,
            student=self.student,
            status="registered",
        )

        response = self._get_dashboard()
        assert response.status_code == 200
        cta = response.context["priority_cta"]
        assert cta["type"] == "session"
        assert cta["title"] == "Join Session Now"
        assert session.title in cta["subtitle"]
        assert cta["color"] == "accent"

    def test_revision_needed_shows_revise_cta(self):
        """Student with assignment needing revision sees 'Revise & Resubmit' CTA (priority 2)."""
        course = CourseFactory(academy=self.academy, instructor=self.instructor)
        lesson = LessonFactory(course=course, academy=self.academy)
        enrollment = EnrollmentFactory(
            academy=self.academy, student=self.student, course=course
        )
        assignment = PracticeAssignmentFactory(
            academy=self.academy,
            lesson=lesson,
            due_date=timezone.now() + timedelta(days=7),
        )
        # Create a submission that needs revision
        AssignmentSubmission.objects.create(
            academy=self.academy,
            assignment=assignment,
            student=self.student,
            status="needs_revision",
            text_response="My attempt",
        )

        response = self._get_dashboard()
        assert response.status_code == 200
        cta = response.context["priority_cta"]
        assert cta["type"] == "revise"
        assert cta["title"] == "Revise & Resubmit"
        assert cta["color"] == "warning"
        assert reverse("enrollment-detail", args=[enrollment.pk]) in cta["url"]

    def test_urgent_assignment_shows_submit_cta(self):
        """Student with assignment due within 48h sees 'Submit Assignment' CTA (priority 3)."""
        course = CourseFactory(academy=self.academy, instructor=self.instructor)
        lesson = LessonFactory(course=course, academy=self.academy)
        EnrollmentFactory(
            academy=self.academy, student=self.student, course=course
        )
        # Assignment due in 24 hours (within the 48h threshold)
        PracticeAssignmentFactory(
            academy=self.academy,
            lesson=lesson,
            due_date=timezone.now() + timedelta(hours=24),
        )

        response = self._get_dashboard()
        assert response.status_code == 200
        cta = response.context["priority_cta"]
        assert cta["type"] == "submit"
        assert cta["title"] == "Submit Assignment"
        assert cta["color"] == "info"

    def test_session_beats_continue_learning(self):
        """Priority 1 (session) takes precedence over priority 4 (continue learning)."""
        course = CourseFactory(academy=self.academy, instructor=self.instructor)
        LessonFactory(course=course, academy=self.academy)
        EnrollmentFactory(academy=self.academy, student=self.student, course=course)

        now = timezone.now()
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=now + timedelta(minutes=5),
            scheduled_end=now + timedelta(minutes=65),
            status="scheduled",
        )
        SessionAttendance.objects.create(
            academy=self.academy,
            session=session,
            student=self.student,
            status="registered",
        )

        response = self._get_dashboard()
        cta = response.context["priority_cta"]
        # Session (priority 1) beats continue learning (priority 4)
        assert cta["type"] == "session"

    def test_far_future_session_does_not_trigger_cta(self):
        """Session more than 30 minutes away does NOT trigger 'Join Session Now'."""
        now = timezone.now()
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            scheduled_start=now + timedelta(hours=3),
            scheduled_end=now + timedelta(hours=4),
            status="scheduled",
        )
        SessionAttendance.objects.create(
            academy=self.academy,
            session=session,
            student=self.student,
            status="registered",
        )

        response = self._get_dashboard()
        cta = response.context["priority_cta"]
        # Should fall through to browse (no enrollments)
        assert cta["type"] == "browse"

    def test_unauthenticated_redirects_to_login(self):
        """Unauthenticated user is redirected to login."""
        anon_client = Client()
        response = anon_client.get(reverse("student-dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.integration
class TestProfileLearningPreferences(TestCase):
    """Profile pages show Learning Preferences section for students only."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-profile",
            description="A test academy",
            email="test-ux-profile@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-ux-profile",
            email="owner-ux-profile@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="instructor-ux-profile",
            email="instructor-ux-profile@test.com",
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
            username="student-ux-profile",
            email="student-ux-profile@test.com",
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

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="owner-ux-profile@test.com", password="testpass123")

    def test_student_profile_shows_learning_preferences(self):
        """Student profile page shows the Learning Preferences card."""
        # Set up learning preferences on the membership
        membership = self.student.memberships.get(academy=self.academy)
        membership.skill_level = "intermediate"
        membership.learning_goal = "Master classical piano"
        membership.instruments = ["Piano", "Violin"]
        membership.save()

        client = Client()
        client.force_login(self.student)
        response = client.get(reverse("profile"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Learning Preferences" in content
        assert "Intermediate" in content
        assert "Master classical piano" in content
        assert "Piano" in content
        assert "Violin" in content

    def test_student_profile_shows_not_set_defaults(self):
        """Student profile shows 'Not set' for empty learning preferences."""
        # Reset learning preferences to defaults
        membership = self.student.memberships.get(academy=self.academy)
        membership.learning_goal = ""
        membership.instruments = []
        membership.save()

        client = Client()
        client.force_login(self.student)
        response = client.get(reverse("profile"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Learning Preferences" in content
        assert "Not set" in content

    def test_owner_profile_does_not_show_learning_preferences(self):
        """Owner profile page does NOT show the Learning Preferences section."""
        response = self.auth_client.get(reverse("profile"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Learning Preferences" not in content

    def test_instructor_profile_does_not_show_learning_preferences(self):
        """Instructor profile page does NOT show the Learning Preferences section."""
        client = Client()
        client.force_login(self.instructor)
        response = client.get(reverse("profile"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Learning Preferences" not in content

    def test_student_profile_edit_shows_learning_preferences_fields(self):
        """Student profile edit page shows skill_level, learning_goal, and instruments fields."""
        client = Client()
        client.force_login(self.student)
        response = client.get(reverse("profile-edit"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Learning Preferences" in content
        assert 'name="skill_level"' in content
        assert 'name="learning_goal"' in content
        assert 'name="instruments"' in content

    def test_owner_profile_edit_does_not_show_learning_preferences(self):
        """Owner profile edit page does NOT show Learning Preferences fields."""
        response = self.auth_client.get(reverse("profile-edit"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Learning Preferences" not in content
        assert 'name="skill_level"' not in content

    def test_student_can_update_learning_preferences(self):
        """Student can update learning preferences via profile edit form."""
        client = Client()
        client.force_login(self.student)
        response = client.post(reverse("profile-edit"), {
            "first_name": self.student.first_name,
            "last_name": self.student.last_name,
            "timezone": "UTC",
            "skill_level": "advanced",
            "learning_goal": "Perform at a recital",
            "instruments": ["Guitar", "Voice"],
        })

        assert response.status_code == 302  # redirect to profile on success

        # Verify membership was updated
        membership = self.student.memberships.get(academy=self.academy)
        membership.refresh_from_db()
        assert membership.skill_level == "advanced"
        assert membership.learning_goal == "Perform at a recital"
        assert membership.instruments == ["Guitar", "Voice"]

    def test_student_can_clear_instruments(self):
        """Student can clear all instruments by submitting none checked."""
        # Set some instruments first
        membership = self.student.memberships.get(academy=self.academy)
        membership.instruments = ["Piano"]
        membership.save()

        client = Client()
        client.force_login(self.student)
        response = client.post(reverse("profile-edit"), {
            "first_name": self.student.first_name,
            "last_name": self.student.last_name,
            "timezone": "UTC",
            "skill_level": "beginner",
            "learning_goal": "",
            # No instruments submitted
        })

        assert response.status_code == 302
        membership.refresh_from_db()
        assert membership.instruments == []

    def test_profile_edit_uses_academy_instruments(self):
        """Profile edit page uses academy's primary_instruments for checkbox options."""
        client = Client()
        client.force_login(self.student)
        response = client.get(reverse("profile-edit"))
        content = response.content.decode()

        # The test academy fixture has primary_instruments = ["Piano", "Guitar"]
        assert response.status_code == 200
        assert "Piano" in content
        assert "Guitar" in content


@pytest.mark.integration
class TestSessionRegisterCopyImprovement(TestCase):
    """Session detail page uses 'Reserve Your Spot' instead of 'Register'
    and shows helper text explaining the two-step flow (register then join)."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-session-register",
            description="A test academy",
            email="test-ux-session-register@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.instructor = User.objects.create_user(
            username="instructor-ux-sr",
            email="instructor-ux-sr@test.com",
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
            username="student-ux-sr",
            email="student-ux-sr@test.com",
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

    def setUp(self):
        self.client = Client()

    def test_session_detail_shows_reserve_your_spot(self):
        """Unregistered student sees 'Reserve Your Spot' button (not 'Register')."""
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            status="scheduled",
        )
        self.client.force_login(self.student)
        url = reverse("session-detail", args=[session.pk])
        response = self.client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Reserve Your Spot" in content

    def test_session_detail_shows_reminder_helper_text(self):
        """Session detail page contains helper text about reminders and the Join button."""
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            status="scheduled",
        )
        self.client.force_login(self.student)
        url = reverse("session-detail", args=[session.pk])
        response = self.client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Reserve your spot to receive a reminder" in content
        assert "Join" in content

    def test_session_detail_register_button_helper_text(self):
        """Register button area shows helper text about receiving reminders."""
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            status="scheduled",
        )
        self.client.force_login(self.student)
        url = reverse("session-detail", args=[session.pk])
        response = self.client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Register to receive reminders" in content

    def test_session_detail_no_plain_register_button(self):
        """Session detail page does NOT have a button labelled just 'Register'."""
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            status="scheduled",
        )
        self.client.force_login(self.student)
        url = reverse("session-detail", args=[session.pk])
        response = self.client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        # The word "Register" may appear in helper text (e.g. "Register to receive reminders"),
        # but it must NOT appear as standalone button text.
        # Check that the button specifically says "Reserve Your Spot"
        assert ">Reserve Your Spot</button>" in content
        # Ensure there is no button with just "Register" text
        assert ">Register</button>" not in content

    def test_unauthenticated_redirects(self):
        """Unauthenticated user is redirected to login."""
        session = LiveSessionFactory(
            academy=self.academy,
            instructor=self.instructor,
            status="scheduled",
        )
        url = reverse("session-detail", args=[session.pk])
        anon_client = Client()
        response = anon_client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.integration
class TestStudentSidebarCollapsibleGroups(TestCase):
    """Student sidebar shows 5 always-visible items + 2 collapsible groups.

    The student sidebar is restructured to reduce cognitive overload:
    - Always visible: Dashboard, Courses, Live Sessions, Practice, My Progress
    - Collapsible "Music Tools": Metronome, Tuner, Notation, Ear Training, Recordings, Library
    - Collapsible "Account & Billing": My Subscriptions, My Packages, Pricing, Payment History
    - Owner/instructor sidebar remains unchanged
    """

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="test-ux-sidebar",
            description="A test academy",
            email="test-ux-sidebar@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-ux-sidebar",
            email="owner-ux-sidebar@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-ux-sidebar",
            email="student-ux-sidebar@test.com",
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

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(username="owner-ux-sidebar@test.com", password="testpass123")
        self.student_client = Client()
        self.student_client.force_login(self.student)

    def _get_sidebar_html(self, client, user):
        """Helper: log in and GET dashboard, return the decoded HTML content."""
        client.force_login(user)
        response = client.get(reverse("dashboard"), follow=True)
        assert response.status_code == 200
        return response.content.decode()

    def _get_student_dashboard_content(self):
        """Helper: GET the student dashboard (following redirect) and return decoded HTML."""
        response = self.student_client.get(reverse("dashboard"), follow=True)
        assert response.status_code == 200
        return response.content.decode()

    def test_student_sidebar_has_dashboard_link(self):
        """Student sidebar contains 'Dashboard' as an always-visible item."""
        content = self._get_student_dashboard_content()
        assert reverse("dashboard") in content
        assert "Dashboard" in content

    def test_student_sidebar_has_courses_link(self):
        """Student sidebar contains 'Courses' as an always-visible item."""
        content = self._get_student_dashboard_content()
        assert reverse("course-list") in content
        assert "Courses" in content

    def test_student_sidebar_has_live_sessions_link(self):
        """Student sidebar contains 'Live Sessions' as an always-visible item."""
        content = self._get_student_dashboard_content()
        assert reverse("schedule-list") in content
        assert "Live Sessions" in content

    def test_student_sidebar_has_practice_link(self):
        """Student sidebar contains 'Practice' as an always-visible item."""
        content = self._get_student_dashboard_content()
        assert reverse("practice-log-list") in content
        assert "Practice" in content

    def test_student_sidebar_has_my_progress_link(self):
        """Student sidebar contains 'My Progress' as an always-visible item."""
        content = self._get_student_dashboard_content()
        assert reverse("enrollment-list") in content
        assert "My Progress" in content

    def test_student_sidebar_has_account_billing_collapsible(self):
        """Student sidebar contains 'Account & Billing' collapsible group."""
        content = self._get_student_dashboard_content()
        assert "Account &amp; Billing" in content or "Account & Billing" in content
        assert "<details" in content
        assert "<summary" in content

    def test_student_sidebar_account_billing_contains_subscriptions(self):
        """Account & Billing group contains 'My Subscriptions' link."""
        content = self._get_student_dashboard_content()
        assert reverse("my-subscriptions") in content
        assert "My Subscriptions" in content

    def test_student_sidebar_account_billing_contains_packages(self):
        """Account & Billing group contains 'My Packages' link."""
        content = self._get_student_dashboard_content()
        assert reverse("my-packages") in content
        assert "My Packages" in content

    def test_student_sidebar_account_billing_contains_pricing(self):
        """Account & Billing group contains 'Pricing' link."""
        content = self._get_student_dashboard_content()
        assert reverse("pricing") in content
        assert "Pricing" in content

    def test_student_sidebar_account_billing_contains_payment_history(self):
        """Account & Billing group contains 'Payment History' link."""
        content = self._get_student_dashboard_content()
        assert reverse("payment-history") in content
        assert "Payment History" in content

    def test_student_sidebar_has_music_tools_collapsible(self):
        """Student sidebar contains 'Music Tools' collapsible group (not flat menu-title)."""
        content = self._get_student_dashboard_content()
        assert "Music Tools" in content
        # Student sidebar uses <details>/<summary> pattern, not flat menu-title
        assert "<details" in content

    def test_student_sidebar_has_book_session_link(self):
        """Student sidebar contains 'Book Session' link next to Live Sessions."""
        content = self._get_student_dashboard_content()
        assert reverse("book-session") in content
        assert "Book Session" in content

    def test_owner_sidebar_unchanged_has_manage_section(self):
        """Owner sidebar still has the 'Manage' section with management items."""
        response = self.auth_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert response.status_code == 200
        # Owner should see Manage section
        assert "Manage" in content
        assert reverse("course-create") in content
        assert reverse("session-create") in content

    def test_owner_sidebar_unchanged_has_academy_section(self):
        """Owner sidebar still has the 'Academy' section with members, settings, etc."""
        response = self.auth_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert response.status_code == 200
        assert "Members" in content
        assert "Settings" in content
        assert "Coupons" in content
        assert "Payouts" in content

    def test_owner_sidebar_has_flat_account_section(self):
        """Owner sidebar still has the flat 'Account' section (not collapsible)."""
        response = self.auth_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert response.status_code == 200
        # Owner sidebar should show Account as a menu-title (flat), not inside <details>
        assert "Billing" in content
        assert reverse("pricing") in content

    def test_student_sidebar_does_not_have_manage_section(self):
        """Student sidebar does NOT contain 'Manage' section items like '+ New Course'."""
        content = self._get_student_dashboard_content()
        assert reverse("course-create") not in content
        assert reverse("session-create") not in content

    def test_all_student_sidebar_links_resolve(self):
        """All links in the student sidebar return 200 (no broken URLs)."""
        urls_to_check = [
            reverse("dashboard"),
            reverse("course-list"),
            reverse("schedule-list"),
            reverse("book-session"),
            reverse("practice-log-list"),
            reverse("enrollment-list"),
            reverse("message-inbox"),
            reverse("my-subscriptions"),
            reverse("my-packages"),
            reverse("pricing"),
            reverse("payment-history"),
        ]
        for url in urls_to_check:
            response = self.student_client.get(url, follow=True)
            assert response.status_code == 200, f"URL {url} returned {response.status_code}"
