from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from .models import (
    SubscriptionPlan, Subscription, Payment, Coupon,
    InstructorPayout, PackageDeal, PackagePurchase, AcademyTier,
)


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
        })


class CheckoutView(TenantMixin, View):
    """FEAT-023: Checkout for a course or plan (stubbed Stripe)."""

    def get(self, request, plan_id=None, course_slug=None):
        context = {}
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
        academy = self.get_academy()
        if plan_id:
            plan = get_object_or_404(SubscriptionPlan, pk=plan_id, academy=academy)
            sub = Subscription.objects.create(
                student=request.user, plan=plan, academy=academy,
                status=Subscription.Status.TRIALING if plan.trial_days > 0 else Subscription.Status.ACTIVE,
                current_period_start=timezone.now(),
            )
            if plan.trial_days > 0:
                sub.trial_end = timezone.now() + timezone.timedelta(days=plan.trial_days)
                sub.save()
            Payment.objects.create(
                student=request.user, academy=academy,
                amount_cents=plan.price_cents, payment_type=Payment.PaymentType.SUBSCRIPTION,
                subscription=sub, status=Payment.Status.COMPLETED,
                paid_at=timezone.now(),
            )
            return redirect("subscription-detail", pk=sub.pk)
        elif course_slug:
            from apps.courses.models import Course
            from apps.enrollments.models import Enrollment
            course = get_object_or_404(Course, slug=course_slug, academy=academy)
            Payment.objects.create(
                student=request.user, academy=academy,
                amount_cents=0, payment_type=Payment.PaymentType.COURSE,
                course=course, status=Payment.Status.COMPLETED,
                paid_at=timezone.now(),
            )
            Enrollment.objects.get_or_create(
                student=request.user, course=course, academy=academy,
            )
            return redirect("course-detail", slug=course_slug)
        return redirect("pricing")


class SubscriptionDetailView(TenantMixin, View):
    """View subscription details."""

    def get(self, request, pk):
        sub = get_object_or_404(
            Subscription, pk=pk, student=request.user,
        )
        return render(request, "payments/subscription_detail.html", {"subscription": sub})


class CancelSubscriptionView(TenantMixin, View):
    """Cancel a subscription."""

    def post(self, request, pk):
        sub = get_object_or_404(
            Subscription, pk=pk, student=request.user,
        )
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

    def get(self, request):
        coupons = Coupon.objects.filter(academy=self.get_academy())
        return render(request, "payments/coupons.html", {"coupons": coupons})

    def post(self, request):
        Coupon.objects.create(
            academy=self.get_academy(),
            code=request.POST.get("code", "").upper(),
            discount_type=request.POST.get("discount_type", "percentage"),
            discount_value=int(request.POST.get("discount_value", 10)),
            max_uses=int(request.POST.get("max_uses", 0)),
        )
        return redirect("coupon-manage")


class InstructorPayoutListView(TenantMixin, ListView):
    """FEAT-028: Instructor payout list."""
    model = InstructorPayout
    template_name = "payments/payouts.html"
    context_object_name = "payouts"

    def get_queryset(self):
        user = self.request.user
        role = user.get_role_in(self.get_academy())
        if role in ("owner",):
            return InstructorPayout.objects.filter(academy=self.get_academy())
        return InstructorPayout.objects.filter(
            instructor=user, academy=self.get_academy(),
        )


class PackagePurchaseView(TenantMixin, View):
    """FEAT-031: Purchase a package deal."""

    def post(self, request, pk):
        package = get_object_or_404(
            PackageDeal, pk=pk, academy=self.get_academy(), is_active=True,
        )
        payment = Payment.objects.create(
            student=request.user, academy=self.get_academy(),
            amount_cents=package.price_cents, payment_type=Payment.PaymentType.PACKAGE,
            status=Payment.Status.COMPLETED, paid_at=timezone.now(),
        )
        PackagePurchase.objects.create(
            student=request.user, academy=self.get_academy(),
            package=package, credits_remaining=package.total_credits,
            payment=payment,
        )
        return redirect("my-packages")


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
