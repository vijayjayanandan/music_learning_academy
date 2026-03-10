"""
Stripe service module for Music Learning Academy.

Provides all Stripe API interactions for subscriptions, one-time course
purchases, and package deal purchases. Handles webhook event processing
to synchronise Stripe state with local database records.
"""

import logging
from datetime import datetime

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.payments.models import (
    Coupon,
    PackageDeal,
    PackagePurchase,
    Payment,
    Subscription,
    SubscriptionPlan,
)

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# ---------------------------------------------------------------------------
# Billing-cycle to Stripe interval mapping
# ---------------------------------------------------------------------------
BILLING_CYCLE_TO_STRIPE_INTERVAL = {
    SubscriptionPlan.BillingCycle.MONTHLY: ("month", 1),
    SubscriptionPlan.BillingCycle.QUARTERLY: ("month", 3),
    SubscriptionPlan.BillingCycle.ANNUAL: ("year", 1),
}


# ---------------------------------------------------------------------------
# Customer management
# ---------------------------------------------------------------------------


def get_or_create_stripe_customer(user: User) -> str:
    """
    Return the Stripe Customer ID for the given user, creating one if it
    does not already exist.  The ID is persisted on the User record.
    """
    if user.stripe_customer_id:
        return user.stripe_customer_id

    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name() or user.email,
            metadata={
                "user_id": str(user.pk),
            },
        )
        user.stripe_customer_id = customer.id
        user.save(update_fields=["stripe_customer_id"])
        logger.info("Created Stripe customer %s for user %s", customer.id, user.pk)
        return customer.id
    except stripe.error.StripeError:
        logger.exception("Failed to create Stripe customer for user %s", user.pk)
        raise


# ---------------------------------------------------------------------------
# Checkout session builders
# ---------------------------------------------------------------------------


def _build_stripe_coupon(coupon: Coupon) -> str:
    """
    Create a one-off Stripe Coupon object from a local Coupon and return its
    ID.  Percentage coupons map to ``percent_off``; fixed-amount coupons map
    to ``amount_off`` (in the smallest currency unit).
    """
    try:
        params = {
            "name": coupon.code,
            "metadata": {"coupon_id": str(coupon.pk)},
        }
        if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
            params["percent_off"] = coupon.discount_value
        else:
            params["amount_off"] = coupon.discount_value
            params["currency"] = "usd"

        stripe_coupon = stripe.Coupon.create(**params)
        return stripe_coupon.id
    except stripe.error.StripeError:
        logger.exception("Failed to create Stripe coupon for coupon %s", coupon.pk)
        raise


def _apply_discount(session_params: dict, coupon: Coupon | None) -> None:
    """Mutate *session_params* in place to add a discount when a coupon is provided."""
    if coupon is None:
        return
    stripe_coupon_id = _build_stripe_coupon(coupon)
    session_params["discounts"] = [{"coupon": stripe_coupon_id}]


