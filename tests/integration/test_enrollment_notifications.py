"""Integration tests for instructor enrollment notifications (email + in-app)."""

import pytest
from django.core import mail
from django.test import TestCase

from apps.academies.models import Academy
from apps.accounts.models import Membership, User
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.notifications.models import Notification


@pytest.mark.integration
class TestInstructorEnrollmentNotification(TestCase):
    """Tests that enrolling a student triggers HTML email and in-app notification for the instructor."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Notification Test Academy",
            slug="enroll-notif-test-iso",
        )
        cls.instructor = User.objects.create_user(
            username="instructor-enroll-notif",
            email="instructor-enroll-notif@test.com",
            password="testpass123",
            first_name="Sarah",
            last_name="Melody",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

        cls.student = User.objects.create_user(
            username="student-enroll-notif",
            email="student-enroll-notif@test.com",
            password="testpass123",
            first_name="Alice",
            last_name="Harmony",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(user=cls.student, academy=cls.academy, role="student")

        cls.course = Course.objects.create(
            title="Piano Fundamentals",
            slug="piano-fundamentals-enroll-notif",
            description="Learn piano basics",
            instructor=cls.instructor,
            academy=cls.academy,
            instrument="Piano",
            difficulty_level="beginner",
            is_published=True,
        )

    def test_enrollment_sends_html_email_to_instructor(self):
        """Happy path: creating an enrollment sends an HTML email to the instructor."""
        mail.outbox.clear()

        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            academy=self.academy,
        )

        # Instructor gets an email (student also gets one, so at least 1 for instructor)
        instructor_emails = [m for m in mail.outbox if self.instructor.email in m.to]
        assert len(instructor_emails) == 1

        email = instructor_emails[0]
        # Check subject
        assert "New enrollment:" in email.subject
        assert "Alice Harmony" in email.subject
        assert "Piano Fundamentals" in email.subject

        # Check HTML content is present
        assert email.alternatives, "Email should have HTML alternative"
        html_content = email.alternatives[0][0]
        assert "Alice Harmony" in html_content
        assert "student-enroll-notif@test.com" in html_content
        assert "Piano Fundamentals" in html_content
        assert "View Course" in html_content
        # Check the info card content
        assert "Piano" in html_content  # instrument
        assert "Beginner" in html_content  # difficulty level display
        assert "student" in html_content.lower()  # enrolled count text

        # Plain-text fallback is also present
        assert "Alice Harmony" in email.body

    def test_enrollment_creates_inapp_notification_for_instructor(self):
        """Happy path: creating an enrollment creates an in-app Notification for the instructor."""
        Notification.objects.filter(recipient=self.instructor).delete()

        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            academy=self.academy,
        )

        notifications = Notification.objects.filter(
            recipient=self.instructor,
            notification_type="enrollment",
        )
        assert notifications.count() == 1

        notif = notifications.first()
        assert "Piano Fundamentals" in notif.title
        assert "Alice Harmony" in notif.message
        assert notif.academy == self.academy
        assert f"/courses/{self.course.slug}/" in notif.link
        assert notif.is_read is False

    def test_instructor_email_disabled_still_gets_notification(self):
        """Boundary: instructor with enrollment_created email disabled still gets in-app notification."""
        # Create a separate instructor with email preference disabled
        instructor_no_email = User.objects.create_user(
            username="instructor-no-email-notif",
            email="instructor-no-email-notif@test.com",
            password="testpass123",
            first_name="Bob",
            last_name="Rhythm",
            email_preferences={"enrollment_created": False},
        )
        instructor_no_email.current_academy = self.academy
        instructor_no_email.save()
        Membership.objects.create(
            user=instructor_no_email, academy=self.academy, role="instructor"
        )

        course2 = Course.objects.create(
            title="Guitar Basics",
            slug="guitar-basics-enroll-notif",
            description="Learn guitar",
            instructor=instructor_no_email,
            academy=self.academy,
            instrument="Guitar",
            is_published=True,
        )

        mail.outbox.clear()
        Notification.objects.filter(recipient=instructor_no_email).delete()

        Enrollment.objects.create(
            student=self.student,
            course=course2,
            academy=self.academy,
        )

        # No email should be sent to this instructor
        instructor_emails = [
            m for m in mail.outbox if instructor_no_email.email in m.to
        ]
        assert len(instructor_emails) == 0

        # But in-app notification should still be created
        notifications = Notification.objects.filter(
            recipient=instructor_no_email,
            notification_type="enrollment",
        )
        assert notifications.count() == 1
        assert "Guitar Basics" in notifications.first().title

    def test_enrolled_count_in_email_is_accurate(self):
        """The enrolled_count in the email context should reflect the current count including the new enrollment."""
        mail.outbox.clear()

        # Create a second student and enroll them first
        student2 = User.objects.create_user(
            username="student2-enroll-notif",
            email="student2-enroll-notif@test.com",
            password="testpass123",
            first_name="Carol",
            last_name="Beat",
        )
        student2.current_academy = self.academy
        student2.save()
        Membership.objects.create(user=student2, academy=self.academy, role="student")

        course3 = Course.objects.create(
            title="Drums 101",
            slug="drums-101-enroll-notif",
            description="Drum basics",
            instructor=self.instructor,
            academy=self.academy,
            instrument="Drums",
            is_published=True,
        )

        # First enrollment
        Enrollment.objects.create(
            student=student2,
            course=course3,
            academy=self.academy,
        )
        mail.outbox.clear()

        # Second enrollment
        Enrollment.objects.create(
            student=self.student,
            course=course3,
            academy=self.academy,
        )

        instructor_emails = [m for m in mail.outbox if self.instructor.email in m.to]
        assert len(instructor_emails) == 1

        html_content = instructor_emails[0].alternatives[0][0]
        # Should say "2 students" (both enrollments active)
        assert "2 students" in html_content
