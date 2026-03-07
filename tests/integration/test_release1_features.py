"""Tests for FEAT-005 through FEAT-012 (Release 1 remainder)."""
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User, Membership
from apps.notifications.models import Message


@pytest.mark.integration
class TestCalendarView:
    """FEAT-005: Visual calendar view."""

    def test_schedule_list_renders_calendar(self, auth_client):
        response = auth_client.get(reverse("schedule-list"))
        assert response.status_code == 200
        assert b"fullcalendar" in response.content.lower()
        assert b"calendar" in response.content.lower()

    def test_session_events_api(self, auth_client, db):
        response = auth_client.get(reverse("session-events-api"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"


@pytest.mark.integration
class TestTimezoneSupport:
    """FEAT-006: User timezone support."""

    def test_user_has_timezone_field(self, owner_user):
        assert hasattr(owner_user, "timezone")
        assert owner_user.timezone == "UTC"

    def test_profile_form_includes_timezone(self):
        from apps.accounts.forms import ProfileForm

        form = ProfileForm()
        assert "timezone" in form.fields

    def test_timezone_middleware_activates(self, auth_client, owner_user):
        owner_user.timezone = "US/Eastern"
        owner_user.save(update_fields=["timezone"])
        response = auth_client.get(reverse("dashboard"))
        assert response.status_code in [200, 302]


@pytest.mark.integration
class TestSessionReminders:
    """FEAT-007: Session reminders via email."""

    def test_livesession_has_reminder_flags(self, db):
        from apps.scheduling.models import LiveSession

        assert hasattr(LiveSession, "reminder_24h_sent")
        assert hasattr(LiveSession, "reminder_1h_sent")

    def test_send_reminders_command_runs(self, db):
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command("send_session_reminders", stdout=out)
        assert "reminders" in out.getvalue().lower()


@pytest.mark.integration
class TestRecordingUpload:
    """FEAT-008: Student recording upload."""

    def test_submission_has_recording_field(self, db):
        from apps.enrollments.models import AssignmentSubmission

        assert hasattr(AssignmentSubmission, "recording")

    def test_recording_properties(self, db):
        from apps.enrollments.models import AssignmentSubmission

        sub = AssignmentSubmission()
        assert sub.is_audio_recording is False
        assert sub.is_video_recording is False
        assert sub.recording_size_display == ""


@pytest.mark.integration
class TestInAppMessaging:
    """FEAT-009: In-app messaging."""

    def test_inbox_loads(self, auth_client):
        response = auth_client.get(reverse("message-inbox"))
        assert response.status_code == 200
        assert b"Messages" in response.content

    def test_sent_loads(self, auth_client):
        response = auth_client.get(reverse("message-sent"))
        assert response.status_code == 200

    def test_compose_loads(self, auth_client):
        response = auth_client.get(reverse("message-compose"))
        assert response.status_code == 200
        assert b"Compose" in response.content

    def test_send_message(self, auth_client, owner_user, db):
        # Create a second user to send to
        recipient = User.objects.create_user(
            email="msg_recipient@test.com",
            username="msg_recipient",
            password="testpass123",
        )
        academy = owner_user.current_academy
        Membership.objects.create(user=recipient, academy=academy, role="student")

        response = auth_client.post(reverse("message-compose"), {
            "recipient": recipient.pk,
            "subject": "Test Message",
            "body": "Hello!",
        })
        assert response.status_code == 302
        assert Message.objects.filter(sender=owner_user, recipient=recipient).exists()

    def test_unread_count(self, auth_client):
        response = auth_client.get(reverse("message-unread-count"))
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.django_db
class TestBrandedSignup:
    """FEAT-011: Academy-branded signup link."""

    def test_branded_signup_page_loads(self, client, db):
        from apps.academies.models import Academy

        academy = Academy.objects.create(name="Test Academy", slug="test-academy")
        response = client.get(reverse("branded-signup", args=["test-academy"]))
        assert response.status_code == 200
        assert b"Test Academy" in response.content

    def test_branded_signup_creates_student(self, client, db):
        from apps.academies.models import Academy

        academy = Academy.objects.create(name="Signup Academy", slug="signup-academy")
        response = client.post(reverse("branded-signup", args=["signup-academy"]), {
            "email": "newstudent@test.com",
            "username": "newstudent",
            "first_name": "New",
            "last_name": "Student",
            "password1": "complexpass123!",
            "password2": "complexpass123!",
        })
        assert response.status_code == 302
        user = User.objects.get(email="newstudent@test.com")
        assert Membership.objects.filter(user=user, academy=academy, role="student").exists()

    def test_branded_signup_sends_email_to_owner(self, client, db):
        """BUG-013: Branded signup should send notification email to academy owner(s)."""
        from django.core import mail
        from apps.academies.models import Academy
        from apps.notifications.models import Notification

        # Create academy with an owner
        academy = Academy.objects.create(name="Email Academy", slug="email-academy")
        owner = User.objects.create_user(
            username="academy_owner",
            email="owner@email-academy.com",
            password="testpass123",
            first_name="Academy",
            last_name="Owner",
        )
        Membership.objects.create(user=owner, academy=academy, role="owner")

        # Register a new student via branded signup
        response = client.post(reverse("branded-signup", args=["email-academy"]), {
            "email": "newstudent@example.com",
            "username": "newstudent_email",
            "first_name": "Jane",
            "last_name": "Doe",
            "password1": "complexpass123!",
            "password2": "complexpass123!",
        })
        assert response.status_code == 302

        # Verify email was sent to the owner
        assert len(mail.outbox) == 1
        email_msg = mail.outbox[0]
        assert email_msg.to == ["owner@email-academy.com"]
        assert "Email Academy" in email_msg.subject
        assert "New member" in email_msg.subject
        assert "Jane Doe" in email_msg.body
        assert "newstudent@example.com" in email_msg.body

        # Verify in-app notification was created for the owner
        notifications = Notification.objects.filter(recipient=owner, academy=academy)
        assert notifications.count() == 1
        assert "Jane Doe" in notifications.first().message
        assert "branded signup" in notifications.first().message

    def test_branded_signup_invalid_slug_returns_404(self, client, db):
        """Boundary: branded signup for a non-existent academy slug returns 404."""
        response = client.get(reverse("branded-signup", args=["nonexistent-academy"]))
        assert response.status_code == 404

        response = client.post(reverse("branded-signup", args=["nonexistent-academy"]), {
            "email": "ghost@example.com",
            "username": "ghost",
            "first_name": "Ghost",
            "last_name": "User",
            "password1": "complexpass123!",
            "password2": "complexpass123!",
        })
        assert response.status_code == 404


@pytest.mark.integration
class TestEmailNotifications:
    """FEAT-012: Email notifications."""

    def test_user_has_email_preferences(self, owner_user):
        assert hasattr(owner_user, "email_preferences")

    def test_wants_email_defaults_true(self, owner_user):
        assert owner_user.wants_email("enrollment_created") is True
        assert owner_user.wants_email("assignment_graded") is True

    def test_wants_email_respects_preference(self, owner_user):
        owner_user.email_preferences = {"enrollment_created": False}
        owner_user.save()
        assert owner_user.wants_email("enrollment_created") is False
        assert owner_user.wants_email("assignment_graded") is True


@pytest.mark.integration
class TestMobileResponsive:
    """FEAT-010: Mobile responsive (base template checks)."""

    def test_base_template_has_viewport_meta(self, auth_client):
        response = auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200
        assert b"viewport" in response.content

    def test_base_template_has_drawer(self, auth_client):
        response = auth_client.get(reverse("admin-dashboard"))
        assert b"drawer" in response.content

    def test_sidebar_has_messages_link(self, auth_client):
        response = auth_client.get(reverse("admin-dashboard"))
        assert b"Messages" in response.content
