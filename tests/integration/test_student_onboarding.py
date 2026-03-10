"""Tests for the student onboarding card on the student dashboard.

Covers:
- New student sees onboarding card (needs_onboarding is True)
- POST with valid data saves to membership + user timezone
- After saving, card disappears (redirect to dashboard, needs_onboarding is False)
- Skip action hides card (onboarding_skipped becomes True)
- Only students see the onboarding card (not owners/instructors)
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import Membership, User
from apps.academies.models import Academy


@pytest.mark.integration
class TestStudentOnboardingCardVisibility(TestCase):
    """Tests that the onboarding card is shown/hidden based on student state."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Onboarding Academy Visibility",
            slug="stu-visibility-iso",
            description="Academy for onboarding visibility tests",
            email="onboard-vis@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar", "Violin"],
            genres=["Classical"],
        )

        # A brand-new student who has NOT filled in any preferences yet.
        cls.new_student = User.objects.create_user(
            username="new-student-vis",
            email="new_student_vis@test.com",
            password="testpass123",
            first_name="New",
            last_name="Student",
        )
        cls.new_student.current_academy = cls.academy
        cls.new_student.save()
        Membership.objects.create(
            user=cls.new_student,
            academy=cls.academy,
            role="student",
            # Deliberately NOT setting instruments, learning_goal, or skill_level
            # so the defaults are used (empty list, empty string, "beginner").
        )

        # A student who has already completed onboarding.
        cls.onboarded_student = User.objects.create_user(
            username="onboarded-student-vis",
            email="onboarded_vis@test.com",
            password="testpass123",
            first_name="Onboarded",
            last_name="Student",
        )
        cls.onboarded_student.current_academy = cls.academy
        cls.onboarded_student.save()
        Membership.objects.create(
            user=cls.onboarded_student,
            academy=cls.academy,
            role="student",
            instruments=["Piano"],
            skill_level="intermediate",
            learning_goal="Play jazz",
            onboarding_skipped=True,
        )

        # An owner of the academy.
        cls.owner = User.objects.create_user(
            username="owner-vis",
            email="owner_vis@test.com",
            password="testpass123",
            first_name="Owner",
            last_name="Test",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(
            user=cls.owner, academy=cls.academy, role="owner"
        )

        # An instructor of the academy.
        cls.instructor = User.objects.create_user(
            username="instructor-vis",
            email="instructor_vis@test.com",
            password="testpass123",
            first_name="Instructor",
            last_name="Test",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

    def setUp(self):
        """Fresh HTTP clients for each test (no session bleed)."""
        self.client_new_student = Client()
        self.client_new_student.login(username="new_student_vis@test.com", password="testpass123")
        self.client_onboarded = Client()
        self.client_onboarded.login(username="onboarded_vis@test.com", password="testpass123")
        self.client_owner = Client()
        self.client_owner.login(username="owner_vis@test.com", password="testpass123")
        self.client_instructor = Client()
        self.client_instructor.login(username="instructor_vis@test.com", password="testpass123")

    def test_new_student_sees_onboarding_card(self):
        """A brand-new student with default membership fields should see the card."""
        response = self.client_new_student.get(reverse("student-dashboard"))
        assert response.status_code == 200
        assert response.context["needs_onboarding"] is True
        assert "onboarding_form" in response.context
        content = response.content.decode()
        assert "Let's personalize your experience" in content

    def test_onboarded_student_does_not_see_card(self):
        """A student who has already completed onboarding should NOT see the card."""
        response = self.client_onboarded.get(reverse("student-dashboard"))
        assert response.status_code == 200
        assert response.context["needs_onboarding"] is False
        content = response.content.decode()
        assert "Let's personalize your experience" not in content

    def test_owner_does_not_see_onboarding_card(self):
        """Owners access the admin dashboard, not the student dashboard.

        If an owner somehow hits the student dashboard, needs_onboarding is False.
        """
        response = self.client_owner.get(reverse("student-dashboard"))
        assert response.status_code == 200
        assert response.context["needs_onboarding"] is False

    def test_instructor_does_not_see_onboarding_card(self):
        """Instructors should not see the onboarding card on the student dashboard."""
        response = self.client_instructor.get(reverse("student-dashboard"))
        assert response.status_code == 200
        assert response.context["needs_onboarding"] is False


@pytest.mark.integration
class TestStudentOnboardingSubmit(TestCase):
    """Tests for the POST endpoint that saves or skips onboarding."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Onboarding Academy Submit",
            slug="stu-submit-iso",
            description="Academy for onboarding submit tests",
            email="onboard-sub@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar", "Violin"],
            genres=["Classical"],
        )

        # A brand-new student who has NOT filled in any preferences yet.
        cls.new_student = User.objects.create_user(
            username="new-student-sub",
            email="new_student_sub@test.com",
            password="testpass123",
            first_name="New",
            last_name="Student",
        )
        cls.new_student.current_academy = cls.academy
        cls.new_student.save()
        Membership.objects.create(
            user=cls.new_student,
            academy=cls.academy,
            role="student",
            # Deliberately NOT setting instruments, learning_goal, or skill_level
            # so the defaults are used (empty list, empty string, "beginner").
        )

    def setUp(self):
        """Fresh HTTP client for each test (no session bleed)."""
        self.client_new_student = Client()
        self.client_new_student.login(username="new_student_sub@test.com", password="testpass123")

    def test_save_preferences_updates_membership(self):
        """Submitting the form with valid data should save to the membership."""
        url = reverse("student-onboarding-submit")
        response = self.client_new_student.post(url, {
            "action": "save",
            "instruments": ["Piano", "Guitar"],
            "skill_level": "intermediate",
            "learning_goal": "Learn jazz piano",
            "timezone": "US/Eastern",
        })
        # Should redirect back to student dashboard
        assert response.status_code == 302
        assert response.url == reverse("student-dashboard")

        # Check membership was updated
        membership = Membership.objects.get(user=self.new_student, academy=self.academy)
        assert membership.skill_level == "intermediate"
        assert membership.learning_goal == "Learn jazz piano"
        assert membership.instruments == ["Piano", "Guitar"]
        assert membership.onboarding_skipped is True

        # Check user timezone was updated
        self.new_student.refresh_from_db()
        assert self.new_student.timezone == "US/Eastern"

    def test_save_shows_success_message(self):
        """After saving, a success message should be in the messages framework."""
        url = reverse("student-onboarding-submit")
        response = self.client_new_student.post(url, {
            "action": "save",
            "instruments": ["Piano"],
            "skill_level": "beginner",
            "learning_goal": "Have fun",
            "timezone": "UTC",
        }, follow=True)
        assert response.status_code == 200
        messages_list = list(response.context["messages"])
        assert any("preferences have been saved" in str(m) for m in messages_list)

    def test_card_disappears_after_save(self):
        """After completing onboarding, revisiting the dashboard should not show the card."""
        # Save preferences
        self.client_new_student.post(reverse("student-onboarding-submit"), {
            "action": "save",
            "instruments": ["Violin"],
            "skill_level": "advanced",
            "learning_goal": "Master violin",
            "timezone": "Europe/London",
        })
        # Revisit dashboard
        response = self.client_new_student.get(reverse("student-dashboard"))
        assert response.status_code == 200
        assert response.context["needs_onboarding"] is False

    def test_skip_hides_card(self):
        """Clicking 'Skip' should set onboarding_skipped=True and hide the card."""
        url = reverse("student-onboarding-submit")
        response = self.client_new_student.post(url, {"action": "skip"})
        assert response.status_code == 302
        assert response.url == reverse("student-dashboard")

        # Check membership
        membership = Membership.objects.get(user=self.new_student, academy=self.academy)
        assert membership.onboarding_skipped is True
        # Skill level should still be the default
        assert membership.skill_level == "beginner"
        assert membership.learning_goal == ""

        # Card should not appear on next visit
        response = self.client_new_student.get(reverse("student-dashboard"))
        assert response.context["needs_onboarding"] is False

    def test_partial_save_only_updates_provided_fields(self):
        """If a student only fills in some fields, only those should be updated."""
        url = reverse("student-onboarding-submit")
        response = self.client_new_student.post(url, {
            "action": "save",
            "skill_level": "intermediate",
            # No instruments, no learning_goal, no timezone
        })
        assert response.status_code == 302

        membership = Membership.objects.get(user=self.new_student, academy=self.academy)
        assert membership.skill_level == "intermediate"
        assert membership.learning_goal == ""  # unchanged
        assert membership.instruments == []  # unchanged (was default empty)
        assert membership.onboarding_skipped is True


@pytest.mark.integration
class TestStudentOnboardingPermissions(TestCase):
    """Security boundary tests for the onboarding submit endpoint."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Onboarding Academy Permissions",
            slug="stu-perms-iso",
            description="Academy for onboarding permission tests",
            email="onboard-perms@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar", "Violin"],
            genres=["Classical"],
        )

        # A brand-new student who has NOT filled in any preferences yet.
        cls.new_student = User.objects.create_user(
            username="new-student-perms",
            email="new_student_perms@test.com",
            password="testpass123",
            first_name="New",
            last_name="Student",
        )
        cls.new_student.current_academy = cls.academy
        cls.new_student.save()
        Membership.objects.create(
            user=cls.new_student,
            academy=cls.academy,
            role="student",
        )

        # An owner of the academy.
        cls.owner = User.objects.create_user(
            username="owner-perms",
            email="owner_perms@test.com",
            password="testpass123",
            first_name="Owner",
            last_name="Test",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(
            user=cls.owner, academy=cls.academy, role="owner"
        )

        # An instructor of the academy.
        cls.instructor = User.objects.create_user(
            username="instructor-perms",
            email="instructor_perms@test.com",
            password="testpass123",
            first_name="Instructor",
            last_name="Test",
        )
        cls.instructor.current_academy = cls.academy
        cls.instructor.save()
        Membership.objects.create(
            user=cls.instructor, academy=cls.academy, role="instructor"
        )

    def setUp(self):
        """Fresh HTTP clients for each test (no session bleed)."""
        self.anon_client = Client()
        self.client_new_student = Client()
        self.client_new_student.login(username="new_student_perms@test.com", password="testpass123")
        self.client_owner = Client()
        self.client_owner.login(username="owner_perms@test.com", password="testpass123")
        self.client_instructor = Client()
        self.client_instructor.login(username="instructor_perms@test.com", password="testpass123")

    def test_unauthenticated_user_redirected(self):
        """Unauthenticated users should be redirected to login."""
        url = reverse("student-onboarding-submit")
        response = self.anon_client.post(url, {"action": "save"})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_owner_cannot_submit_onboarding(self):
        """Owners should be redirected away from the student onboarding endpoint."""
        url = reverse("student-onboarding-submit")
        response = self.client_owner.post(url, {
            "action": "save",
            "skill_level": "advanced",
            "learning_goal": "Hack the system",
        })
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

    def test_instructor_cannot_submit_onboarding(self):
        """Instructors should be redirected away from the student onboarding endpoint."""
        url = reverse("student-onboarding-submit")
        response = self.client_instructor.post(url, {
            "action": "save",
            "skill_level": "advanced",
        })
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

    def test_get_request_not_allowed(self):
        """The onboarding endpoint only accepts POST, not GET."""
        url = reverse("student-onboarding-submit")
        response = self.client_new_student.get(url)
        assert response.status_code == 405  # Method Not Allowed
