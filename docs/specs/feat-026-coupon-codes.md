# FEAT-026: Coupon Codes

## Status: Done

## Summary
Academy owners can create and manage discount coupons (percentage or fixed amount). Coupons are applied during Stripe Checkout and tracked for usage limits and expiry.

## Models
- Coupon (`apps/payments/models.py`): code, discount_type (percentage/fixed_amount), discount_value, max_uses (0=unlimited), times_used, expires_at, is_active, applicable_courses (M2M). unique_together on (academy, code). Property `is_valid` checks active, usage limits, and expiry.

## Views
- CouponManageView (`apps/payments/views.py`) -- GET lists all coupons for the academy; POST creates a new coupon. Restricted to owners only.
- CheckoutView (`apps/payments/views.py`) -- accepts coupon_code via GET param or POST field, validates and passes to Stripe service.

## Service Layer
- _build_stripe_coupon (`apps/payments/stripe_service.py`) -- creates a Stripe Coupon object from local Coupon (percent_off or amount_off)
- _apply_discount -- adds discount to Stripe session params
- _increment_coupon_usage -- increments times_used on webhook completion

## URLs
- `/payments/coupons/` -- `coupon-manage`

## Templates
- `templates/payments/coupons.html`

## Tests
- TestCoupons in `tests/integration/test_release3_features.py` -- model fields, coupon validity, expired coupon invalid, manage view loads, create coupon via POST
