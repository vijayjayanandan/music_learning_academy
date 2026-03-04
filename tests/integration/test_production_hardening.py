import json

import pytest
from django.template.loader import get_template
from django.urls import reverse


@pytest.mark.integration
class TestHealthCheck:
    @pytest.mark.django_db
    def test_health_check_returns_json(self, client):
        response = client.get(reverse("health-check"))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "ok"

    @pytest.mark.django_db
    def test_health_check_no_auth_required(self, client):
        """Health check must work without authentication."""
        response = client.get(reverse("health-check"))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_health_check_detail_requires_staff(self, client):
        """Detailed health check should deny anonymous users."""
        response = client.get(reverse("health-check-detail"))
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_health_check_detail_returns_checks_for_staff(self, auth_client, owner_user):
        """Detailed health check returns service statuses for staff users."""
        owner_user.is_staff = True
        owner_user.save()
        response = auth_client.get(reverse("health-check-detail"))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data
        assert "db" in data["checks"]
        assert "redis" in data["checks"]
        assert "celery" in data["checks"]
        assert data["checks"]["db"] is True


@pytest.mark.integration
class TestRateLimiting:
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
class TestSecurityMiddleware:
    def test_security_headers_middleware_registered(self):
        from django.conf import settings
        assert "apps.common.middleware.SecurityHeadersMiddleware" in settings.MIDDLEWARE

    def test_403_template_exists(self):
        """The 403 error template should load without errors."""
        template = get_template("403.html")
        assert template is not None
