"""Tests for FEAT-013 through FEAT-022 (Release 2: Retention)."""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy, Announcement
from apps.courses.models import Course, Lesson, PracticeAssignment
from apps.enrollments.models import Enrollment, AssignmentSubmission
from apps.practice.models import PracticeLog, PracticeGoal
from apps.scheduling.models import LiveSession, SessionNote


@pytest.mark.integration
class TestPracticeJournal:
    """FEAT-013: Practice journal / daily log."""

    def test_practice_log_model_fields(self, db):
        assert hasattr(PracticeLog, "student")
        assert hasattr(PracticeLog, "date")
        assert hasattr(PracticeLog, "duration_minutes")
        assert hasattr(PracticeLog, "instrument")
        assert hasattr(PracticeLog, "pieces_worked_on")
        assert hasattr(PracticeLog, "notes")
        assert hasattr(PracticeLog, "course")

    def test_practice_log_str(self, student_user, academy):
        log = PracticeLog.objects.create(
            student=student_user,
            academy=academy,
            date=date.today(),
            duration_minutes=30,
            instrument="Piano",
        )
        assert "Piano" in str(log)
        assert "30min" in str(log)

    def test_practice_log_list_view_loads(self, auth_client):
        response = auth_client.get(reverse("practice-log-list"))
        assert response.status_code == 200

    def test_create_practice_log(self, auth_client, owner_user, academy):
        response = auth_client.post(reverse("practice-log-create"), {
            "date": date.today().isoformat(),
            "duration_minutes": 45,
            "instrument": "Guitar",
            "pieces_worked_on": "Stairway to Heaven",
            "notes": "Worked on solo section",
        })
        assert response.status_code == 302
        assert PracticeLog.objects.filter(student=owner_user).exists()


@pytest.mark.integration
class TestPracticeStreaksAndGoals:
    """FEAT-014: Practice streaks and goals."""

    def test_practice_goal_model(self, db):
        assert hasattr(PracticeGoal, "weekly_minutes_target")
        assert hasattr(PracticeGoal, "is_active")

    def test_set_goal(self, auth_client, owner_user, academy):
        response = auth_client.post(reverse("practice-set-goal"), {
            "weekly_minutes_target": 180,
        })
        assert response.status_code == 302
        goal = PracticeGoal.objects.get(student=owner_user, academy=academy)
        assert goal.weekly_minutes_target == 180
        assert goal.is_active is True

    def test_streak_calculation(self, auth_client, owner_user, academy):
        # Create logs for 3 consecutive days including today
        # Use timezone.now().date() to match the view's date calculation
        today = timezone.now().date()
        for i in range(3):
            PracticeLog.objects.create(
                student=owner_user,
                academy=academy,
                date=today - timedelta(days=i),
                duration_minutes=30,
                instrument="Piano",
            )
        response = auth_client.get(reverse("practice-log-list"))
        assert response.status_code == 200
        assert response.context["streak"] == 3

    def test_weekly_minutes_aggregation(self, auth_client, owner_user, academy):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        PracticeLog.objects.create(
            student=owner_user, academy=academy,
            date=week_start, duration_minutes=60, instrument="Piano",
        )
        PracticeLog.objects.create(
            student=owner_user, academy=academy,
            date=week_start + timedelta(days=1), duration_minutes=45, instrument="Piano",
        )
        response = auth_client.get(reverse("practice-log-list"))
        assert response.context["weekly_minutes"] == 105


