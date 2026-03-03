import pytest
from django.urls import reverse


@pytest.mark.integration
class TestAuthViews:
    def test_login_page_loads(self, client):
        response = client.get(reverse("login"))
        assert response.status_code == 200
        assert b"Sign in" in response.content

    def test_login_with_valid_credentials(self, client, owner_user):
        response = client.post(reverse("login"), {
            "username": "owner@test.com",
            "password": "testpass123",
        })
        assert response.status_code == 302

    def test_login_with_invalid_credentials(self, client, owner_user):
        response = client.post(reverse("login"), {
            "username": "owner@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 200  # stays on login page

    def test_register_page_loads(self, client):
        response = client.get(reverse("register"))
        assert response.status_code == 200

    def test_logout_redirects(self, auth_client):
        response = auth_client.post(reverse("logout"))
        assert response.status_code == 302


@pytest.mark.integration
class TestDashboardViews:
    def test_dashboard_redirect_unauthenticated(self, client):
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_dashboard_redirect_for_owner(self, auth_client):
        response = auth_client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "admin" in response.url

    def test_admin_dashboard_loads(self, auth_client):
        response = auth_client.get(reverse("admin-dashboard"))
        assert response.status_code == 200


@pytest.mark.integration
class TestCourseViews:
    def test_course_list_loads(self, auth_client):
        response = auth_client.get(reverse("course-list"))
        assert response.status_code == 200

    def test_course_create_loads(self, auth_client):
        response = auth_client.get(reverse("course-create"))
        assert response.status_code == 200

    def test_course_list_unauthenticated(self, client):
        response = client.get(reverse("course-list"))
        assert response.status_code == 302


@pytest.mark.integration
class TestScheduleViews:
    def test_schedule_list_loads(self, auth_client):
        response = auth_client.get(reverse("schedule-list"))
        assert response.status_code == 200

    def test_session_create_loads(self, auth_client):
        response = auth_client.get(reverse("session-create"))
        assert response.status_code == 200


@pytest.mark.integration
class TestNotificationViews:
    def test_notification_list_loads(self, auth_client):
        response = auth_client.get(reverse("notification-list"))
        assert response.status_code == 200

    def test_notification_badge_partial(self, auth_client):
        response = auth_client.get(reverse("notification-badge-partial"))
        assert response.status_code == 200
