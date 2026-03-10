"""Tests for FEAT-013 through FEAT-022 (Release 2: Retention)."""

import pytest
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy, Announcement
from apps.courses.models import Course, Lesson, PracticeAssignment
from apps.enrollments.models import Enrollment, AssignmentSubmission
from apps.practice.models import PracticeLog, PracticeGoal
from apps.scheduling.models import LiveSession, SessionNote


@pytest.mark.integration
class TestPracticeJournal(TestCase):
    """FEAT-013: Practice journal / daily log."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-practicelog-iso",
            description="A test academy",
            email="rel2-practicelog@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="rel2-practicelog-owner",
            email="rel2-practicelog-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="rel2-practicelog-student",
            email="rel2-practicelog-student@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
            instruments=["Piano"],
            skill_level="beginner",
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="rel2-practicelog-owner@test.com", password="testpass123"
        )

    def test_practice_log_model_fields(self):
        assert hasattr(PracticeLog, "student")
        assert hasattr(PracticeLog, "date")
        assert hasattr(PracticeLog, "duration_minutes")
        assert hasattr(PracticeLog, "instrument")
        assert hasattr(PracticeLog, "pieces_worked_on")
        assert hasattr(PracticeLog, "notes")
        assert hasattr(PracticeLog, "course")

    def test_practice_log_str(self):
        log = PracticeLog.objects.create(
            student=self.student,
            academy=self.academy,
            date=date.today(),
            duration_minutes=30,
            instrument="Piano",
        )
        assert "Piano" in str(log)
        assert "30min" in str(log)

    def test_practice_log_list_view_loads(self):
        response = self.auth_client.get(reverse("practice-log-list"))
        assert response.status_code == 200

    def test_create_practice_log(self):
        response = self.auth_client.post(
            reverse("practice-log-create"),
            {
                "date": date.today().isoformat(),
                "duration_minutes": 45,
                "instrument": "Guitar",
                "pieces_worked_on": "Stairway to Heaven",
                "notes": "Worked on solo section",
            },
        )
        assert response.status_code == 302
        assert PracticeLog.objects.filter(student=self.owner).exists()


@pytest.mark.integration
class TestPracticeStreaksAndGoals(TestCase):
    """FEAT-014: Practice streaks and goals."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-streaks-iso",
            description="A test academy",
            email="rel2-streaks@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="rel2-streaks-owner",
            email="rel2-streaks-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="rel2-streaks-owner@test.com", password="testpass123"
        )

    def test_practice_goal_model(self):
        assert hasattr(PracticeGoal, "weekly_minutes_target")
        assert hasattr(PracticeGoal, "is_active")

    def test_set_goal(self):
        response = self.auth_client.post(
            reverse("practice-set-goal"),
            {
                "weekly_minutes_target": 180,
            },
        )
        assert response.status_code == 302
        goal = PracticeGoal.objects.get(student=self.owner, academy=self.academy)
        assert goal.weekly_minutes_target == 180
        assert goal.is_active is True

    def test_streak_calculation(self):
        # Create logs for 3 consecutive days including today
        # Use timezone.now().date() to match the view's date calculation
        today = timezone.now().date()
        for i in range(3):
            PracticeLog.objects.create(
                student=self.owner,
                academy=self.academy,
                date=today - timedelta(days=i),
                duration_minutes=30,
                instrument="Piano",
            )
        response = self.auth_client.get(reverse("practice-log-list"))
        assert response.status_code == 200
        assert response.context["streak"] == 3

    def test_weekly_minutes_aggregation(self):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        PracticeLog.objects.create(
            student=self.owner,
            academy=self.academy,
            date=week_start,
            duration_minutes=60,
            instrument="Piano",
        )
        PracticeLog.objects.create(
            student=self.owner,
            academy=self.academy,
            date=week_start + timedelta(days=1),
            duration_minutes=45,
            instrument="Piano",
        )
        response = self.auth_client.get(reverse("practice-log-list"))
        assert response.context["weekly_minutes"] == 105


