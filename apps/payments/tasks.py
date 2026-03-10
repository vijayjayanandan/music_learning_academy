import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def expire_trials():
    """Mark trialing subscriptions as expired when trial_end has passed."""
    from apps.payments.models import Subscription

    now = timezone.now()
    expired = Subscription.objects.filter(
        status=Subscription.Status.TRIALING,
        trial_end__lt=now,
    )
    count = expired.update(status=Subscription.Status.EXPIRED)
    if count:
        logger.info("Expired %d trial subscriptions", count)
    return count


def send_payment_confirmation_email(payment_id):
    """Send payment confirmation email asynchronously."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from apps.payments.models import Payment

    try:
        payment = Payment.objects.select_related(
            "student", "course", "subscription__plan"
        ).get(pk=payment_id)
    except Payment.DoesNotExist:
        logger.warning("Payment %s not found for email", payment_id)
        return

    user = payment.student
    if not user.wants_email("payment_confirmation"):
        return

    description = payment.description
    if payment.course:
        description = f"Course: {payment.course.title}"
    elif payment.subscription:
        description = f"Plan: {payment.subscription.plan.name}"

    html_message = render_to_string(
        "emails/payment_confirmation_email.html",
        {
            "user": user,
            "payment": payment,
            "description": description,
            "invoice_url": f"/payments/invoice/{payment.pk}/",
        },
    )

    send_mail(
        subject=f"Payment Confirmed - {payment.invoice_number}",
        message=f"Your payment of {payment.amount_display} has been confirmed. Invoice: {payment.invoice_number}",
        from_email=None,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )
    logger.info(
        "Sent payment confirmation email for payment %s to %s", payment_id, user.email
    )


def expire_platform_trials():
    """Mark PlatformSubscription trials as expired when trial_ends_at has passed."""
    from apps.payments.models import PlatformSubscription

    now = timezone.now()
    expired = PlatformSubscription.objects.filter(
        status=PlatformSubscription.Status.TRIAL,
        trial_ends_at__lt=now,
        stripe_subscription_id="",
    )
    count = expired.update(status=PlatformSubscription.Status.EXPIRED)
    if count:
        logger.info("Expired %d platform trials", count)
    return count


def send_trial_reminder_emails():
    """Send trial expiry reminder emails at 7d, 3d, and 1d before trial ends."""
    from apps.payments.models import PlatformSubscription
    from django.core.mail import send_mail
    from datetime import timedelta as td

    now = timezone.now()
    count = 0

    # 7-day reminder: trial_ends_at between now+5d and now+7d
    subs_7d = PlatformSubscription.objects.filter(
        status=PlatformSubscription.Status.TRIAL,
        trial_ends_at__gt=now,
        trial_ends_at__lte=now + td(days=7),
        trial_reminder_7d_sent=False,
    )
    for sub in subs_7d:
        send_mail(
            subject=f"{sub.academy.name} - 7 days left in trial",
            message="Your trial expires in 7 days.",
            from_email=None,
            recipient_list=[sub.academy.email],
            fail_silently=True,
        )
        sub.trial_reminder_7d_sent = True
        sub.save(update_fields=["trial_reminder_7d_sent"])
        count += 1

    # 3-day reminder: trial_ends_at between now and now+3d
    subs_3d = PlatformSubscription.objects.filter(
        status=PlatformSubscription.Status.TRIAL,
        trial_ends_at__gt=now,
        trial_ends_at__lte=now + td(days=3),
        trial_reminder_3d_sent=False,
    )
    for sub in subs_3d:
        send_mail(
            subject=f"{sub.academy.name} - 3 days left in trial",
            message="Your trial expires in 3 days.",
            from_email=None,
            recipient_list=[sub.academy.email],
            fail_silently=True,
        )
        sub.trial_reminder_3d_sent = True
        sub.save(update_fields=["trial_reminder_3d_sent"])
        count += 1

    # 1-day reminder: trial_ends_at between now and now+1d
    subs_1d = PlatformSubscription.objects.filter(
        status=PlatformSubscription.Status.TRIAL,
        trial_ends_at__gt=now,
        trial_ends_at__lte=now + td(days=1),
        trial_reminder_1d_sent=False,
    )
    for sub in subs_1d:
        send_mail(
            subject=f"{sub.academy.name} - Last day of trial!",
            message="Your trial expires tomorrow.",
            from_email=None,
            recipient_list=[sub.academy.email],
            fail_silently=True,
        )
        sub.trial_reminder_1d_sent = True
        sub.save(update_fields=["trial_reminder_1d_sent"])
        count += 1

    logger.info("Sent %d trial reminder emails", count)
    return count


def expire_grace_periods():
    """Expire platform subscriptions that are past their grace period."""
    from apps.payments.models import PlatformSubscription

    now = timezone.now()
    expired = PlatformSubscription.objects.filter(
        status=PlatformSubscription.Status.GRACE,
        grace_period_ends_at__lt=now,
    )
    count = expired.update(status=PlatformSubscription.Status.EXPIRED)
    if count:
        logger.info("Expired %d platform subscriptions past grace period", count)
    return count