@pytest.mark.integration
class TestRubricGrading:
    """FEAT-016: Rubric-based grading."""

    def test_submission_has_rubric_scores_field(self, db):
        assert hasattr(AssignmentSubmission, "rubric_scores")

    def test_rubric_scores_default_empty(self, instructor_user, academy, db):
        course = Course.objects.create(
            title="Test Course", slug="test-rubric-course",
            description="Test", instructor=instructor_user, academy=academy,
            instrument="Piano",
        )
        lesson = Lesson.objects.create(
            course=course, title="Lesson 1", academy=academy, order=1,
        )
        assignment = PracticeAssignment.objects.create(
            lesson=lesson, title="Play scales", description="Play all major scales",
            academy=academy,
        )
        sub = AssignmentSubmission.objects.create(
            assignment=assignment, student=instructor_user, academy=academy,
        )
        assert sub.rubric_scores == {}

    def test_rubric_scores_stores_json(self, instructor_user, academy, db):
        course = Course.objects.create(
            title="Rubric Course", slug="rubric-course",
            description="Test", instructor=instructor_user, academy=academy,
            instrument="Piano",
        )
        lesson = Lesson.objects.create(
            course=course, title="Lesson 1", academy=academy, order=1,
        )
        assignment = PracticeAssignment.objects.create(
            lesson=lesson, title="Performance", description="Play sonata",
            academy=academy,
        )
        sub = AssignmentSubmission.objects.create(
            assignment=assignment, student=instructor_user, academy=academy,
            rubric_scores={"tone": 8, "rhythm": 7, "technique": 9, "expression": 8},
        )
        sub.refresh_from_db()
        assert sub.rubric_scores["tone"] == 8
        assert sub.rubric_scores["expression"] == 8


@pytest.mark.integration
class TestSessionNotes:
    """FEAT-017: Session notes (instructor private notes)."""

    def test_session_note_model_fields(self, db):
        assert hasattr(SessionNote, "session")
        assert hasattr(SessionNote, "instructor")
        assert hasattr(SessionNote, "student")
        assert hasattr(SessionNote, "content")

    def test_create_session_note(self, instructor_user, student_user, academy, db):
        session = LiveSession.objects.create(
            title="Piano Lesson",
            instructor=instructor_user,
            academy=academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            jitsi_room_name="test-room-notes",
        )
        note = SessionNote.objects.create(
            session=session,
            instructor=instructor_user,
            student=student_user,
            academy=academy,
            content="Student needs to work on finger positioning",
        )
        assert "Note by" in str(note)
        assert note.content == "Student needs to work on finger positioning"


@pytest.mark.integration
class TestRecurringSessions:
    """FEAT-018: Recurring sessions."""

    def test_livesession_has_recurring_fields(self, db):
        assert hasattr(LiveSession, "is_recurring")
        assert hasattr(LiveSession, "recurrence_rule")
        assert hasattr(LiveSession, "recurrence_parent")

    def test_recurring_session_creation(self, instructor_user, academy, db):
        session = LiveSession.objects.create(
            title="Weekly Piano Lesson",
            instructor=instructor_user,
            academy=academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            jitsi_room_name="test-recurring",
            is_recurring=True,
            recurrence_rule="weekly",
        )
        assert session.is_recurring is True
        assert session.recurrence_rule == "weekly"

    def test_recurrence_parent_relationship(self, instructor_user, academy, db):
        parent = LiveSession.objects.create(
            title="Parent Session",
            instructor=instructor_user,
            academy=academy,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            jitsi_room_name="parent-session",
            is_recurring=True,
            recurrence_rule="weekly",
        )
        child = LiveSession.objects.create(
            title="Child Session",
            instructor=instructor_user,
            academy=academy,
            scheduled_start=timezone.now() + timedelta(weeks=1),
            scheduled_end=timezone.now() + timedelta(weeks=1, hours=1),
            jitsi_room_name="child-session",
            recurrence_parent=parent,
        )
        assert child.recurrence_parent == parent
        assert parent.recurrence_instances.count() == 1