def create_checkout_session_for_plan(
    user: User,
    plan: SubscriptionPlan,
    academy,
    success_url: str,
    cancel_url: str,
    coupon: Coupon | None = None,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout Session in ``subscription`` mode for the given
    plan.  If the plan has ``trial_days`` set, a trial period is configured.
    Returns the Stripe Session object.
    """
    customer_id = get_or_create_stripe_customer(user)

    interval, interval_count = BILLING_CYCLE_TO_STRIPE_INTERVAL.get(
        plan.billing_cycle, ("month", 1)
    )

    metadata = {
        "payment_type": "subscription",
        "academy_id": str(academy.pk),
        "user_id": str(user.pk),
        "plan_id": str(plan.pk),
    }
    if coupon is not None:
        metadata["coupon_code"] = coupon.code

    session_params: dict = {
        "mode": "subscription",
        "customer": customer_id,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata,
        "line_items": [
            {
                "price_data": {
                    "currency": plan.currency.lower(),
                    "product_data": {
                        "name": plan.name,
                        "description": plan.description or f"{plan.name} subscription",
                    },
                    "unit_amount": plan.price_cents,
                    "recurring": {
                        "interval": interval,
                        "interval_count": interval_count,
                    },
                },
                "quantity": 1,
            }
        ],
    }

    # Trial period
    subscription_data: dict = {}
    if plan.trial_days and plan.trial_days > 0:
        subscription_data["trial_period_days"] = plan.trial_days
    if subscription_data:
        session_params["subscription_data"] = subscription_data

    _apply_discount(session_params, coupon)

    try:
        session = stripe.checkout.Session.create(**session_params)
        logger.info(
            "Created Stripe checkout session %s for plan %s (user %s)",
            session.id,
            plan.pk,
            user.pk,
        )
        return session
    except stripe.error.StripeError:
        logger.exception(
            "Failed to create checkout session for plan %s (user %s)",
            plan.pk,
            user.pk,
        )
        raise


def create_checkout_session_for_course(
    user: User,
    course: Course,
    academy,
    success_url: str,
    cancel_url: str,
    coupon: Coupon | None = None,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout Session in ``payment`` mode for a one-time
    course purchase.  Returns the Stripe Session object.
    """
    customer_id = get_or_create_stripe_customer(user)

    metadata = {
        "payment_type": "course",
        "academy_id": str(academy.pk),
        "user_id": str(user.pk),
        "course_slug": course.slug,
    }
    if coupon is not None:
        metadata["coupon_code"] = coupon.code

    session_params: dict = {
        "mode": "payment",
        "customer": customer_id,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata,
        "line_items": [
            {
                "price_data": {
                    "currency": course.currency.lower(),
                    "product_data": {
                        "name": course.title,
                        "description": (course.description or course.title)[:500],
                    },
                    "unit_amount": course.price_cents,
                },
                "quantity": 1,
            }
        ],
    }

    _apply_discount(session_params, coupon)

    try:
        session = stripe.checkout.Session.create(**session_params)
        logger.info(
            "Created Stripe checkout session %s for course '%s' (user %s)",
            session.id,
            course.slug,
            user.pk,
        )
        return session
    except stripe.error.StripeError:
        logger.exception(
            "Failed to create checkout session for course '%s' (user %s)",
            course.slug,
            user.pk,
        )
        raise


def create_checkout_session_for_package(
    user: User,
    package: PackageDeal,
    academy,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout Session in ``payment`` mode for a package deal
    purchase.  Returns the Stripe Session object.
    """
    customer_id = get_or_create_stripe_customer(user)

    metadata = {
        "payment_type": "package",
        "academy_id": str(academy.pk),
        "user_id": str(user.pk),
        "package_id": str(package.pk),
    }

    session_params: dict = {
        "mode": "payment",
        "customer": customer_id,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata,
        "line_items": [
            {
                "price_data": {
                    "currency": package.currency.lower(),
                    "product_data": {
                        "name": package.name,
                        "description": package.description
                        or f"{package.name} ({package.total_credits} credits)",
                    },
                    "unit_amount": package.price_cents,
                },
                "quantity": 1,
            }
        ],
    }

    try:
        session = stripe.checkout.Session.create(**session_params)
        logger.info(
            "Created Stripe checkout session %s for package %s (user %s)",
            session.id,
            package.pk,
            user.pk,
        )
        return session
    except stripe.error.StripeError:
        logger.exception(
            "Failed to create checkout session for package %s (user %s)",
            package.pk,
            user.pk,
        )
        raise


# ---------------------------------------------------------------------------
# Webhook event handlers
# ---------------------------------------------------------------------------


def _timestamp_to_datetime(ts: int | None) -> datetime | None:
    """Convert a Unix timestamp from Stripe to a timezone-aware datetime."""
    if ts is None:
        return None
    return timezone.make_aware(
        datetime.utcfromtimestamp(ts),
        timezone=timezone.utc,
    )


@transaction.atomic
def handle_checkout_completed(session: stripe.checkout.Session) -> None:
    """
    Process a ``checkout.session.completed`` event.

    Dispatches to the appropriate handler based on the ``payment_type``
    stored in the session metadata:
      - ``subscription`` -- creates Subscription + Payment records
      - ``course``       -- creates Payment + Enrollment records
      - ``package``      -- creates Payment + PackagePurchase records
    """
    metadata = session.get("metadata", {}) or {}
    payment_type = metadata.get("payment_type")
    academy_id = metadata.get("academy_id")
    user_id = metadata.get("user_id")

    if not payment_type or not academy_id or not user_id:
        logger.error(
            "Checkout session %s missing required metadata (payment_type=%s, "
            "academy_id=%s, user_id=%s)",
            session.id,
            payment_type,
            academy_id,
            user_id,
        )
        return

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error(
            "User %s from checkout session %s does not exist", user_id, session.id
        )
        return

    from apps.academies.models import Academy

    try:
        academy = Academy.objects.get(pk=academy_id)
    except Academy.DoesNotExist:
        logger.error(
            "Academy %s from checkout session %s does not exist", academy_id, session.id
        )
        return

    # Idempotency: skip if we already processed this checkout session
    if Payment.objects.filter(stripe_checkout_session_id=session.id).exists():
        logger.info(
            "Checkout session %s already processed — skipping (idempotent)", session.id
        )
        return

    if payment_type == "subscription":
        _handle_subscription_checkout(session, metadata, user, academy)
    elif payment_type == "course":
        _handle_course_checkout(session, metadata, user, academy)
    elif payment_type == "package":
        _handle_package_checkout(session, metadata, user, academy)
    else:
        logger.warning(
            "Unknown payment_type '%s' in checkout session %s", payment_type, session.id
        )


def _handle_subscription_checkout(
    session: stripe.checkout.Session,
    metadata: dict,
    user: User,
    academy,
) -> None:
    """Create Subscription and Payment records after a subscription checkout."""
    plan_id = metadata.get("plan_id")
    if not plan_id:
        logger.error("Checkout session %s missing plan_id in metadata", session.id)
        return

    try:
        plan = SubscriptionPlan.objects.get(pk=plan_id, academy=academy)
    except SubscriptionPlan.DoesNotExist:
        logger.error(
            "SubscriptionPlan %s not found for academy %s", plan_id, academy.pk
        )
        return

    stripe_subscription_id = session.get("subscription", "")

    # Fetch the full subscription object from Stripe for period details
    stripe_sub = None
    if stripe_subscription_id:
        try:
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        except stripe.error.StripeError:
            logger.warning(
                "Could not retrieve Stripe subscription %s; proceeding with limited data",
                stripe_subscription_id,
            )

    status = Subscription.Status.ACTIVE
    current_period_start = None
    current_period_end = None
    trial_end = None

    if stripe_sub:
        stripe_status = stripe_sub.get("status", "active")
        status_map = {
            "active": Subscription.Status.ACTIVE,
            "trialing": Subscription.Status.TRIALING,
            "past_due": Subscription.Status.PAST_DUE,
            "canceled": Subscription.Status.CANCELLED,
            "unpaid": Subscription.Status.PAST_DUE,
        }
        status = status_map.get(stripe_status, Subscription.Status.ACTIVE)
        current_period_start = _timestamp_to_datetime(
            stripe_sub.get("current_period_start")
        )
        current_period_end = _timestamp_to_datetime(
            stripe_sub.get("current_period_end")
        )
        trial_end = _timestamp_to_datetime(stripe_sub.get("trial_end"))

    subscription = Subscription.objects.create(
        academy=academy,
        student=user,
        plan=plan,
        status=status,
        stripe_subscription_id=stripe_subscription_id or "",
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        trial_end=trial_end,
    )

    amount_total = session.get("amount_total", 0) or 0

    payment = Payment.objects.create(
        academy=academy,
        student=user,
        amount_cents=amount_total,
        currency=plan.currency,
        status=Payment.Status.COMPLETED,
        payment_type=Payment.PaymentType.SUBSCRIPTION,
        stripe_payment_intent_id=session.get("payment_intent", "") or "",
        stripe_checkout_session_id=session.id,
        subscription=subscription,
        description=f"Subscription: {plan.name}",
        paid_at=timezone.now(),
    )

    # Increment coupon usage if applicable
    _increment_coupon_usage(metadata, academy)

    # Send payment confirmation email
    try:
        from apps.payments.tasks import send_payment_confirmation_email

        send_payment_confirmation_email(payment.pk)
    except Exception:
        logger.warning(
            "Could not send payment confirmation email for payment %s", payment.pk
        )

    logger.info(
        "Created subscription %s and payment for user %s, plan %s",
        subscription.pk,
        user.pk,
        plan.pk,
    )


def _handle_course_checkout(
    session: stripe.checkout.Session,
    metadata: dict,
    user: User,
    academy,
) -> None:
    """Create Payment and Enrollment records after a course purchase."""
    course_slug = metadata.get("course_slug")
    if not course_slug:
        logger.error("Checkout session %s missing course_slug in metadata", session.id)
        return

    try:
        course = Course.objects.get(slug=course_slug, academy=academy)
    except Course.DoesNotExist:
        logger.error("Course '%s' not found for academy %s", course_slug, academy.pk)
        return

    amount_total = session.get("amount_total", 0) or 0

    payment = Payment.objects.create(
        academy=academy,
        student=user,
        amount_cents=amount_total,
        currency=course.currency,
        status=Payment.Status.COMPLETED,
        payment_type=Payment.PaymentType.COURSE,
        stripe_payment_intent_id=session.get("payment_intent", "") or "",
        stripe_checkout_session_id=session.id,
        course=course,
        description=f"Course purchase: {course.title}",
        paid_at=timezone.now(),
    )

    # Create or reactivate enrollment
    enrollment, created = Enrollment.objects.get_or_create(
        student=user,
        course=course,
        defaults={
            "academy": academy,
            "status": Enrollment.Status.ACTIVE,
        },
    )
    if not created and enrollment.status != Enrollment.Status.ACTIVE:
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

    _increment_coupon_usage(metadata, academy)

    try:
        from apps.payments.tasks import send_payment_confirmation_email

        send_payment_confirmation_email(payment.pk)
    except Exception:
        logger.warning(
            "Could not send payment confirmation email for payment %s", payment.pk
        )

    logger.info(
        "Created payment %s and enrollment for user %s, course '%s'",
        payment.pk,
        user.pk,
        course.slug,
    )


def _handle_package_checkout(
    session: stripe.checkout.Session,
    metadata: dict,
    user: User,
    academy,
) -> None:
    """Create Payment and PackagePurchase records after a package purchase."""
    package_id = metadata.get("package_id")
    if not package_id:
        logger.error("Checkout session %s missing package_id in metadata", session.id)
        return

    try:
        package = PackageDeal.objects.get(pk=package_id, academy=academy)
    except PackageDeal.DoesNotExist:
        logger.error("PackageDeal %s not found for academy %s", package_id, academy.pk)
        return

    amount_total = session.get("amount_total", 0) or 0

    payment = Payment.objects.create(
        academy=academy,
        student=user,
        amount_cents=amount_total,
        currency=package.currency,
        status=Payment.Status.COMPLETED,
        payment_type=Payment.PaymentType.PACKAGE,
        stripe_payment_intent_id=session.get("payment_intent", "") or "",
        stripe_checkout_session_id=session.id,
        description=f"Package purchase: {package.name}",
        paid_at=timezone.now(),
    )

    PackagePurchase.objects.create(
        academy=academy,
        student=user,
        package=package,
        credits_remaining=package.total_credits,
        payment=payment,
    )

    logger.info(
        "Created payment %s and package purchase for user %s, package %s",
        payment.pk,
        user.pk,
        package.pk,
    )


def _increment_coupon_usage(metadata: dict, academy) -> None:
    """Increment the ``times_used`` counter on the coupon if one was applied."""
    coupon_code = metadata.get("coupon_code")
    if not coupon_code:
        return
    try:
        coupon = Coupon.objects.get(code=coupon_code, academy=academy)
        coupon.times_used += 1
        coupon.save(update_fields=["times_used"])
    except Coupon.DoesNotExist:
        logger.warning(
            "Coupon '%s' referenced in metadata not found for academy %s",
            coupon_code,
            academy.pk,
        )


# ---------------------------------------------------------------------------
# Subscription lifecycle handlers
# ---------------------------------------------------------------------------


def handle_subscription_updated(stripe_subscription: stripe.Subscription) -> None:
    """
    Handle a ``customer.subscription.updated`` event.  Updates the local
    Subscription record with the latest status and period information from
    Stripe.
    """
    stripe_sub_id = stripe_subscription.get("id", "")

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
    except Subscription.DoesNotExist:
        logger.warning(
            "Received subscription.updated for unknown Stripe subscription %s",
            stripe_sub_id,
        )
        return

    stripe_status = stripe_subscription.get("status", "")
    status_map = {
        "active": Subscription.Status.ACTIVE,
        "trialing": Subscription.Status.TRIALING,
        "past_due": Subscription.Status.PAST_DUE,
        "canceled": Subscription.Status.CANCELLED,
        "unpaid": Subscription.Status.PAST_DUE,
        "incomplete": Subscription.Status.PAST_DUE,
        "incomplete_expired": Subscription.Status.EXPIRED,
    }
    new_status = status_map.get(stripe_status)
    if new_status is None:
        logger.warning(
            "Unmapped Stripe subscription status '%s' for subscription %s",
            stripe_status,
            subscription.pk,
        )
        return

    subscription.status = new_status
    subscription.current_period_start = _timestamp_to_datetime(
        stripe_subscription.get("current_period_start"),
    )
    subscription.current_period_end = _timestamp_to_datetime(
        stripe_subscription.get("current_period_end"),
    )
    subscription.trial_end = _timestamp_to_datetime(
        stripe_subscription.get("trial_end"),
    )

    if new_status == Subscription.Status.CANCELLED and not subscription.cancelled_at:
        subscription.cancelled_at = timezone.now()

    subscription.save(
        update_fields=[
            "status",
            "current_period_start",
            "current_period_end",
            "trial_end",
            "cancelled_at",
            "updated_at",
        ],
    )

    logger.info(
        "Updated subscription %s (stripe=%s) to status '%s'",
        subscription.pk,
        stripe_sub_id,
        new_status,
    )


def handle_subscription_deleted(stripe_subscription: stripe.Subscription) -> None:
    """
    Handle a ``customer.subscription.deleted`` event.  Marks the local
    Subscription as cancelled.
    """
    stripe_sub_id = stripe_subscription.get("id", "")

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
    except Subscription.DoesNotExist:
        logger.warning(
            "Received subscription.deleted for unknown Stripe subscription %s",
            stripe_sub_id,
        )
        return

    subscription.status = Subscription.Status.CANCELLED
    if not subscription.cancelled_at:
        subscription.cancelled_at = timezone.now()

    subscription.save(update_fields=["status", "cancelled_at", "updated_at"])

    logger.info(
        "Marked subscription %s (stripe=%s) as cancelled",
        subscription.pk,
        stripe_sub_id,
    )


# ---------------------------------------------------------------------------
# Subscription cancellation
# ---------------------------------------------------------------------------


def cancel_stripe_subscription(subscription: Subscription) -> None:
    """
    Cancel a subscription on Stripe and update the local record.

    Uses ``cancel_at_period_end`` so the customer retains access until the
    end of their current billing period.
    """
    if not subscription.stripe_subscription_id:
        logger.warning(
            "Cannot cancel subscription %s: no Stripe subscription ID",
            subscription.pk,
        )
        subscription.status = Subscription.Status.CANCELLED
        subscription.cancelled_at = timezone.now()
        subscription.save(update_fields=["status", "cancelled_at", "updated_at"])
        return

    try:
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        logger.info(
            "Set cancel_at_period_end for Stripe subscription %s",
            subscription.stripe_subscription_id,
        )
    except stripe.error.StripeError:
        logger.exception(
            "Failed to cancel Stripe subscription %s",
            subscription.stripe_subscription_id,
        )
        raise

    subscription.cancelled_at = timezone.now()
    subscription.save(update_fields=["cancelled_at", "updated_at"])


# ---------------------------------------------------------------------------
# Webhook event construction / verification
# ---------------------------------------------------------------------------


def construct_webhook_event(
    payload: bytes,
    sig_header: str,
) -> stripe.Event:
    """
    Verify the webhook signature and construct a ``stripe.Event`` from the
    raw request payload and the ``Stripe-Signature`` header value.

    Raises ``stripe.error.SignatureVerificationError`` if the signature is
    invalid.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
        return event
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise
    except ValueError:
        logger.warning("Invalid Stripe webhook payload")
        raise


# ---------------------------------------------------------------------------
# Invoice payment failure → grace period
# ---------------------------------------------------------------------------


def handle_invoice_payment_failed(event_data: dict) -> None:
    """
    Handle invoice.payment_failed — triggers grace period for platform
    subscriptions or marks student subscriptions as past_due.
    """
    from apps.payments.models import PlatformSubscription
    from datetime import timedelta

    stripe_sub_id = event_data.get("subscription", "")
    if not stripe_sub_id:
        logger.warning("invoice.payment_failed missing subscription ID")
        return

    # Check platform subscription first
    try:
        platform_sub = PlatformSubscription.objects.get(
            stripe_subscription_id=stripe_sub_id,
        )
        platform_sub.status = PlatformSubscription.Status.GRACE
        platform_sub.grace_period_ends_at = timezone.now() + timedelta(days=7)
        platform_sub.save(
            update_fields=["status", "grace_period_ends_at", "updated_at"]
        )
        logger.info(
            "Platform subscription %s moved to grace period (ends %s)",
            platform_sub.pk,
            platform_sub.grace_period_ends_at,
        )
        return
    except PlatformSubscription.DoesNotExist:
        pass

    # Fall back to student subscription
    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=stripe_sub_id,
        )
        subscription.status = Subscription.Status.PAST_DUE
        subscription.save(update_fields=["status", "updated_at"])
        logger.info(
            "Student subscription %s marked as past_due",
            subscription.pk,
        )
    except Subscription.DoesNotExist:
        logger.warning(
            "invoice.payment_failed for unknown subscription %s",
            stripe_sub_id,
        )