@pytest.mark.integration
class TestRubricGrading(TestCase):
    """FEAT-016: Rubric-based grading."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-rubric-iso",
            description="A test academy",
            email="rel2-rubric@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="rel2-rubric-instructor",
            email="rel2-rubric-instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor,
            academy=cls.academy,
            role="instructor",
            instruments=["Piano"],
        )

    def test_submission_has_rubric_scores_field(self):
        assert hasattr(AssignmentSubmission, "rubric_scores")

    def test_rubric_scores_default_empty(self):
        course = Course.objects.create(
            title="Test Course",
            slug="rel2-rubric-course",
            description="Test",
            instructor=self.instructor,
            academy=self.academy,
            instrument="Piano",
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Lesson 1",
            academy=self.academy,
            order=1,
        )
        assignment = PracticeAssignment.objects.create(
            lesson=lesson,
            title="Play scales",
            description="Play all major scales",
            academy=self.academy,
        )
        sub = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=self.instructor,
            academy=self.academy,
        )
        assert sub.rubric_scores == {}

    def test_rubric_scores_stores_json(self):
        course = Course.objects.create(
            title="Rubric Course",
            slug="rel2-rubric-course-2",
            description="Test",
            instructor=self.instructor,
            academy=self.academy,
            instrument="Piano",
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Lesson 1",
            academy=self.academy,
            order=1,
        )
        assignment = PracticeAssignment.objects.create(
            lesson=lesson,
            title="Performance",
            description="Play sonata",
            academy=self.academy,
        )
        sub = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=self.instructor,
            academy=self.academy,
            rubric_scores={"tone": 8, "rhythm": 7, "technique": 9, "expression": 8},
        )
        sub.refresh_from_db()
        assert sub.rubric_scores["tone"] == 8
        assert sub.rubric_scores["expression"] == 8


@pytest.mark.integration
class TestSessionNotes(TestCase):
    """FEAT-017: Session notes (instructor private notes)."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-sessionnotes-iso",
            description="A test academy",
            email="rel2-sessionnotes@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="rel2-sessionnotes-instructor",
            email="rel2-sessionnotes-instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
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
            username="rel2-sessionnotes-student",
            email="rel2-sessionnotes-student@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
            instruments=["Piano"],
            skill_level="beginner",
        )

    def test_session_note_model_fields(self):
        assert hasattr(SessionNote, "session")
        assert hasattr(SessionNote, "instructor")
        assert hasattr(SessionNote, "student")
        assert hasattr(SessionNote, "content")

    def test_create_session_note(self):
        session = LiveSession.objects.create(
            title="Piano Lesson",
            instructor=self.instructor,
            academy=self.academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            room_name="rel2-notes-room",
        )
        note = SessionNote.objects.create(
            session=session,
            instructor=self.instructor,
            student=self.student,
            academy=self.academy,
            content="Student needs to work on finger positioning",
        )
        assert "Note by" in str(note)
        assert note.content == "Student needs to work on finger positioning"


@pytest.mark.integration
class TestRecurringSessions(TestCase):
    """FEAT-018: Recurring sessions."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-recurring-iso",
            description="A test academy",
            email="rel2-recurring@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="rel2-recurring-instructor",
            email="rel2-recurring-instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor,
            academy=cls.academy,
            role="instructor",
            instruments=["Piano"],
        )

    def setUp(self):
        self.client = Client()
        self.client.login(
            username="rel2-recurring-instructor@test.com", password="testpass123"
        )

    def test_livesession_has_recurring_fields(self):
        assert hasattr(LiveSession, "is_recurring")
        assert hasattr(LiveSession, "recurrence_rule")
        assert hasattr(LiveSession, "recurrence_parent")

    def test_recurring_session_creation(self):
        session = LiveSession.objects.create(
            title="Weekly Piano Lesson",
            instructor=self.instructor,
            academy=self.academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            room_name="rel2-test-recurring",
            is_recurring=True,
            recurrence_rule="weekly",
        )
        assert session.is_recurring is True
        assert session.recurrence_rule == "weekly"

    def test_recurrence_parent_relationship(self):
        parent = LiveSession.objects.create(
            title="Parent Session",
            instructor=self.instructor,
            academy=self.academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            room_name="rel2-parent-session",
            is_recurring=True,
            recurrence_rule="weekly",
        )
        child = LiveSession.objects.create(
            title="Child Session",
            instructor=self.instructor,
            academy=self.academy,
            scheduled_start=timezone.now() + timedelta(weeks=1),
            scheduled_end=timezone.now() + timedelta(weeks=1, hours=1),
            room_name="rel2-child-session",
            recurrence_parent=parent,
        )
        assert child.recurrence_parent == parent
        assert parent.recurrence_instances.count() == 1


@pytest.mark.integration
class TestCoursePrerequisites(TestCase):
    """FEAT-019: Course prerequisites."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-prereq-iso",
            description="A test academy",
            email="rel2-prereq@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.instructor = User.objects.create_user(
            username="rel2-prereq-instructor",
            email="rel2-prereq-instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor,
            academy=cls.academy,
            role="instructor",
            instruments=["Piano"],
        )

    def test_course_has_prerequisite_courses(self):
        assert hasattr(Course, "prerequisite_courses")

    def test_add_prerequisite(self):
        course1 = Course.objects.create(
            title="Piano Basics",
            slug="rel2-piano-basics",
            description="Beginner",
            instructor=self.instructor,
            academy=self.academy,
            instrument="Piano",
        )
        course2 = Course.objects.create(
            title="Piano Intermediate",
            slug="rel2-piano-intermediate",
            description="Intermediate",
            instructor=self.instructor,
            academy=self.academy,
            instrument="Piano",
        )
        course2.prerequisite_courses.add(course1)
        assert course1 in course2.prerequisite_courses.all()
        assert course2 in course1.dependent_courses.all()


