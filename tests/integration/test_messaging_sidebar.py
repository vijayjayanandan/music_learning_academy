"""Tests for messaging sidebar visibility and unread badge.

Verifies that:
- Messages link is visible in sidebar for all authenticated roles
- Unread badge endpoint returns correct count
- Unauthenticated users cannot access messaging endpoints
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.notifications.models import Message


@pytest.mark.integration
class TestMessageSidebarVisibility(TestCase):
    """Messages link should be visible in sidebar for all roles."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Messaging Sidebar Academy",
            slug="msg-sidebar-iso",
            description="Academy for sidebar messaging tests",
            email="msg-sidebar-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="msg-sidebar-owner",
            email="msg-sidebar-owner@test.com",
            password="testpass123",
            first_name="Sidebar",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.instructor = User.objects.create_user(
            username="msg-sidebar-instructor",
            email="msg-sidebar-instructor@test.com",
            password="testpass123",
            first_name="Sidebar",
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
            username="msg-sidebar-student",
            email="msg-sidebar-student@test.com",
            password="testpass123",
            first_name="Sidebar",
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
            username="msg-sidebar-owner@test.com", password="testpass123"
        )
        self.instructor_client = Client()
        self.instructor_client.login(
            username="msg-sidebar-instructor@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="msg-sidebar-student@test.com", password="testpass123"
        )

    def test_owner_sees_messages_in_sidebar(self):
        response = self.auth_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert reverse("message-inbox") in content
        assert "Messages" in content

    def test_instructor_sees_messages_in_sidebar(self):
        response = self.instructor_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert reverse("message-inbox") in content
        assert "Messages" in content

    def test_student_sees_messages_in_sidebar(self):
        response = self.student_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert reverse("message-inbox") in content
        assert "Messages" in content

    def test_sidebar_has_unread_badge_htmx(self):
        """Sidebar Messages link includes HTMX polling for unread count."""
        response = self.auth_client.get(reverse("dashboard"), follow=True)
        content = response.content.decode()
        assert reverse("message-unread-count") in content
        assert 'hx-trigger="load, every 30s"' in content


@pytest.mark.integration
class TestUnreadMessageCountBadge(TestCase):
    """UnreadMessageCountView returns correct badge HTML."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Unread Badge Academy",
            slug="msg-unread-iso",
            description="Academy for unread badge tests",
            email="msg-unread-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Guitar"],
            genres=["Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="msg-unread-owner",
            email="msg-unread-owner@test.com",
            password="testpass123",
            first_name="Unread",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="msg-unread-student",
            email="msg-unread-student@test.com",
            password="testpass123",
            first_name="Unread",
            last_name="Student",
        )
        cls.student.current_academy = cls.academy
        cls.student.save()
        Membership.objects.create(
            user=cls.student,
            academy=cls.academy,
            role="student",
            instruments=["Guitar"],
            skill_level="beginner",
        )

        cls.instructor = User.objects.create_user(
            username="msg-unread-instructor",
            email="msg-unread-instructor@test.com",
            password="testpass123",
            first_name="Unread",
            last_name="Instructor",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor,
            academy=cls.academy,
            role="instructor",
            instruments=["Guitar"],
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="msg-unread-owner@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="msg-unread-student@test.com", password="testpass123"
        )
        self.instructor_client = Client()
        self.instructor_client.login(
            username="msg-unread-instructor@test.com", password="testpass123"
        )

    def test_zero_unread_returns_empty(self):
        response = self.auth_client.get(reverse("message-unread-count"))
        assert response.status_code == 200
        content = response.content.decode().strip()
        # No badge should be rendered when count is 0
        assert "badge" not in content

    def test_unread_messages_show_badge_count(self):
        # Create a sender
        sender = User.objects.create_user(
            email="msg-unread-sender@test.com",
            username="msg-unread-sender",
            password="testpass123",
        )
        Membership.objects.create(user=sender, academy=self.academy, role="instructor")
        # Create 3 unread messages
        for i in range(3):
            Message.objects.create(
                sender=sender,
                recipient=self.owner,
                academy=self.academy,
                subject=f"Test {i}",
                body=f"Body {i}",
                is_read=False,
            )
        response = self.auth_client.get(reverse("message-unread-count"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "badge" in content
        assert "3" in content

    def test_read_messages_not_counted(self):
        sender = User.objects.create_user(
            email="msg-unread-sender2@test.com",
            username="msg-unread-sender2",
            password="testpass123",
        )
        Membership.objects.create(user=sender, academy=self.academy, role="student")
        # Create a read message
        Message.objects.create(
            sender=sender,
            recipient=self.owner,
            academy=self.academy,
            subject="Read msg",
            body="Already read",
            is_read=True,
        )
        response = self.auth_client.get(reverse("message-unread-count"))
        content = response.content.decode().strip()
        assert "badge" not in content

    def test_student_can_access_unread_count(self):
        response = self.student_client.get(reverse("message-unread-count"))
        assert response.status_code == 200

    def test_instructor_can_access_unread_count(self):
        response = self.instructor_client.get(reverse("message-unread-count"))
        assert response.status_code == 200


@pytest.mark.integration
class TestMessagingAccessControl(TestCase):
    """Unauthenticated users cannot access messaging."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Access Control Academy",
            slug="msg-access-iso",
            description="Academy for access control tests",
            email="msg-access-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Violin"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="msg-access-owner",
            email="msg-access-owner@test.com",
            password="testpass123",
            first_name="Access",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="msg-access-owner@test.com", password="testpass123"
        )
        self.anon_client = Client()

    def test_unauthenticated_inbox_redirects(self):
        response = self.anon_client.get(reverse("message-inbox"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_unauthenticated_unread_count_redirects(self):
        response = self.anon_client.get(reverse("message-unread-count"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_other_academy_messages_not_counted(self):
        """Messages from another academy should not appear in unread count."""
        other_academy = Academy.objects.create(
            name="Other Academy", slug="msg-other-academy-iso"
        )
        sender = User.objects.create_user(
            email="msg-other-sender@test.com",
            username="msg-other-sender",
            password="testpass123",
        )
        Membership.objects.create(user=sender, academy=other_academy, role="owner")
        # Create an unread message in a different academy
        Message.objects.create(
            sender=sender,
            recipient=self.owner,
            academy=other_academy,
            subject="Cross-academy",
            body="Should not count",
            is_read=False,
        )
        response = self.auth_client.get(reverse("message-unread-count"))
        content = response.content.decode().strip()
        # Should not show badge because the message is in another academy
        assert "badge" not in content
