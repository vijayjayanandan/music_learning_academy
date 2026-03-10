"""Tests for Chat with Instructor UX redesign."""

from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.notifications.models import Message
from apps.scheduling.models import LiveSession


class TestChatInstructor(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Academy A
        cls.academy = Academy.objects.create(
            name="Test Academy",
            slug="test-academy",
            description="A test academy",
            email="test@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner_user = User.objects.create_user(
            username="owner",
            email="owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner_user.current_academy = cls.academy
        cls.owner_user.save()
        Membership.objects.create(user=cls.owner_user, academy=cls.academy, role="owner")

        cls.instructor_user = User.objects.create_user(
            username="instructor",
            email="instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user, academy=cls.academy, role="instructor"
        )

        cls.student_user = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Student",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user, academy=cls.academy, role="student"
        )

        # Course + Enrollment
        cls.course = Course.objects.create(
            academy=cls.academy,
            title="Piano 101",
            slug="piano-101",
            description="Intro to piano",
            instructor=cls.instructor_user,
            instrument="Piano",
            difficulty_level="beginner",
            is_published=True,
        )
        cls.enrollment = Enrollment.objects.create(
            academy=cls.academy,
            student=cls.student_user,
            course=cls.course,
            status="active",
        )

        # Live Session (future)
        cls.session = LiveSession.objects.create(
            academy=cls.academy,
            title="Piano Lesson",
            instructor=cls.instructor_user,
            scheduled_start=timezone.now() + timedelta(days=7),
            scheduled_end=timezone.now() + timedelta(days=7, hours=1),
            session_type="one_on_one",
            room_name="test-room-123",
        )

        # Academy B (for cross-tenant test)
        cls.academy_b = Academy.objects.create(
            name="Other Academy",
            slug="other-academy",
            description="Another academy",
            email="other@academy.com",
            timezone="UTC",
            primary_instruments=["Guitar"],
            genres=["Rock"],
        )
        cls.owner_b = User.objects.create_user(
            username="owner_b",
            email="ownerb@test.com",
            password="testpass123",
            first_name="Other",
            last_name="Owner",
        )
        cls.owner_b.current_academy = cls.academy_b
        cls.owner_b.save()
        Membership.objects.create(user=cls.owner_b, academy=cls.academy_b, role="owner")

    # --- Conversation list (3 tests) ---

    def test_conversation_list_shows_threads(self):
        """Inbox shows threads where user is sender or recipient."""
        # Thread 1: student sent to instructor
        Message.objects.create(
            sender=self.student_user,
            recipient=self.instructor_user,
            academy=self.academy,
            subject="Conversation",
            body="Hello instructor",
        )
        # Thread 2: owner sent to student
        Message.objects.create(
            sender=self.owner_user,
            recipient=self.student_user,
            academy=self.academy,
            subject="Conversation",
            body="Hello student",
        )
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("message-inbox"))
        content = response.content.decode()
        assert self.instructor_user.get_full_name() in content
        assert self.owner_user.get_full_name() in content

    def test_conversation_list_shows_last_message(self):
        """Last message preview shows most recent reply, not root."""
        root = Message.objects.create(
            sender=self.student_user,
            recipient=self.instructor_user,
            academy=self.academy,
            subject="Conversation",
            body="Hello",
        )
        Message.objects.create(
            sender=self.instructor_user,
            recipient=self.student_user,
            academy=self.academy,
            subject="Re: Conversation",
            body="Hi there",
            parent=root,
        )
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("message-inbox"))
        assert "Hi there" in response.content.decode()

    def test_conversation_list_unread_badge(self):
        """Unread messages show badge-primary badge on conversation row."""
        Message.objects.create(
            sender=self.instructor_user,
            recipient=self.student_user,
            academy=self.academy,
            subject="Conversation",
            body="Unread msg",
            is_read=False,
        )
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("message-inbox"))
        assert "badge-primary" in response.content.decode()

    # --- Thread view (3 tests) ---

    def test_thread_view_chat_bubbles(self):
        """Thread shows chat-start and chat-end bubbles for two participants."""
        root = Message.objects.create(
            sender=self.student_user,
            recipient=self.instructor_user,
            academy=self.academy,
            subject="Conversation",
            body="Hello",
        )
        Message.objects.create(
            sender=self.instructor_user,
            recipient=self.student_user,
            academy=self.academy,
            subject="Re: Conversation",
            body="Hi",
            parent=root,
        )
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("message-thread", args=[root.pk]))
        content = response.content.decode()
        assert "chat-start" in content
        assert "chat-end" in content

    def test_reply_via_htmx(self):
        """POST with HTMX returns a single chat bubble partial."""
        root = Message.objects.create(
            sender=self.student_user,
            recipient=self.instructor_user,
            academy=self.academy,
            subject="Conversation",
            body="Hello",
        )
        self.client.force_login(self.student_user)
        url = reverse("message-thread", args=[root.pk])
        response = self.client.post(
            url, {"body": "New reply"}, HTTP_HX_REQUEST="true"
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "New reply" in content
        assert "chat-bubble" in content
        assert Message.objects.filter(parent=root).count() == 1

    def test_marks_read_on_open(self):
        """Opening a thread marks unread messages as read."""
        root = Message.objects.create(
            sender=self.instructor_user,
            recipient=self.student_user,
            academy=self.academy,
            subject="Conversation",
            body="Read me",
            is_read=False,
        )
        self.client.force_login(self.student_user)
        self.client.get(reverse("message-thread", args=[root.pk]))
        root.refresh_from_db()
        assert root.is_read is True

    # --- ConversationWithView (2 tests) ---

    def test_conversation_with_creates_thread(self):
        """GET conversation-with creates a new thread if none exists."""
        self.client.force_login(self.student_user)
        url = reverse("conversation-with", args=[self.instructor_user.pk])
        response = self.client.get(url)
        assert response.status_code == 302
        assert Message.objects.filter(
            sender=self.student_user,
            recipient=self.instructor_user,
            parent__isnull=True,
        ).exists()
        # Follow redirect to verify thread page loads
        follow_response = self.client.get(response.url)
        assert follow_response.status_code == 200

    def test_conversation_with_finds_existing(self):
        """GET conversation-with redirects to existing thread, not a new one."""
        existing = Message.objects.create(
            sender=self.student_user,
            recipient=self.instructor_user,
            academy=self.academy,
            subject="Conversation",
            body="",
        )
        count_before = Message.objects.count()
        self.client.force_login(self.student_user)
        url = reverse("conversation-with", args=[self.instructor_user.pk])
        response = self.client.get(url)
        assert response.status_code == 302
        assert str(existing.pk) in response.url
        assert Message.objects.count() == count_before

    # --- Entry points (2 tests) ---

    def test_course_detail_shows_message_button(self):
        """Course detail page shows Message link for students."""
        self.client.force_login(self.student_user)
        url = reverse("course-detail", args=[self.course.slug])
        response = self.client.get(url)
        content = response.content.decode()
        conversation_url = reverse(
            "conversation-with", args=[self.instructor_user.pk]
        )
        assert conversation_url in content
        assert "Message" in content

    def test_enrollment_detail_shows_message_button(self):
        """Enrollment detail page shows Message Instructor CTA."""
        self.client.force_login(self.student_user)
        url = reverse("enrollment-detail", args=[self.enrollment.pk])
        response = self.client.get(url)
        content = response.content.decode()
        assert "Message Instructor" in content
        conversation_url = reverse(
            "conversation-with", args=[self.instructor_user.pk]
        )
        assert conversation_url in content

    # --- Security (2 tests) ---

    def test_cross_tenant_blocked(self):
        """Cannot start conversation with user in different academy."""
        self.client.force_login(self.student_user)
        url = reverse("conversation-with", args=[self.owner_b.pk])
        response = self.client.get(url)
        assert response.status_code == 403

    def test_cannot_message_self(self):
        """Cannot start conversation with yourself — redirects to inbox."""
        count_before = Message.objects.count()
        self.client.force_login(self.student_user)
        url = reverse("conversation-with", args=[self.student_user.pk])
        response = self.client.get(url)
        assert response.status_code == 302
        assert Message.objects.count() == count_before
