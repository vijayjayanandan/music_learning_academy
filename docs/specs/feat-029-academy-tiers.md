# FEAT-029: Academy Subscription Tiers

## Status: Done

## Summary
Platform-level subscription tiers (Free/Pro/Enterprise) that control academy limits on students, instructors, and courses. Academy model has FK to AcademyTier.

## Models
- AcademyTier (`apps/payments/models.py`): name, tier_level (free/pro/enterprise), price_cents, max_students, max_instructors, max_courses, features (JSON), is_active
- Academy.tier (`apps/academies/models.py`): FK to AcademyTier (nullable)

## Views
- AcademyTierView (`apps/payments/views.py`) — Public page displaying available platform tiers. No authentication required.

## URLs
- `/payments/tiers/` — `academy-tiers`

## Templates
- `templates/payments/tiers.html`

## Tests
- TestAcademyTiers in `tests/integration/test_release3_features.py`
