import logging

from django.db import connection
from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    """Unauthenticated health check for load balancers — DB only."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok"}, status=200)
    except Exception:
        logger.warning("Health check: database unreachable")
        return JsonResponse({"status": "down"}, status=503)


def health_check_detail(request):
    """Staff-only detailed health check with all service statuses."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"error": "forbidden"}, status=403)

    checks = {
        "db": False,
        "redis": False,
        "celery": False,
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["db"] = True
    except Exception:
        logger.warning("Health check detail: database unreachable")

    # Check Redis (cache backend)
    try:
        from django.core.cache import cache
        cache.set("_health_check", "ok", 10)
        if cache.get("_health_check") == "ok":
            checks["redis"] = True
    except Exception:
        logger.warning("Health check detail: cache/Redis unreachable")

    # Check Celery (2s timeout — will be False in dev without workers)
    try:
        from celery import current_app
        inspector = current_app.control.inspect(timeout=2.0)
        ping = inspector.ping()
        checks["celery"] = bool(ping)
    except Exception:
        logger.warning("Health check detail: Celery unreachable")

    # Check R2/S3 storage (only when configured)
    from django.conf import settings
    if getattr(settings, "USE_R2_STORAGE", False):
        checks["storage_r2"] = False
        try:
            from apps.common.storage import PrivateMediaStorage
            storage = PrivateMediaStorage()
            from django.core.files.base import ContentFile
            test_key = "_health_check_r2.txt"
            storage.save(test_key, ContentFile(b"ok"))
            storage.delete(test_key)
            checks["storage_r2"] = True
        except Exception:
            logger.warning("Health check detail: R2 storage unreachable")

    # DB is critical — if it's down the whole app is down
    if checks["db"]:
        all_up = all(checks.values())
        status = "ok" if all_up else "degraded"
        http_status = 200
    else:
        status = "down"
        http_status = 503

    return JsonResponse(
        {"status": status, "checks": checks},
        status=http_status,
    )


def robots_txt(request):
    """Serve robots.txt for search engines."""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /accounts/",
        "Disallow: /notifications/",
        "Disallow: /health/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
