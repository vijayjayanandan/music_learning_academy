# PROD-004: Sentry Integration

## Status: Done

## Summary
Optional Sentry error tracking via SENTRY_DSN env var with Django, Celery, and Redis integrations.

## Implementation
- Sentry SDK initialized only when `SENTRY_DSN` environment variable is set
- Django integration: automatic exception capture, request data, user context
- Celery integration: captures task failures and retries
- Redis integration: tracks Redis connection issues
- Traces sample rate set to 10% for performance monitoring
- Environment tag set from `DJANGO_ENV` (defaults to `production`)

## Files Modified/Created
- `requirements/base.txt` — added `sentry-sdk[django,celery,redis]`
- `config/settings/prod.py` — `sentry_sdk.init()` with integrations
- `.env.example` — added `SENTRY_DSN` placeholder

## Configuration
- `SENTRY_DSN` — Sentry project DSN (optional; Sentry disabled if not set)
- `DJANGO_ENV` — environment name sent to Sentry (default: `production`)
- `SENTRY_TRACES_SAMPLE_RATE` — performance monitoring rate (default: `0.1`)

## Verification
- Set `SENTRY_DSN` and trigger a test error (e.g., visit a broken view)
- Verify error appears in Sentry dashboard with request context and user info
- Verify Celery task failures also appear in Sentry