@pytest.mark.integration
class TestCertificateOfCompletion(TestCase):
    """FEAT-020: Certificate of completion."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-certificate-iso",
            description="A test academy",
            email="rel2-certificate@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="rel2-certificate-owner",
            email="rel2-certificate-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="rel2-certificate-owner@test.com", password="testpass123"
        )

    def test_certificate_requires_completed_enrollment(self):
        course = Course.objects.create(
            title="Cert Course",
            slug="rel2-cert-course",
            description="Test",
            instructor=self.owner,
            academy=self.academy,
            instrument="Piano",
        )
        enrollment = Enrollment.objects.create(
            student=self.owner,
            course=course,
            academy=self.academy,
            status="active",
        )
        # Should 404 since enrollment is not completed
        response = self.auth_client.get(reverse("certificate", args=[enrollment.pk]))
        assert response.status_code == 404

    def test_certificate_renders_for_completed(self):
        course = Course.objects.create(
            title="Completed Course",
            slug="rel2-completed-course",
            description="Test",
            instructor=self.owner,
            academy=self.academy,
            instrument="Piano",
        )
        enrollment = Enrollment.objects.create(
            student=self.owner,
            course=course,
            academy=self.academy,
            status="completed",
        )
        response = self.auth_client.get(reverse("certificate", args=[enrollment.pk]))
        assert response.status_code == 200
        assert b"Certificate" in response.content or b"certificate" in response.content


@pytest.mark.integration
class TestAcademyAnnouncements(TestCase):
    """FEAT-021: Academy announcements."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-announce-iso",
            description="A test academy",
            email="rel2-announce@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="rel2-announce-owner",
            email="rel2-announce-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="rel2-announce-owner@test.com", password="testpass123"
        )

    def test_announcement_model_fields(self):
        assert hasattr(Announcement, "title")
        assert hasattr(Announcement, "body")
        assert hasattr(Announcement, "is_pinned")
        assert hasattr(Announcement, "author")

    def test_announcement_list_loads(self):
        response = self.auth_client.get(
            reverse("academy-announcements", args=[self.academy.slug])
        )
        assert response.status_code == 200

    def test_create_announcement(self):
        response = self.auth_client.post(
            reverse("academy-announcements", args=[self.academy.slug]),
            {"title": "Welcome!", "body": "Hello everyone", "is_pinned": "on"},
        )
        assert response.status_code == 302
        ann = Announcement.objects.get(academy=self.academy)
        assert ann.title == "Welcome!"
        assert ann.is_pinned is True

    def test_announcements_ordering(self):
        Announcement.objects.create(
            academy=self.academy,
            author=self.owner,
            title="Regular",
            body="...",
        )
        Announcement.objects.create(
            academy=self.academy,
            author=self.owner,
            title="Pinned",
            body="...",
            is_pinned=True,
        )
        announcements = Announcement.objects.filter(academy=self.academy)
        assert announcements[0].is_pinned is True


@pytest.mark.integration
class TestGroupChat(TestCase):
    """FEAT-022: Group chat per course."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Test Music Academy",
            slug="rel2-groupchat-iso",
            description="A test academy",
            email="rel2-groupchat@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="rel2-groupchat-owner",
            email="rel2-groupchat-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="rel2-groupchat-owner@test.com", password="testpass123"
        )

    def test_course_chat_loads(self):
        course = Course.objects.create(
            title="Chat Course",
            slug="rel2-chat-course",
            description="Test",
            instructor=self.owner,
            academy=self.academy,
            instrument="Piano",
        )
        response = self.auth_client.get(reverse("course-chat", args=[course.slug]))
        assert response.status_code == 200

    def test_post_chat_message(self):
        from apps.notifications.models import ChatMessage

        course = Course.objects.create(
            title="Chat Course 2",
            slug="rel2-chat-course-2",
            description="Test",
            instructor=self.owner,
            academy=self.academy,
            instrument="Piano",
        )
        response = self.auth_client.post(
            reverse("course-chat", args=[course.slug]),
            {"message": "Hello class!"},
        )
        assert response.status_code == 302
        assert ChatMessage.objects.filter(
            sender=self.owner, message="Hello class!"
        ).exists()
