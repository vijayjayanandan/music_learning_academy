"""
Secured cron endpoint for scheduled tasks.

Replaces Celery Beat — called by cron-job.org (or any external scheduler).
Secured via CRON_API_KEY Bearer token with timing-safe comparison.

Usage:
    POST /cron/
    Authorization: Bearer <CRON_API_KEY>
    Content-Type: application/json
    {"tasks": ["expire_trials", "send_session_reminders"]}
    {"tasks": ["all"]}  # run all registered tasks
"""

import hmac
import json
import logging
import time

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# Task registry: name → import path + function
TASK_REGISTRY = {
    "send_session_reminders": "apps.scheduling.tasks.send_session_reminders",
    "generate_recurring_sessions": "apps.scheduling.tasks.generate_recurring_sessions",
    "expire_trials": "apps.payments.tasks.expire_trials",
    "expire_grace_periods": "apps.payments.tasks.expire_grace_periods",
    "expire_platform_trials": "apps.payments.tasks.expire_platform_trials",
    "send_trial_reminder_emails": "apps.payments.tasks.send_trial_reminder_emails",
}


def _import_task(dotted_path):
    """Import and return the task function from a dotted path."""
    module_path, func_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def _check_auth(request):
    """Validate Bearer token. Returns None if valid, or error JsonResponse."""
    cron_key = getattr(settings, "CRON_API_KEY", "") or ""
    if not cron_key:
        logger.error("CRON_API_KEY not configured")
        return JsonResponse({"error": "CRON_API_KEY not configured"}, status=500)

    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Missing or invalid Authorization header"}, status=403)

    token = auth_header[7:]  # Strip "Bearer "
    if not hmac.compare_digest(token, cron_key):
        return JsonResponse({"error": "Invalid API key"}, status=403)

    return None


@csrf_exempt
@require_POST
def cron_run_tasks(request):
    """
    Run one or more scheduled tasks synchronously.

    Request body: {"tasks": ["task_name", ...]} or {"tasks": ["all"]}
    Response: {"results": {"task_name": {"status": "ok", "result": ...}, ...}}
    Status codes: 200 (all ok), 207 (partial failure), 400 (bad request), 403 (auth failed)
    """
    auth_error = _check_auth(request)
    if auth_error:
        return auth_error

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    task_names = body.get("tasks", [])
    if not isinstance(task_names, list) or not task_names:
        return JsonResponse({"error": "\"tasks\" must be a non-empty list"}, status=400)

    # Resolve "all" to all registered tasks
    if task_names == ["all"]:
        task_names = list(TASK_REGISTRY.keys())

    # Validate all task names first
    unknown = [t for t in task_names if t not in TASK_REGISTRY]
    if unknown:
        return JsonResponse(
            {"error": f"Unknown tasks: {', '.join(unknown)}",
             "available": list(TASK_REGISTRY.keys())},
            status=400,
        )

    results = {}
    has_failure = False

    for name in task_names:
        start = time.monotonic()
        try:
            func = _import_task(TASK_REGISTRY[name])
            result = func()
            elapsed = round(time.monotonic() - start, 3)
            results[name] = {"status": "ok", "result": result, "elapsed_seconds": elapsed}
            logger.info("Cron task %s completed in %.3fs", name, elapsed)
        except Exception:
            elapsed = round(time.monotonic() - start, 3)
            logger.exception("Cron task %s failed", name)
            results[name] = {"status": "error", "elapsed_seconds": elapsed}
            has_failure = True

    status_code = 207 if has_failure else 200
    return JsonResponse({"results": results}, status=status_code)
