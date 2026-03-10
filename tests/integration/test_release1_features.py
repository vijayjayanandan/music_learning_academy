"""Tests for FEAT-005 through FEAT-012 (Release 1 remainder)."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.notifications.models import Message


@pytest.mark.integration
class TestCalendarView(TestCase):
    """FEAT-005: Visual calendar view."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Calendar Academy",
            slug="rel1-calendar-iso",
            email="calendar-iso@academy.com",
            timezone="UTC",
        )
        cls.owner = User.objects.create_user(
            username="calendar-owner-iso",
            email="calendar-owner-iso@test.com",
            password="testpass123",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="calendar-owner-iso@test.com", password="testpass123"
        )

    def test_schedule_list_renders_calendar(self):
        response = self.auth_client.get(reverse("schedule-list"))
        assert response.status_code == 200
        assert b"fullcalendar" in response.content.lower()
        assert b"calendar" in response.content.lower()

    def test_session_events_api(self):
        response = self.auth_client.get(reverse("session-events-api"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"


@pytest.mark.integration
class TestTimezoneSupport(TestCase):
    """FEAT-006: User timezone support."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Timezone Academy",
            slug="rel1-timezone-iso",
            email="timezone-iso@academy.com",
            timezone="UTC",
        )
        cls.owner = User.objects.create_user(
            username="timezone-owner-iso",
            email="timezone-owner-iso@test.com",
            password="testpass123",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="timezone-owner-iso@test.com", password="testpass123"
        )
        # Re-fetch owner to get a clean instance for each test
        self.owner = User.objects.get(pk=self.__class__.owner.pk)

    def test_user_has_timezone_field(self):
        assert hasattr(self.owner, "timezone")
        assert self.owner.timezone == "UTC"

    def test_profile_form_includes_timezone(self):
        from apps.accounts.forms import ProfileForm

        form = ProfileForm()
        assert "timezone" in form.fields

    def test_timezone_middleware_activates(self):
        self.owner.timezone = "US/Eastern"
        self.owner.save(update_fields=["timezone"])
        response = self.auth_client.get(reverse("dashboard"))
        assert response.status_code in [200, 302]


@pytest.mark.integration
class TestSessionReminders(TestCase):
    """FEAT-007: Session reminders via email."""

    @classmethod
    def setUpTestData(cls):
        # No user/academy needed — these tests only inspect models and run a command.
        pass

    def test_livesession_has_reminder_flags(self):
        from apps.scheduling.models import LiveSession

        assert hasattr(LiveSession, "reminder_24h_sent")
        assert hasattr(LiveSession, "reminder_1h_sent")

    def test_send_reminders_command_runs(self):
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command("send_session_reminders", stdout=out)
        assert "reminders" in out.getvalue().lower()


@pytest.mark.integration
class TestRecordingUpload(TestCase):
    """FEAT-008: Student recording upload."""

    @classmethod
    def setUpTestData(cls):
        # No user/academy needed — these tests only inspect model structure.
        pass

    def test_submission_has_recording_field(self):
        from apps.enrollments.models import AssignmentSubmission

        assert hasattr(AssignmentSubmission, "recording")

    def test_recording_properties(self):
        from apps.enrollments.models import AssignmentSubmission

        sub = AssignmentSubmission()
        assert sub.is_audio_recording is False
        assert sub.is_video_recording is False
        assert sub.recording_size_display == ""


@pytest.mark.integration
class TestInAppMessaging(TestCase):
    """FEAT-009: In-app messaging."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Messaging Academy",
            slug="rel1-messaging-iso",
            email="messaging-iso@academy.com",
            timezone="UTC",
        )
        cls.owner = User.objects.create_user(
            username="messaging-owner-iso",
            email="messaging-owner-iso@test.com",
            password="testpass123",
            first_name="Messaging",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="messaging-owner-iso@test.com", password="testpass123"
        )

    def test_inbox_loads(self):
        response = self.auth_client.get(reverse("message-inbox"))
        assert response.status_code == 200
        assert b"Messages" in response.content

    def test_sent_redirects_to_inbox(self):
        response = self.auth_client.get(reverse("message-sent"))
        assert response.status_code == 302

    def test_compose_loads(self):
        response = self.auth_client.get(reverse("message-compose"))
        assert response.status_code == 200
        assert b"New Message" in response.content

    def test_send_message(self):
        # Create a second user to send to (test-specific, rolled back after test)
        recipient = User.objects.create_user(
            email="msg_recipient_rel1@test.com",
            username="msg-recipient-rel1-iso",
            password="testpass123",
        )
        Membership.objects.create(
            user=recipient, academy=self.__class__.academy, role="student"
        )

        response = self.auth_client.post(
            reverse("message-compose"),
            {
                "recipient": recipient.pk,
                "subject": "Test Message",
                "body": "Hello!",
            },
        )
        assert response.status_code == 302
        assert Message.objects.filter(
            sender=self.__class__.owner, recipient=recipient
        ).exists()

    def test_unread_count(self):
        response = self.auth_client.get(reverse("message-unread-count"))
        assert response.status_code == 200


@pytest.mark.integration
class TestBrandedSignup(TestCase):
    """FEAT-011: Academy-branded signup link."""

    @classmethod
    def setUpTestData(cls):
        # Academy for load/404 tests — no owner needed for basic page load.
        cls.academy = Academy.objects.create(
            name="Test Academy",
            slug="rel1-branded-iso",
        )
        # Academy with owner for email notification test.
        cls.email_academy = Academy.objects.create(
            name="Email Academy",
            slug="rel1-email-academy-iso",
        )
        cls.email_owner = User.objects.create_user(
            username="rel1-email-academy-owner-iso",
            email="owner@rel1-email-academy-iso.com",
            password="testpass123",
            first_name="Academy",
            last_name="Owner",
        )
        Membership.objects.create(
            user=cls.email_owner, academy=cls.email_academy, role="owner"
        )
        # Academy for signup test — students are created per test, so we only
        # need the academy in setUpTestData.
        cls.signup_academy = Academy.objects.create(
            name="Signup Academy",
            slug="rel1-signup-academy-iso",
        )

    def setUp(self):
        self.client = Client()

    def test_branded_signup_page_loads(self):
        response = self.client.get(
            reverse("branded-signup", args=[self.__class__.academy.slug])
        )
        assert response.status_code == 200
        assert b"Test Academy" in response.content

    def test_branded_signup_creates_student(self):
        response = self.client.post(
            reverse("branded-signup", args=[self.__class__.signup_academy.slug]),
            {
                "email": "newstudent_rel1@test.com",
                "password1": "complexpass123!",
                "password2": "complexpass123!",
                "date_of_birth": "2000-01-01",
                "accept_terms": "on",
            },
        )
        assert response.status_code == 302
        user = User.objects.get(email="newstudent_rel1@test.com")
        assert Membership.objects.filter(
            user=user, academy=self.__class__.signup_academy, role="student"
        ).exists()

    def test_branded_signup_sends_email_to_owner(self):
        """BUG-013: Branded signup should send notification email to academy owner(s)."""
        from django.core import mail
        from apps.notifications.models import Notification

        response = self.client.post(
            reverse("branded-signup", args=[self.__class__.email_academy.slug]),
            {
                "email": "newstudent_email_rel1@example.com",
                "password1": "complexpass123!",
                "password2": "complexpass123!",
                "date_of_birth": "2000-01-01",
                "accept_terms": "on",
            },
        )
        assert response.status_code == 302

        # Verify email was sent to the owner
        assert len(mail.outbox) == 1
        email_msg = mail.outbox[0]
        assert email_msg.to == ["owner@rel1-email-academy-iso.com"]
        assert "Email Academy" in email_msg.subject
        assert "New member" in email_msg.subject
        # Without first/last name, the notification uses the email address
        assert "newstudent_email_rel1@example.com" in email_msg.body

        # Verify in-app notification was created for the owner
        notifications = Notification.objects.filter(
            recipient=self.__class__.email_owner, academy=self.__class__.email_academy
        )
        assert notifications.count() == 1
        assert "newstudent_email_rel1@example.com" in notifications.first().message
        assert "branded signup" in notifications.first().message

    def test_branded_signup_invalid_slug_returns_404(self):
        """Boundary: branded signup for a non-existent academy slug returns 404."""
        response = self.client.get(
            reverse("branded-signup", args=["nonexistent-academy"])
        )
        assert response.status_code == 404

        response = self.client.post(
            reverse("branded-signup", args=["nonexistent-academy"]),
            {
                "email": "ghost@example.com",
                "password1": "complexpass123!",
                "password2": "complexpass123!",
                "date_of_birth": "2000-01-01",
                "accept_terms": "on",
            },
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestEmailNotifications(TestCase):
    """FEAT-012: Email notifications."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Email Notif Academy",
            slug="rel1-emailnotif-iso",
            email="emailnotif-iso@academy.com",
            timezone="UTC",
        )
        cls.owner = User.objects.create_user(
            username="emailnotif-owner-iso",
            email="emailnotif-owner-iso@test.com",
            password="testpass123",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        # Re-fetch to get a mutable instance (setUpTestData objects are shared/read-only).
        self.owner = User.objects.get(pk=self.__class__.owner.pk)

    def test_user_has_email_preferences(self):
        assert hasattr(self.owner, "email_preferences")

    def test_wants_email_defaults_true(self):
        assert self.owner.wants_email("enrollment_created") is True
        assert self.owner.wants_email("assignment_graded") is True

    def test_wants_email_respects_preference(self):
        self.owner.email_preferences = {"enrollment_created": False}
        self.owner.save()
        assert self.owner.wants_email("enrollment_created") is False
        assert self.owner.wants_email("assignment_graded") is True


@pytest.mark.integration
class TestMobileResponsive(TestCase):
    """FEAT-010: Mobile responsive (base template checks)."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Mobile Academy",
            slug="rel1-mobile-iso",
            email="mobile-iso@academy.com",
            timezone="UTC",
        )
        cls.owner = User.objects.create_user(
            username="mobile-owner-iso",
            email="mobile-owner-iso@test.com",
            password="testpass123",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="mobile-owner-iso@test.com", password="testpass123"
        )

    def test_base_template_has_viewport_meta(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200
        assert b"viewport" in response.content

    def test_base_template_has_drawer(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        assert b"drawer" in response.content

    def test_sidebar_has_messages_link(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        assert b"Messages" in response.content
