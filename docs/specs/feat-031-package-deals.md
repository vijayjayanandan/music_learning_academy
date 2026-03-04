# FEAT-031: Package Deals

## Status: Done

## Summary
Bundled session/lesson packages with credit-based tracking. Students purchase packages via Stripe checkout and use credits for sessions.

## Models
- PackageDeal (`apps/payments/models.py`): name, description, price_cents, currency, total_credits, is_active, courses (M2M to Course)
- PackagePurchase (`apps/payments/models.py`): student (FK User), package (FK PackageDeal), credits_remaining, payment (FK Payment)

## Views
- PackagePurchaseView (`apps/payments/views.py`) — POST initiates Stripe checkout for a package deal. Redirects to Stripe or back to pricing on error.
- MyPackagesView (`apps/payments/views.py`) — Lists student's purchased packages with remaining credits.
- PricingView (`apps/payments/views.py`) — Also displays active packages alongside subscription plans.

## URLs
- `/payments/packages/` — `my-packages`
- `/payments/packages/<int:pk>/purchase/` — `package-purchase`

## Templates
- `templates/payments/my_packages.html`
- `templates/payments/pricing.html` (shared with FEAT-024)

## Tests
- TestPackageDeals in `tests/integration/test_release3_features.py`