@pytest.mark.integration
class TestCoursePrerequisites:
    """FEAT-019: Course prerequisites."""

    def test_course_has_prerequisite_courses(self, db):
        assert hasattr(Course, "prerequisite_courses")

    def test_add_prerequisite(self, instructor_user, academy, db):
        course1 = Course.objects.create(
            title="Piano Basics", slug="piano-basics",
            description="Beginner", instructor=instructor_user, academy=academy,
            instrument="Piano",
        )
        course2 = Course.objects.create(
            title="Piano Intermediate", slug="piano-intermediate",
            description="Intermediate", instructor=instructor_user, academy=academy,
            instrument="Piano",
        )
        course2.prerequisite_courses.add(course1)
        assert course1 in course2.prerequisite_courses.all()
        assert course2 in course1.dependent_courses.all()


@pytest.mark.integration
class TestCertificateOfCompletion:
    """FEAT-020: Certificate of completion."""

    def test_certificate_requires_completed_enrollment(self, auth_client, owner_user, academy, db):
        course = Course.objects.create(
            title="Cert Course", slug="cert-course",
            description="Test", instructor=owner_user, academy=academy,
            instrument="Piano",
        )
        enrollment = Enrollment.objects.create(
            student=owner_user, course=course, academy=academy, status="active",
        )
        # Should 404 since enrollment is not completed
        response = auth_client.get(reverse("certificate", args=[enrollment.pk]))
        assert response.status_code == 404

    def test_certificate_renders_for_completed(self, auth_client, owner_user, academy, db):
        course = Course.objects.create(
            title="Completed Course", slug="completed-course",
            description="Test", instructor=owner_user, academy=academy,
            instrument="Piano",
        )
        enrollment = Enrollment.objects.create(
            student=owner_user, course=course, academy=academy, status="completed",
        )
        response = auth_client.get(reverse("certificate", args=[enrollment.pk]))
        assert response.status_code == 200
        assert b"Certificate" in response.content or b"certificate" in response.content


@pytest.mark.integration
class TestAcademyAnnouncements:
    """FEAT-021: Academy announcements."""

    def test_announcement_model_fields(self, db):
        assert hasattr(Announcement, "title")
        assert hasattr(Announcement, "body")
        assert hasattr(Announcement, "is_pinned")
        assert hasattr(Announcement, "author")

    def test_announcement_list_loads(self, auth_client, academy):
        response = auth_client.get(reverse("academy-announcements", args=[academy.slug]))
        assert response.status_code == 200

    def test_create_announcement(self, auth_client, owner_user, academy):
        response = auth_client.post(
            reverse("academy-announcements", args=[academy.slug]),
            {"title": "Welcome!", "body": "Hello everyone", "is_pinned": "on"},
        )
        assert response.status_code == 302
        ann = Announcement.objects.get(academy=academy)
        assert ann.title == "Welcome!"
        assert ann.is_pinned is True

    def test_announcements_ordering(self, owner_user, academy, db):
        Announcement.objects.create(
            academy=academy, author=owner_user, title="Regular", body="...",
        )
        Announcement.objects.create(
            academy=academy, author=owner_user, title="Pinned", body="...", is_pinned=True,
        )
        announcements = Announcement.objects.filter(academy=academy)
        assert announcements[0].is_pinned is True


@pytest.mark.integration
class TestGroupChat:
    """FEAT-022: Group chat per course."""

    def test_course_chat_loads(self, auth_client, owner_user, academy, db):
        course = Course.objects.create(
            title="Chat Course", slug="chat-course",
            description="Test", instructor=owner_user, academy=academy,
            instrument="Piano",
        )
        response = auth_client.get(reverse("course-chat", args=[course.slug]))
        assert response.status_code == 200

    def test_post_chat_message(self, auth_client, owner_user, academy, db):
        from apps.notifications.models import ChatMessage

        course = Course.objects.create(
            title="Chat Course 2", slug="chat-course-2",
            description="Test", instructor=owner_user, academy=academy,
            instrument="Piano",
        )
        response = auth_client.post(
            reverse("course-chat", args=[course.slug]),
            {"message": "Hello class!"},
        )
        assert response.status_code == 302
        assert ChatMessage.objects.filter(sender=owner_user, message="Hello class!").exists()
