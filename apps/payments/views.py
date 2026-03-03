import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from .models import (
    SubscriptionPlan, Subscription, Payment, Coupon,
    InstructorPayout, PackageDeal, PackagePurchase, AcademyTier,
)

logger = logging.getLogger(__name__)


class PricingView(TenantMixin, View):
    """FEAT-024: Display available subscription plans."""

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(
            academy=self.get_academy(), is_active=True,
        )
        packages = PackageDeal.objects.filter(
            academy=self.get_academy(), is_active=True,
        )
        return render(request, "payments/pricing.html", {
            "plans": plans,
            "packages": packages,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        })


class CheckoutView(TenantMixin, View):
    """FEAT-023: Checkout via Stripe Checkout Sessions."""

    def get(self, request, plan_id=None, course_slug=None):
        context = {"stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY}
        if plan_id:
            plan = get_object_or_404(
                SubscriptionPlan, pk=plan_id, academy=self.get_academy(),
            )
            context["plan"] = plan
            context["amount"] = plan.price_display
        elif course_slug:
            from apps.courses.models import Course
            course = get_object_or_404(
                Course, slug=course_slug, academy=self.get_academy(),
            )
            context["course"] = course
        coupon_code = request.GET.get("coupon")
        if coupon_code:
            coupon = Coupon.objects.filter(
                academy=self.get_academy(), code=coupon_code, is_active=True,
            ).first()
            if coupon and coupon.is_valid:
                context["coupon"] = coupon
        return render(request, "payments/checkout.html", context)

    def post(self, request, plan_id=None, course_slug=None):
        from .stripe_service import (
            create_checkout_session_for_plan,
            create_checkout_session_for_course,
        )

        academy = self.get_academy()
        base_url = request.build_absolute_uri("/")
        success_url = base_url.rstrip("/") + reverse("payment-success") + "?session_id={CHECKOUT_SESSION_ID}"
        cancel_url = base_url.rstrip("/") + reverse("pricing")

        # Check for coupon
        coupon = None
        coupon_code = request.POST.get("coupon_code", "").strip().upper()
        if coupon_code:
            coupon = Coupon.objects.filter(
                academy=academy, code=coupon_code, is_active=True,
            ).first()
            if coupon and not coupon.is_valid:
                coupon = None

        try:
            if plan_id:
                plan = get_object_or_404(SubscriptionPlan, pk=plan_id, academy=academy)
                session = create_checkout_session_for_plan(
                    user=request.user,
                    plan=plan,
                    academy=academy,
                    success_url=success_url,
                    cancel_url=cancel_url,
                    coupon=coupon,
                )
            elif course_slug:
                from apps.courses.models import Course
                course = get_object_or_404(Course, slug=course_slug, academy=academy)
                if course.is_free:
                    # Free course — enroll directly, no Stripe
                    from apps.enrollments.models import Enrollment
                    Enrollment.objects.get_or_create(
                        student=request.user, course=course, academy=academy,
                    )
                    return redirect("course-detail", slug=course_slug)
                session = create_checkout_session_for_course(
                    user=request.user,
                    course=course,
                    academy=academy,
                    success_url=success_url,
                    cancel_url=cancel_url,
                    coupon=coupon,
                )
            else:
                return redirect("pricing")

            return redirect(session.url)

        except Exception:
            logger.exception("Failed to create Stripe checkout session")
            from django.contrib import messages
            messages.error(request, "Payment processing is temporarily unavailable. Please try again.")
            return redirect("pricing")


class PaymentSuccessView(TenantMixin, View):
    """Shown after Stripe redirects back on successful payment."""

    def get(self, request):
        session_id = request.GET.get("session_id")
        return render(request, "payments/success.html", {
            "session_id": session_id,
        })


class SubscriptionDetailView(TenantMixin, View):
    """View subscription details."""

    def get(self, request, pk):
        sub = get_object_or_404(
            Subscription, pk=pk, student=request.user,
        )
        return render(request, "payments/subscription_detail.html", {"subscription": sub})


class CancelSubscriptionView(TenantMixin, View):
    """Cancel a subscription (also cancels on Stripe)."""

    def post(self, request, pk):
        sub = get_object_or_404(
            Subscription, pk=pk, student=request.user,
        )
        # Cancel on Stripe if connected
        if sub.stripe_subscription_id:
            try:
                from .stripe_service import cancel_stripe_subscription
                cancel_stripe_subscription(sub)
            except Exception:
                logger.exception("Failed to cancel Stripe subscription %s", sub.stripe_subscription_id)
        sub.status = Subscription.Status.CANCELLED
        sub.cancelled_at = timezone.now()
        sub.save()
        return redirect("my-subscriptions")


class MySubscriptionsView(TenantMixin, ListView):
    """List student's subscriptions."""
    model = Subscription
    template_name = "payments/my_subscriptions.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return Subscription.objects.filter(
            student=self.request.user, academy=self.get_academy(),
        )


