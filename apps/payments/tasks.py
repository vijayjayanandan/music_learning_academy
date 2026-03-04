import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
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


@shared_task
def send_payment_confirmation_email(payment_id):
    """Send payment confirmation email asynchronously."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from apps.payments.models import Payment

    try:
        payment = Payment.objects.select_related("student", "course", "subscription__plan").get(pk=payment_id)
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

    html_message = render_to_string("emails/payment_confirmation_email.html", {
        "user": user,
        "payment": payment,
        "description": description,
        "invoice_url": f"/payments/invoice/{payment.pk}/",
    })

    send_mail(
        subject=f"Payment Confirmed - {payment.invoice_number}",
        message=f"Your payment of {payment.amount_display} has been confirmed. Invoice: {payment.invoice_number}",
        from_email=None,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )
    logger.info("Sent payment confirmation email for payment %s to %s", payment_id, user.email)
