"""Tests for seat limit enforcement on InviteMemberView, BrandedSignupView, and CourseCreateView."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import Membership, User
from apps.academies.models import Academy, check_seat_limit, check_course_limit
from apps.courses.models import Course
from apps.payments.models import AcademyTier
from tests.factories import (
    CourseFactory,
    MembershipFactory,
    UserFactory,
)


@pytest.mark.integration
class TestCheckSeatLimitHelper(TestCase):
    """Unit tests for the check_seat_limit() helper function."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Seat Limit Helper Academy",
            slug="seat-checkseat-iso",
            description="A test academy",
            email="seat-checkseat-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-checkseat-iso",
            email="owner-checkseat-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def test_student_under_limit_allowed(self):
        """Happy path: academy with room for more students returns allowed."""
        self.academy.max_students = 5
        self.academy.save()
        is_allowed, current, max_count = check_seat_limit(self.academy, "student")
        assert is_allowed is True
        assert current == 0
        assert max_count == 5

    def test_student_at_limit_denied(self):
        """Academy at student capacity returns not allowed."""
        self.academy.max_students = 2
        self.academy.save()
        for i in range(2):
            user = UserFactory(
                username=f"chkseat-stud{i}", email=f"chkseat-stud{i}@test.com"
            )
            MembershipFactory(user=user, academy=self.academy, role="student")
        is_allowed, current, max_count = check_seat_limit(self.academy, "student")
        assert is_allowed is False
        assert current == 2
        assert max_count == 2

    def test_instructor_at_limit_denied(self):
        """Academy at instructor capacity returns not allowed."""
        self.academy.max_instructors = 1
        self.academy.save()
        user = UserFactory(username="chkseat-inst0", email="chkseat-inst0@test.com")
        MembershipFactory(user=user, academy=self.academy, role="instructor")
        is_allowed, current, max_count = check_seat_limit(self.academy, "instructor")
        assert is_allowed is False
        assert current == 1
        assert max_count == 1

    def test_owner_role_always_allowed(self):
        """Owner role has no seat limit."""
        is_allowed, current, max_count = check_seat_limit(self.academy, "owner")
        assert is_allowed is True

    def test_tier_overrides_academy_limit(self):
        """When academy has a tier, tier limits take precedence."""
        tier = AcademyTier.objects.create(
            name="Pro-checkseat",
            tier_level="pro",
            max_students=3,
            max_instructors=1,
            max_courses=10,
        )
        self.academy.tier = tier
        self.academy.max_students = 100  # academy default is higher
        self.academy.save()
        is_allowed, current, max_count = check_seat_limit(self.academy, "student")
        assert max_count == 3  # uses tier limit, not academy limit

    def test_inactive_members_not_counted(self):
        """Inactive members should not count against the seat limit."""
        self.academy.max_students = 1
        self.academy.save()
        user = UserFactory(
            username="chkseat-inactive", email="chkseat-inactive@test.com"
        )
        MembershipFactory(
            user=user, academy=self.academy, role="student", is_active=False
        )
        is_allowed, current, max_count = check_seat_limit(self.academy, "student")
        assert is_allowed is True
        assert current == 0


