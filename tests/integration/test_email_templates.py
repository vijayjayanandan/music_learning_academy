"""Tests for HTML email templates used in assignment submission/grading and trial reminders."""

from datetime import timedelta

import pytest
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import Membership, User
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson, PracticeAssignment
from apps.enrollments.models import AssignmentSubmission, Enrollment
from apps.payments.models import AcademyTier, PlatformSubscription


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.integration
class TestAssignmentSubmittedEmail(TestCase):
    """Test that creating an AssignmentSubmission sends an HTML email to the instructor."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Email Test Academy",
            slug="email-test-sub",
            email="academy-sub@test.com",
            timezone="UTC",
        )
        cls.instructor = User.objects.create_user(
            username="email_test_instructor",
            email="instructor-sub@test.com",
            password="testpass123",
            first_name="Sarah",
            last_name="Teacher",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

        cls.student = User.objects.create_user(
            username="email_test_student",
            email="student-sub@test.com",
            password="testpass123",
            first_name="Alice",
            last_name="Learner",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(user=cls.student, academy=cls.academy, role="student")

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Guitar Basics",
            slug="guitar-basics-sub",
            instructor=cls.instructor,
            is_published=True,
        )
        cls.lesson = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="Lesson 1",
            order=1,
        )
        cls.assignment = PracticeAssignment.objects.create(
            academy=cls.academy,
            lesson=cls.lesson,
            title="Play C Major Scale",
            description="Record yourself playing the C major scale.",
            assignment_type="practice",
        )
        cls.enrollment = Enrollment.objects.create(
            academy=cls.academy,
            student=cls.student,
            course=cls.course,
        )

    def test_submission_sends_html_email_to_instructor(self):
        """Creating an AssignmentSubmission sends HTML email to the instructor."""
        mail.outbox.clear()

        AssignmentSubmission.objects.create(
            academy=self.academy,
            assignment=self.assignment,
            student=self.student,
            text_response="Here is my scale recording.",
        )

        # Filter for the submission email (not the enrollment confirmation)
        submission_emails = [m for m in mail.outbox if "New submission" in m.subject]
        assert len(submission_emails) == 1

        msg = submission_emails[0]
        assert msg.to == ["instructor-sub@test.com"]
        assert "Alice Learner" in msg.subject
        assert "Play C Major Scale" in msg.subject

        # Check HTML content is present
        assert msg.alternatives, "Email should have HTML alternative"
        html_body = msg.alternatives[0][0]
        assert "Submission Details" in html_body
        assert "Play C Major Scale" in html_body
        assert "Guitar Basics" in html_body
        assert "Review Submission" in html_body

        # Plain text fallback still present
        assert "Play C Major Scale" in msg.body

    def test_submission_email_not_sent_when_preference_disabled(self):
        """No email sent if instructor has disabled assignment_submitted preference."""
        self.instructor.email_preferences = {"assignment_submitted": False}
        self.instructor.save()
        mail.outbox.clear()

        AssignmentSubmission.objects.create(
            academy=self.academy,
            assignment=self.assignment,
            student=self.student,
            text_response="Another submission.",
        )

        submission_emails = [m for m in mail.outbox if "New submission" in m.subject]
        assert len(submission_emails) == 0

        # Restore preference
        self.instructor.email_preferences = {}
        self.instructor.save()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.integration
class TestAssignmentGradedEmail(TestCase):
    """Test that grading an AssignmentSubmission sends an HTML email to the student."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Email Grade Academy",
            slug="email-test-grade",
            email="academy-grade@test.com",
            timezone="UTC",
        )
        cls.instructor = User.objects.create_user(
            username="grade_instructor",
            email="instructor-grade@test.com",
            password="testpass123",
            first_name="David",
            last_name="Maestro",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

        cls.student = User.objects.create_user(
            username="grade_student",
            email="student-grade@test.com",
            password="testpass123",
            first_name="Bob",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(user=cls.student, academy=cls.academy, role="student")

        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Piano Fundamentals",
            slug="piano-fundamentals-grade",
            instructor=cls.instructor,
            is_published=True,
        )
        cls.lesson = Lesson.objects.create(
            academy=cls.academy,
            course=cls.course,
            title="Chords Lesson",
            order=1,
        )
        cls.assignment = PracticeAssignment.objects.create(
            academy=cls.academy,
            lesson=cls.lesson,
            title="Chord Progressions",
            description="Practice I-IV-V-I progression.",
            assignment_type="practice",
        )
        cls.enrollment = Enrollment.objects.create(
            academy=cls.academy,
            student=cls.student,
            course=cls.course,
        )

    def test_grading_sends_html_email_to_student(self):
        """Updating submission status to reviewed with reviewer sends HTML email to student."""
        mail.outbox.clear()

        # Create submission first (this triggers creation email, not grading)
        submission = AssignmentSubmission.objects.create(
            academy=self.academy,
            assignment=self.assignment,
            student=self.student,
            text_response="My chord practice.",
        )
        mail.outbox.clear()

        # Now grade the submission
        submission.status = "reviewed"
        submission.reviewed_by = self.instructor
        submission.grade = "A"
        submission.instructor_feedback = "Excellent work!"
        submission.save()

        graded_emails = [m for m in mail.outbox if "Assignment graded" in m.subject]
        assert len(graded_emails) == 1

        msg = graded_emails[0]
        assert msg.to == ["student-grade@test.com"]
        assert "Chord Progressions" in msg.subject

        # Check HTML content
        assert msg.alternatives, "Email should have HTML alternative"
        html_body = msg.alternatives[0][0]
        assert "Review Complete" in html_body
        assert "Chord Progressions" in html_body
        assert "Piano Fundamentals" in html_body
        assert "View Feedback" in html_body
        assert "A" in html_body  # grade value

        # Plain text fallback
        assert "Chord Progressions" in msg.body

    def test_grading_email_shows_see_feedback_when_no_grade(self):
        """When no grade is set, email shows 'See feedback' instead."""
        mail.outbox.clear()

        submission = AssignmentSubmission.objects.create(
            academy=self.academy,
            assignment=self.assignment,
            student=self.student,
            text_response="Another attempt.",
        )
        mail.outbox.clear()

        submission.status = "approved"
        submission.reviewed_by = self.instructor
        submission.grade = ""  # no grade
        submission.instructor_feedback = "Good job!"
        submission.save()

        graded_emails = [m for m in mail.outbox if "Assignment graded" in m.subject]
        assert len(graded_emails) == 1

        html_body = graded_emails[0].alternatives[0][0]
        assert "See feedback" in html_body


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.integration
class TestTrialReminderEmail(TestCase):
    """Test that trial reminder emails use HTML templates."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Trial Academy",
            slug="trial-reminder-test",
            email="admin-trial@test.com",
            timezone="UTC",
        )
        cls.tier = AcademyTier.objects.create(
            name="Pro",
            tier_level="pro",
            price_cents=4999,
            max_students=100,
            max_instructors=10,
            max_courses=50,
        )

    def test_trial_reminder_sends_html_email(self):
        """Trial reminder email includes HTML template content."""
        mail.outbox.clear()

        sub = PlatformSubscription.objects.create(
            academy=self.academy,
            tier=self.tier,
            status="trial",
            trial_started_at=timezone.now() - timedelta(days=7),
            trial_ends_at=timezone.now() + timedelta(days=3),
            trial_reminder_7d_sent=True,
            trial_reminder_3d_sent=False,
            trial_reminder_1d_sent=False,
        )

        from apps.payments.tasks import send_trial_reminder_emails

        count = send_trial_reminder_emails()
        assert count >= 1

        trial_emails = [m for m in mail.outbox if "days left in trial" in m.subject]
        assert len(trial_emails) >= 1

        msg = trial_emails[0]
        assert msg.to == ["admin-trial@test.com"]

        # Check HTML content
        assert msg.alternatives, "Email should have HTML alternative"
        html_body = msg.alternatives[0][0]
        assert "Trial Expiring" in html_body
        assert "Trial Academy" in html_body
        assert "Upgrade Now" in html_body
        assert "day" in html_body

        # Plain text fallback
        assert "trial" in msg.body.lower()

        # Cleanup
        sub.delete()

    def test_trial_reminder_not_resent(self):
        """Trial reminder is not sent again if already marked as sent."""
        mail.outbox.clear()

        sub = PlatformSubscription.objects.create(
            academy=self.academy,
            tier=self.tier,
            status="trial",
            trial_started_at=timezone.now() - timedelta(days=7),
            trial_ends_at=timezone.now() + timedelta(days=3),
            trial_reminder_7d_sent=True,
            trial_reminder_3d_sent=True,
            trial_reminder_1d_sent=True,
        )

        from apps.payments.tasks import send_trial_reminder_emails

        count = send_trial_reminder_emails()
        assert count == 0

        # Cleanup
        sub.delete()
