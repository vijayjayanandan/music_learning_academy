# PROD-002: Health Check Endpoint

## Status: Done

## Summary
/health/ endpoint that checks database, Redis, and Celery connectivity for load balancer and monitoring use.

## Implementation
- GET /health/ returns JSON `{status, checks: {database, redis, celery}}`
- Each check returns `ok` or `error` with optional detail message
- Overall status is `healthy` (HTTP 200) if all pass, `unhealthy` (HTTP 503) if any fail
- Database check: simple ORM query
- Redis check: ping via cache backend
- Celery check: inspect active workers

## Files Modified/Created
- `apps/common/views.py` — `health_check` view function
- `config/urls.py` — added `path('health/', health_check, name='health-check')`

## Configuration
- No additional configuration required
- Works with both SQLite (dev) and PostgreSQL (prod)
- Redis check skipped gracefully if cache backend is LocMemCache

## Verification
- `curl http://localhost:8001/health/` — should return 200 with JSON status
- Stop Redis/DB and verify 503 response with failed check details
