# FEAT-028: Instructor Payout Management

## Status: Done

## Summary
Track and manage instructor payouts with period-based earnings, Stripe transfer integration, and role-based access (owners see all, instructors see their own).

## Models
- InstructorPayout (`apps/payments/models.py`): instructor (FK User), amount_cents, currency, status (pending/processing/completed/failed), period_start, period_end, stripe_transfer_id, notes, paid_at

## Views
- InstructorPayoutListView (`apps/payments/views.py`) — Lists payouts; owners see all academy payouts, instructors see only their own. Role-restricted to owner/instructor.

## URLs
- `/payments/payouts/` — `payout-list`

## Templates
- `templates/payments/payouts.html`

## Tests
- TestInstructorPayouts in `tests/integration/test_release3_features.py`
