# FEAT-024: Subscription Plans

## Status: Done

## Summary
Academies can define subscription plans with different billing cycles (monthly/quarterly/annual). Students can subscribe, view their subscriptions, and cancel.

## Models
- SubscriptionPlan (`apps/payments/models.py`): name, description, price_cents, currency, billing_cycle (monthly/quarterly/annual), is_active, trial_days, stripe_price_id, features (JSONField list).
- Subscription (`apps/payments/models.py`): student, plan (FK SubscriptionPlan), status (active/trialing/past_due/cancelled/expired), stripe_subscription_id, current_period_start/end, trial_end, cancelled_at. Property `is_valid` returns True if active or trialing.

## Views
- PricingView (`apps/payments/views.py`) -- displays active plans and packages for the academy
- MySubscriptionsView (`apps/payments/views.py`) -- lists student's subscriptions
- SubscriptionDetailView (`apps/payments/views.py`) -- shows subscription details
- CancelSubscriptionView (`apps/payments/views.py`) -- cancels on Stripe (cancel_at_period_end) and updates local status

## URLs
- `/payments/pricing/` -- `pricing`
- `/payments/subscriptions/` -- `my-subscriptions`
- `/payments/subscriptions/<int:pk>/` -- `subscription-detail`
- `/payments/subscriptions/<int:pk>/cancel/` -- `cancel-subscription`

## Templates
- `templates/payments/pricing.html`
- `templates/payments/my_subscriptions.html`
- `templates/payments/subscription_detail.html`

## Tests
- TestSubscriptionPlans in `tests/integration/test_release3_features.py` -- model fields, pricing page loads, create subscription, is_valid property, my-subscriptions view