class PaymentHistoryView(TenantMixin, ListView):
    """FEAT-027: Payment history / invoices."""
    model = Payment
    template_name = "payments/payment_history.html"
    context_object_name = "payments"
    paginate_by = 20

    def get_queryset(self):
        return Payment.objects.filter(
            student=self.request.user, academy=self.get_academy(),
        )


class InvoiceDetailView(TenantMixin, View):
    """FEAT-027: Invoice detail / printable."""

    def get(self, request, pk):
        payment = get_object_or_404(
            Payment, pk=pk, student=request.user,
        )
        return render(request, "payments/invoice.html", {"payment": payment})


class CouponManageView(TenantMixin, View):
    """FEAT-026: Manage coupons (admin)."""

    def dispatch(self, request, *args, **kwargs):
        # Security: only owners can manage coupons
        if hasattr(request, 'academy') and request.academy:
            role = request.user.get_role_in(request.academy)
            if role != "owner":
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Only academy owners can manage coupons.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        coupons = Coupon.objects.filter(academy=self.get_academy())
        return render(request, "payments/coupons.html", {"coupons": coupons})

    def post(self, request):
        # Security: validate input values
        try:
            discount_value = max(0, int(request.POST.get("discount_value", 10)))
            max_uses = max(0, int(request.POST.get("max_uses", 0)))
        except (ValueError, TypeError):
            discount_value = 10
            max_uses = 0
        discount_type = request.POST.get("discount_type", "percentage")
        if discount_type not in ("percentage", "fixed"):
            discount_type = "percentage"
        Coupon.objects.create(
            academy=self.get_academy(),
            code=request.POST.get("code", "").upper().strip(),
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
        )
        return redirect("coupon-manage")


class InstructorPayoutListView(TenantMixin, ListView):
    """FEAT-028: Instructor payout list."""
    model = InstructorPayout
    template_name = "payments/payouts.html"
    context_object_name = "payouts"

    def dispatch(self, request, *args, **kwargs):
        # Security: only owners and instructors can view payouts
        if hasattr(request, 'academy') and request.academy:
            role = request.user.get_role_in(request.academy)
            if role not in ("owner", "instructor"):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("You do not have permission to view payouts.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        role = user.get_role_in(self.get_academy())
        if role == "owner":
            return InstructorPayout.objects.filter(academy=self.get_academy())
        return InstructorPayout.objects.filter(
            instructor=user, academy=self.get_academy(),
        )


class PackagePurchaseView(TenantMixin, View):
    """FEAT-031: Purchase a package deal via Stripe."""

    def post(self, request, pk):
        from .stripe_service import create_checkout_session_for_package

        package = get_object_or_404(
            PackageDeal, pk=pk, academy=self.get_academy(), is_active=True,
        )
        base_url = request.build_absolute_uri("/")
        success_url = base_url.rstrip("/") + reverse("payment-success") + "?session_id={CHECKOUT_SESSION_ID}"
        cancel_url = base_url.rstrip("/") + reverse("pricing")

        try:
            session = create_checkout_session_for_package(
                user=request.user,
                package=package,
                academy=self.get_academy(),
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return redirect(session.url)
        except Exception:
            logger.exception("Failed to create Stripe checkout for package %s", pk)
            from django.contrib import messages
            messages.error(request, "Payment processing is temporarily unavailable.")
            return redirect("pricing")


class MyPackagesView(TenantMixin, ListView):
    """List student's purchased packages."""
    model = PackagePurchase
    template_name = "payments/my_packages.html"
    context_object_name = "purchases"

    def get_queryset(self):
        return PackagePurchase.objects.filter(
            student=self.request.user, academy=self.get_academy(),
        )


class AcademyTierView(View):
    """FEAT-029: Display platform tiers for academy signup."""

    def get(self, request):
        tiers = AcademyTier.objects.filter(is_active=True)
        return render(request, "payments/tiers.html", {"tiers": tiers})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    """Handle Stripe webhook events."""

    def post(self, request):
        from .stripe_service import construct_webhook_event, handle_checkout_completed

        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = construct_webhook_event(payload, sig_header)
        except ValueError:
            logger.warning("Invalid Stripe webhook payload")
            return HttpResponse(status=400)
        except Exception as e:
            logger.warning("Stripe webhook signature verification failed: %s", e)
            return HttpResponse(status=400)

        event_type = event["type"]
        logger.info("Stripe webhook received: %s", event_type)

        try:
            if event_type == "checkout.session.completed":
                session = event["data"]["object"]
                handle_checkout_completed(session)

            elif event_type == "customer.subscription.updated":
                from .stripe_service import handle_subscription_updated
                stripe_sub = event["data"]["object"]
                handle_subscription_updated(stripe_sub)

            elif event_type == "customer.subscription.deleted":
                from .stripe_service import handle_subscription_deleted
                stripe_sub = event["data"]["object"]
                handle_subscription_deleted(stripe_sub)

        except Exception:
            logger.exception("Error handling Stripe webhook event %s", event_type)
            # Return 200 to prevent Stripe retries on our processing errors
            # The issue is logged and can be investigated

        return HttpResponse(status=200)
