import json

import pytest
from django.template.loader import get_template
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User, Membership
from apps.academies.models import Academy


@pytest.mark.integration
class TestHealthCheck(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academy = Academy.objects.create(
            name="Prod Hardening Academy",
            slug="prod-healthcheck-iso",
            description="Health check test academy",
            email="healthcheck-iso@academy.com",
            timezone="UTC",
        )
        cls.owner = User.objects.create_user(
            username="owner-healthcheck-iso",
            email="owner-healthcheck-iso@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner.current_academy = cls.academy
        cls.owner.save()
        Membership.objects.create(user=cls.owner, academy=cls.academy, role="owner")

    def setUp(self):
        self.client = Client()
        self.auth_client = Client()
        self.auth_client.login(
            username="owner-healthcheck-iso@test.com", password="testpass123"
        )

    def test_health_check_returns_json(self):
        response = self.client.get(reverse("health-check"))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "ok"

    def test_health_check_no_auth_required(self):
        """Health check must work without authentication."""
        response = self.client.get(reverse("health-check"))
        assert response.status_code == 200

    def test_health_check_detail_requires_staff(self):
        """Detailed health check should deny anonymous users."""
        response = self.client.get(reverse("health-check-detail"))
        assert response.status_code == 403

    def test_health_check_detail_returns_checks_for_staff(self):
        """Detailed health check returns service statuses for staff users."""
        User.objects.filter(pk=self.owner.pk).update(is_staff=True)
        staff_client = Client()
        staff_client.login(
            username="owner-healthcheck-iso@test.com", password="testpass123"
        )
        response = staff_client.get(reverse("health-check-detail"))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data
        assert "db" in data["checks"]
        assert "redis" in data["checks"]
        assert data["checks"]["db"] is True


@pytest.mark.integration
class TestRateLimiting(TestCase):
    def test_429_template_exists(self):
        """The 429 error template should load without errors."""
        template = get_template("429.html")
        assert template is not None

    def test_ratelimit_middleware_registered(self):
        from django.conf import settings

        assert "apps.common.middleware.RatelimitMiddleware" in settings.MIDDLEWARE

    def test_ratelimit_settings_configured(self):
        from django.conf import settings

        assert settings.RATELIMIT_USE_CACHE == "default"
        assert settings.RATELIMIT_FAIL_OPEN is True


@pytest.mark.integration
class TestSecurityMiddleware(TestCase):
    def test_security_headers_middleware_registered(self):
        from django.conf import settings

        assert "apps.common.middleware.SecurityHeadersMiddleware" in settings.MIDDLEWARE

    def test_403_template_exists(self):
        """The 403 error template should load without errors."""
        template = get_template("403.html")
        assert template is not None
