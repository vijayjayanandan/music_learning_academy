import uuid
from django.db import models
from apps.common.models import TenantScopedModel, TimeStampedModel


class SubscriptionPlan(TenantScopedModel):
    """FEAT-024: Subscription plans for an academy."""

    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        ANNUAL = "annual", "Annual"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField(help_text="Price in cents")
    currency = models.CharField(max_length=3, default="USD")
    billing_cycle = models.CharField(
        max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY,
    )
    is_active = models.BooleanField(default=True)
    trial_days = models.PositiveIntegerField(default=0, help_text="Free trial period in days")
    stripe_price_id = models.CharField(max_length=100, blank=True)
    features = models.JSONField(default=list, help_text='e.g. ["All courses", "Live sessions"]')

    class Meta:
        ordering = ["price_cents"]

    def __str__(self):
        return f"{self.name} - ${self.price_cents / 100:.2f}/{self.billing_cycle}"

    @property
    def price_display(self):
        return f"${self.price_cents / 100:.2f}"


class Subscription(TenantScopedModel):
    """Active subscription linking student to a plan."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        TRIALING = "trialing", "Trialing"
        PAST_DUE = "past_due", "Past Due"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="subscriptions",
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, db_index=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["academy", "student", "status"]),
        ]

    def __str__(self):
        return f"{self.student.email} - {self.plan.name} ({self.status})"

    @property
    def is_valid(self):
        return self.status in (self.Status.ACTIVE, self.Status.TRIALING)


class Payment(TenantScopedModel):
    """FEAT-023: Individual payment records."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class PaymentType(models.TextChoices):
        COURSE = "course", "Course Purchase"
        SUBSCRIPTION = "subscription", "Subscription"
        PACKAGE = "package", "Package Deal"

    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="payments",
    )
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_checkout_session_id = models.CharField(max_length=100, blank=True, db_index=True)

    course = models.ForeignKey(
        "courses.Course", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments",
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments",
    )
    description = models.TextField(blank=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["academy", "student", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.invoice_number} - ${self.amount_cents / 100:.2f}"

    @property
    def amount_display(self):
        return f"${self.amount_cents / 100:.2f}"


class Coupon(TenantScopedModel):
    """FEAT-026: Coupon codes and discounts."""

    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED_AMOUNT = "fixed_amount", "Fixed Amount"

    code = models.CharField(max_length=50, db_index=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.PositiveIntegerField(
        help_text="Percentage (1-100) or amount in cents",
    )
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    times_used = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    applicable_courses = models.ManyToManyField(
        "courses.Course", blank=True, related_name="coupons",
    )

    class Meta:
        unique_together = ("academy", "code")
        ordering = ["-created_at"]

    def __str__(self):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return f"{self.code} ({self.discount_value}% off)"
        return f"{self.code} (${self.discount_value / 100:.2f} off)"

    @property
    def is_valid(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class InstructorPayout(TenantScopedModel):
    """FEAT-028: Instructor payout management."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    instructor = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="payouts",
    )
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    period_start = models.DateField()
    period_end = models.DateField()
    stripe_transfer_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payout to {self.instructor.email} - ${self.amount_cents / 100:.2f}"


class PackageDeal(TenantScopedModel):
    """FEAT-031: Package deals (bundled sessions/courses)."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    total_credits = models.PositiveIntegerField(help_text="Total number of sessions/lessons")
    is_active = models.BooleanField(default=True)
    courses = models.ManyToManyField("courses.Course", blank=True, related_name="packages")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.total_credits} credits (${self.price_cents / 100:.2f})"


class PackagePurchase(TenantScopedModel):
    """Tracks a student's purchased package and remaining credits."""

    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="package_purchases",
    )
    package = models.ForeignKey(
        PackageDeal, on_delete=models.PROTECT, related_name="purchases",
    )
    credits_remaining = models.PositiveIntegerField()
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.email} - {self.package.name} ({self.credits_remaining} left)"


class AcademyTier(TimeStampedModel):
    """FEAT-029: Platform-level academy subscription tiers."""

    class TierLevel(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"
        ENTERPRISE = "enterprise", "Enterprise"

    name = models.CharField(max_length=100)
    tier_level = models.CharField(max_length=20, choices=TierLevel.choices, unique=True)
    price_cents = models.PositiveIntegerField(default=0)
    max_students = models.PositiveIntegerField(default=10)
    max_instructors = models.PositiveIntegerField(default=2)
    max_courses = models.PositiveIntegerField(default=5)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price_cents"]

    def __str__(self):
        return f"{self.name} (${self.price_cents / 100:.2f}/mo)"
