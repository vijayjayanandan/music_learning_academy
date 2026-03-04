# FEAT-025: Free Trial Period

## Status: Done

## Summary
Subscription plans can include a free trial period (in days). Stripe Checkout sessions are created with trial_period_days. A Celery task expires trials daily.

## Models
- SubscriptionPlan (`apps/payments/models.py`): `trial_days` field (PositiveIntegerField, default=0).
- Subscription (`apps/payments/models.py`): `trial_end` (DateTimeField, nullable), status includes TRIALING choice.

## Service Layer
- create_checkout_session_for_plan (`apps/payments/stripe_service.py`) -- when plan.trial_days > 0, sets subscription_data.trial_period_days on the Stripe Checkout Session.

## Celery Tasks
- expire_trials (`apps/payments/tasks.py`) -- runs daily at 00:30 via Celery Beat. Finds subscriptions with status=trialing and trial_end in the past, bulk-updates them to expired.

## URLs
- No additional URLs; trial logic integrates into existing checkout and subscription flows.

## Tests
- TestFreeTrial in `tests/integration/test_release3_features.py` -- plan with trial_days, subscription in trialing status is_valid
