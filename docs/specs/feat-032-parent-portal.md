# FEAT-032: Parent/Guardian Portal

## Status: Done

## Summary
Parents can link child student accounts and view their enrollments and practice activity from a dedicated dashboard. Security checks prevent arbitrary account linking.

## Models
- User.parent (`apps/accounts/models.py`): FK to self (nullable), links child to parent
- User.is_parent (`apps/accounts/models.py`): BooleanField, set True when a child is linked

## Views
- ParentDashboardView (`apps/accounts/views.py`) — Shows all linked children with their enrollments and recent practice logs.
- LinkChildView (`apps/accounts/views.py`) — POST links a child account by email. Validates: no existing parent, not self, shared academy membership required.

## URLs
- `/accounts/parent-dashboard/` — `parent-dashboard`
- `/accounts/link-child/` — `link-child`

## Templates
- `templates/accounts/parent_dashboard.html`

## Tests
- TestParentPortal in `tests/integration/test_release3_features.py`
