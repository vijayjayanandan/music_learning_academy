# PROD-001: Rate Limiting on Auth Views

## Status: Done

## Summary
django-ratelimit applied to all sensitive authentication and webhook endpoints to prevent brute-force attacks and abuse.

## Implementation
- Login view: 5 attempts per 5 minutes (keyed by IP)
- Register view: 3 attempts per 10 minutes (keyed by IP)
- Password reset view: 3 attempts per 10 minutes (keyed by IP)
- Resend verification view: 2 attempts per 10 minutes (keyed by IP)
- Stripe webhook endpoint: 100 requests per minute
- Custom 429 Too Many Requests template with user-friendly messaging
- Global rate-limit middleware returns JSON for API requests, HTML for browser

## Files Modified/Created
- `apps/accounts/views.py` — `@ratelimit` decorators on login, register, password_reset, resend_verification
- `apps/payments/views.py` — `@ratelimit` on stripe_webhook
- `apps/common/middleware.py` — Custom `RateLimitMiddleware` for 429 handling
- `templates/429.html` — User-friendly rate limit error page
- `config/settings/base.py` — `RATELIMIT_VIEW` setting
- `requirements/base.txt` — added `django-ratelimit`

## Configuration
- `RATELIMIT_VIEW` in settings points to custom 429 handler
- Rate limits are hardcoded per view via decorators

## Verification
- Attempt 6 rapid logins with wrong password — should see 429 after 5th
- Verify 429.html renders with friendly message and retry guidance