@pytest.mark.integration
class TestCheckCourseLimitHelper(TestCase):
    """Unit tests for the check_course_limit() helper function."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Course Limit Helper Academy",
            slug="seat-checkcourse-iso",
            description="A test academy",
            email="seat-checkcourse-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="owner-checkcourse-iso",
            email="owner-checkcourse-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def test_under_limit_allowed(self):
        """Happy path: academy with room for more courses returns allowed."""
        is_allowed, current, max_count = check_course_limit(self.academy)
        assert is_allowed is True
        assert current == 0
        assert max_count == 50  # default when no tier

    def test_tier_limit_enforced(self):
        """Course limit from tier is enforced."""
        tier = AcademyTier.objects.create(
            name="Free-checkcourse",
            tier_level="free",
            max_students=10,
            max_instructors=2,
            max_courses=2,
        )
        self.academy.tier = tier
        self.academy.save()
        CourseFactory(academy=self.academy, instructor=self.owner)
        CourseFactory(academy=self.academy, instructor=self.owner)
        is_allowed, current, max_count = check_course_limit(self.academy)
        assert is_allowed is False
        assert current == 2
        assert max_count == 2


@pytest.mark.integration
class TestInviteMemberViewSeatLimit(TestCase):
    """Integration tests for seat limit enforcement in InviteMemberView."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Invite Seat Limit Academy",
            slug="seat-invite-iso",
            description="A test academy",
            email="seat-invite-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-invite-iso",
            email="owner-invite-iso@test.com",
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
            username="owner-invite-iso@test.com", password="testpass123"
        )

    def test_invite_allowed_under_limit(self):
        """Happy path: invite succeeds when under the seat limit."""
        self.academy.max_students = 10
        self.academy.save()
        url = reverse("academy-invite", args=[self.academy.slug])
        response = self.auth_client.post(
            url,
            {
                "email": "newstudent-invite@example.com",
                "role": "student",
            },
        )
        assert response.status_code == 302  # redirect to members page

    def test_invite_blocked_at_student_limit(self):
        """Invitation is blocked when student seat limit is reached."""
        self.academy.max_students = 1
        self.academy.save()
        # Fill the one student seat
        student = UserFactory(username="invite-s1", email="invite-s1@test.com")
        MembershipFactory(user=student, academy=self.academy, role="student")
        url = reverse("academy-invite", args=[self.academy.slug])
        response = self.auth_client.post(
            url,
            {
                "email": "invite-another@example.com",
                "role": "student",
            },
        )
        # Should redirect back to members with error
        assert response.status_code == 302

    def test_invite_blocked_at_instructor_limit(self):
        """Invitation is blocked when instructor seat limit is reached."""
        self.academy.max_instructors = 1
        self.academy.save()
        instructor = UserFactory(username="invite-i1", email="invite-i1@test.com")
        MembershipFactory(user=instructor, academy=self.academy, role="instructor")
        url = reverse("academy-invite", args=[self.academy.slug])
        response = self.auth_client.post(
            url,
            {
                "email": "invite-newinstructor@example.com",
                "role": "instructor",
            },
        )
        assert response.status_code == 302

    def test_invite_htmx_returns_error_at_limit(self):
        """HTMX invite returns error message when at capacity."""
        self.academy.max_students = 0
        self.academy.save()
        url = reverse("academy-invite", args=[self.academy.slug])
        response = self.auth_client.post(
            url,
            {"email": "invite-new@example.com", "role": "student"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "maximum of 0 students" in content


@pytest.mark.integration
class TestBrandedSignupSeatLimit(TestCase):
    """Integration tests for seat limit enforcement in BrandedSignupView."""

    @classmethod
    def setUpTestData(cls):
        # Branded signup tests create their own academies per-test
        # because each test needs different max_students settings.
        # Shared data: a reusable user for authenticated GET tests.
        cls.auth_user = User.objects.create_user(
            username="branded-authuser-iso",
            email="branded-auth-iso@test.com",
            password="testpass123",
            first_name="Auth",
            last_name="User",
        )
        cls.existing_member_user = User.objects.create_user(
            username="branded-member-iso",
            email="branded-member-iso@test.com",
            password="testpass123",
            first_name="Member",
            last_name="User",
        )

    def setUp(self):
        self.client = Client()

    def test_branded_signup_post_allowed_under_limit(self):
        """Happy path: branded signup succeeds when under seat limit."""
        academy = Academy.objects.create(
            name="Branded Allowed Academy",
            slug="seat-branded-allowed-iso",
            description="A test academy",
            email="seat-branded-allowed-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
            max_students=10,
        )
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.post(
            url,
            {
                "email": "branded-newuser@example.com",
                "password1": "securePass123!",
                "password2": "securePass123!",
                "date_of_birth": "2000-01-01",
                "accept_terms": "on",
            },
        )
        # Successful signup redirects to dashboard
        assert response.status_code == 302

    def test_branded_signup_post_blocked_at_limit(self):
        """Branded signup POST is blocked when student limit is reached."""
        academy = Academy.objects.create(
            name="Branded Blocked Academy",
            slug="seat-branded-blocked-iso",
            description="A test academy",
            email="seat-branded-blocked-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
            max_students=1,
        )
        # Fill the seat
        student = UserFactory(
            username="branded-existing-iso", email="branded-existing-iso@test.com"
        )
        MembershipFactory(user=student, academy=academy, role="student")
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.post(
            url,
            {
                "email": "branded-blocked@example.com",
                "password1": "securePass123!",
                "password2": "securePass123!",
                "date_of_birth": "2000-01-01",
                "accept_terms": "on",
            },
        )
        # Should redirect back to branded signup
        assert response.status_code == 302
        assert academy.slug in response.url
        # User should NOT have been created
        assert not User.objects.filter(email="branded-blocked@example.com").exists()

    def test_branded_signup_get_authenticated_blocked_at_limit(self):
        """Authenticated GET to branded signup is blocked at capacity."""
        academy = Academy.objects.create(
            name="Branded Auth Blocked Academy",
            slug="seat-branded-authblocked-iso",
            description="A test academy",
            email="seat-branded-authblocked-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
            max_students=0,
        )
        self.client.force_login(self.auth_user)
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)
        # Should redirect back with error
        assert response.status_code == 302
        assert academy.slug in response.url
        # No membership created
        assert not Membership.objects.filter(
            user=self.auth_user, academy=academy
        ).exists()

    def test_branded_signup_get_authenticated_existing_member_allowed(self):
        """Existing member should bypass seat limit check on GET."""
        academy = Academy.objects.create(
            name="Branded Member Allowed Academy",
            slug="seat-branded-memberok-iso",
            description="A test academy",
            email="seat-branded-memberok-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
            max_students=1,
        )
        MembershipFactory(
            user=self.existing_member_user, academy=academy, role="student"
        )
        self.client.force_login(self.existing_member_user)
        url = reverse("branded-signup", args=[academy.slug])
        response = self.client.get(url)
        # Should redirect to dashboard, not blocked
        assert response.status_code == 302
        assert "join" not in response.url  # not redirecting back to signup


@pytest.mark.integration
class TestCourseCreateViewCourseLimit(TestCase):
    """Integration tests for course limit enforcement in CourseCreateView."""

    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Course Create Limit Academy",
            slug="seat-coursecreate-iso",
            description="A test academy",
            email="seat-coursecreate-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical", "Jazz"],
        )
        cls.owner = User.objects.create_user(
            username="owner-coursecreate-iso",
            email="owner-coursecreate-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

        cls.student = User.objects.create_user(
            username="student-coursecreate-iso",
            email="student-coursecreate-iso@test.com",
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
            username="owner-coursecreate-iso@test.com", password="testpass123"
        )
        self.student_client = Client()
        self.student_client.login(
            username="student-coursecreate-iso@test.com", password="testpass123"
        )

    def test_course_create_allowed_under_limit(self):
        """Happy path: course creation succeeds when under the limit."""
        url = reverse("course-create")
        response = self.auth_client.post(
            url,
            {
                "title": "New Course Seat Test",
                "description": "A test course",
                "instrument": "Piano",
                "difficulty_level": "beginner",
                "estimated_duration_weeks": 8,
                "max_students": 30,
            },
        )
        assert response.status_code == 302
        assert Course.objects.filter(
            academy=self.academy, title="New Course Seat Test"
        ).exists()

    def test_course_create_blocked_at_tier_limit(self):
        """Course creation is blocked when tier course limit is reached."""
        tier = AcademyTier.objects.create(
            name="Free-coursecreate",
            tier_level="free",
            max_students=10,
            max_instructors=2,
            max_courses=1,
        )
        self.academy.tier = tier
        self.academy.save()
        # Create one course to fill the limit
        CourseFactory(academy=self.academy, instructor=self.owner)
        url = reverse("course-create")
        response = self.auth_client.post(
            url,
            {
                "title": "Over Limit Course Seat Test",
                "description": "Should not be created",
                "instrument": "Guitar",
                "difficulty_level": "beginner",
                "estimated_duration_weeks": 4,
                "max_students": 20,
            },
        )
        # form_invalid renders the form page with 200
        assert response.status_code == 200
        assert not Course.objects.filter(title="Over Limit Course Seat Test").exists()

    def test_student_cannot_create_course(self):
        """Permission boundary: students cannot create courses."""
        url = reverse("course-create")
        response = self.student_client.post(
            url,
            {
                "title": "Student Course Seat Test",
                "description": "Should be forbidden",
                "instrument": "Piano",
                "difficulty_level": "beginner",
            },
        )
        assert response.status_code == 403
