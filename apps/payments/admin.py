from django.contrib import admin
from .models import (
    SubscriptionPlan,
    Subscription,
    Payment,
    Coupon,
    InstructorPayout,
    PackageDeal,
    PackagePurchase,
    AcademyTier,
)


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ["student", "status", "current_period_start", "current_period_end"]
    readonly_fields = ["current_period_start", "current_period_end"]
    autocomplete_fields = ["student"]
    show_change_link = True


class PaymentInline(admin.TabularInline):
    model = Payment
    fk_name = "subscription"
    extra = 0
    fields = ["invoice_number", "amount_cents", "status", "paid_at"]
    readonly_fields = ["invoice_number", "paid_at"]
    show_change_link = True


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "academy",
        "price_display_column",
        "currency",
        "billing_cycle",
        "trial_days",
        "is_active",
        "created_at",
    ]
    list_filter = ["billing_cycle", "is_active", "currency", "academy"]
    search_fields = ["name", "description", "academy__name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["academy"]
    list_select_related = ["academy"]
    inlines = [SubscriptionInline]

    @admin.display(description="Price")
    def price_display_column(self, obj):
        return obj.price_display


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "plan",
        "academy",
        "status",
        "current_period_start",
        "current_period_end",
        "trial_end",
        "created_at",
    ]
    list_filter = ["status", "academy"]
    search_fields = [
        "student__email",
        "plan__name",
        "stripe_subscription_id",
        "academy__name",
    ]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["student", "plan", "academy"]
    list_select_related = ["student", "plan", "academy"]
    inlines = [PaymentInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("student", "plan", "academy", "status"),
            },
        ),
        (
            "Billing Period",
            {
                "fields": (
                    "current_period_start",
                    "current_period_end",
                    "trial_end",
                    "cancelled_at",
                ),
            },
        ),
        (
            "Stripe Integration",
            {
                "fields": ("stripe_subscription_id",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "student",
        "academy",
        "amount_display_column",
        "payment_type",
        "status",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "payment_type", "currency", "academy"]
    search_fields = [
        "invoice_number",
        "student__email",
        "description",
        "stripe_payment_intent_id",
        "stripe_checkout_session_id",
    ]
    readonly_fields = ["invoice_number", "created_at", "updated_at"]
    autocomplete_fields = ["student", "course", "subscription", "academy"]
    list_select_related = ["student", "course", "subscription", "academy"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "student",
                    "academy",
                    "invoice_number",
                    "amount_cents",
                    "currency",
                    "payment_type",
                    "status",
                ),
            },
        ),
        (
            "Related Objects",
            {
                "fields": ("course", "subscription", "description"),
            },
        ),
        (
            "Payment Details",
            {
                "fields": ("paid_at",),
            },
        ),
        (
            "Stripe Integration",
            {
                "fields": ("stripe_payment_intent_id", "stripe_checkout_session_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Amount")
    def amount_display_column(self, obj):
        return obj.amount_display


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "academy",
        "discount_type",
        "discount_value",
        "times_used",
        "max_uses",
        "is_active",
        "expires_at",
    ]
    list_filter = ["discount_type", "is_active", "academy"]
    search_fields = ["code", "academy__name"]
    readonly_fields = ["times_used", "created_at", "updated_at"]
    autocomplete_fields = ["academy"]
    list_select_related = ["academy"]
    filter_horizontal = ["applicable_courses"]


@admin.register(InstructorPayout)
class InstructorPayoutAdmin(admin.ModelAdmin):
    list_display = [
        "instructor",
        "academy",
        "amount_display_column",
        "status",
        "period_start",
        "period_end",
        "paid_at",
    ]
    list_filter = ["status", "academy"]
    search_fields = ["instructor__email", "notes", "stripe_transfer_id"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["instructor", "academy"]
    list_select_related = ["instructor", "academy"]

    @admin.display(description="Amount")
    def amount_display_column(self, obj):
        return f"${obj.amount_cents / 100:.2f}"


@admin.register(PackageDeal)
class PackageDealAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "academy",
        "price_display_column",
        "total_credits",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "academy"]
    search_fields = ["name", "description", "academy__name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["academy"]
    list_select_related = ["academy"]
    filter_horizontal = ["courses"]

    @admin.display(description="Price")
    def price_display_column(self, obj):
        return f"${obj.price_cents / 100:.2f}"


@admin.register(PackagePurchase)
class PackagePurchaseAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "package",
        "academy",
        "credits_remaining",
        "payment",
        "created_at",
    ]
    list_filter = ["academy"]
    search_fields = ["student__email", "package__name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["student", "package", "payment", "academy"]
    list_select_related = ["student", "package", "payment", "academy"]


@admin.register(AcademyTier)
class AcademyTierAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "tier_level",
        "price_display_column",
        "max_students",
        "max_instructors",
        "max_courses",
        "is_active",
    ]
    list_filter = ["tier_level", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Price/mo")
    def price_display_column(self, obj):
        return f"${obj.price_cents / 100:.2f}"
