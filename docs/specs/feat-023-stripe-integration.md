# FEAT-023: Stripe Integration

## Status: Done

## Summary
Stripe Checkout Sessions handle course purchases and subscription payments. Webhooks process completed checkouts to create Payment, Enrollment, and Subscription records.

## Models
- Payment (`apps/payments/models.py`): student, amount_cents, currency, status (pending/completed/failed/refunded), payment_type (course/subscription/package), stripe_payment_intent_id, stripe_checkout_session_id, course (FK), subscription (FK), invoice_number (auto-generated), paid_at.

## Views
- CheckoutView (`apps/payments/views.py`) -- GET shows checkout page for a plan or course (with optional coupon); POST creates a Stripe Checkout Session and redirects to Stripe. Free courses bypass Stripe and enroll directly.
- PaymentSuccessView (`apps/payments/views.py`) -- success landing page after Stripe redirect
- StripeWebhookView (`apps/payments/views.py`) -- CSRF-exempt, rate-limited (100/min). Handles checkout.session.completed, customer.subscription.updated, customer.subscription.deleted events.

## Service Layer
- `apps/payments/stripe_service.py` -- create_checkout_session_for_plan, create_checkout_session_for_course, create_checkout_session_for_package, handle_checkout_completed, handle_subscription_updated/deleted, construct_webhook_event

## URLs
- `/payments/checkout/plan/<int:plan_id>/` -- `checkout-plan`
- `/payments/checkout/course/<slug:course_slug>/` -- `checkout-course`
- `/payments/success/` -- `payment-success`
- `/payments/webhook/` -- `stripe-webhook`

## Templates
- `templates/payments/checkout.html`
- `templates/payments/success.html`

## Tests
- TestStripePayments in `tests/integration/test_release3_features.py` -- model fields, auto invoice number, payment history view
