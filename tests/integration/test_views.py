import pytest
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy


@pytest.mark.integration
class TestAuthViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Auth Views Academy",
            slug="views-auth-iso",
            description="A test academy",
            email="views-auth-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="views-auth-owner",
            email="views-auth-owner@test.com",
            password="testpass123",
            first_name="Auth",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(
            username="views-auth-owner@test.com", password="testpass123"
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        assert response.status_code == 200
        assert b"Sign in" in response.content

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "views-auth-owner@test.com",
                "password": "testpass123",
            },
        )
        assert response.status_code == 302

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "views-auth-owner@test.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 200  # stays on login page

    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        assert response.status_code == 200

    def test_logout_redirects(self):
        response = self.auth_client.post(reverse("logout"))
        assert response.status_code == 302


@pytest.mark.integration
class TestDashboardViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Dashboard Views Academy",
            slug="views-dashboard-iso",
            description="A test academy",
            email="views-dashboard-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="views-dashboard-owner",
            email="views-dashboard-owner@test.com",
            password="testpass123",
            first_name="Dashboard",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(
            username="views-dashboard-owner@test.com", password="testpass123"
        )

    def test_dashboard_redirect_unauthenticated(self):
        response = self.client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_dashboard_redirect_for_owner(self):
        response = self.auth_client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "admin" in response.url

    def test_admin_dashboard_loads(self):
        response = self.auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200


@pytest.mark.integration
class TestCourseViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Course Views Academy",
            slug="views-course-iso",
            description="A test academy",
            email="views-course-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="views-course-owner",
            email="views-course-owner@test.com",
            password="testpass123",
            first_name="Course",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(
            username="views-course-owner@test.com", password="testpass123"
        )

    def test_course_list_loads(self):
        response = self.auth_client.get(reverse("course-list"))
        assert response.status_code == 200

    def test_course_create_loads(self):
        response = self.auth_client.get(reverse("course-create"))
        assert response.status_code == 200

    def test_course_list_unauthenticated(self):
        response = self.client.get(reverse("course-list"))
        assert response.status_code == 302


@pytest.mark.integration
class TestScheduleViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Schedule Views Academy",
            slug="views-schedule-iso",
            description="A test academy",
            email="views-schedule-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="views-schedule-owner",
            email="views-schedule-owner@test.com",
            password="testpass123",
            first_name="Schedule",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="views-schedule-owner@test.com", password="testpass123"
        )

    def test_schedule_list_loads(self):
        response = self.auth_client.get(reverse("schedule-list"))
        assert response.status_code == 200

    def test_session_create_loads(self):
        response = self.auth_client.get(reverse("session-create"))
        assert response.status_code == 200


@pytest.mark.integration
class TestNotificationViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Notification Views Academy",
            slug="views-notif-iso",
            description="A test academy",
            email="views-notif-iso@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        cls.owner = User.objects.create_user(
            username="views-notif-owner",
            email="views-notif-owner@test.com",
            password="testpass123",
            first_name="Notif",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.login(
            username="views-notif-owner@test.com", password="testpass123"
        )

    def test_notification_list_loads(self):
        response = self.auth_client.get(reverse("notification-list"))
        assert response.status_code == 200

    def test_notification_badge_partial(self):
        response = self.auth_client.get(reverse("notification-badge-partial"))
        assert response.status_code == 200
