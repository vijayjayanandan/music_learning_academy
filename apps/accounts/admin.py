from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Membership, Invitation


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = [
        "academy",
        "role",
        "skill_level",
        "learning_goal",
        "onboarding_skipped",
        "is_active",
        "joined_at",
    ]
    readonly_fields = ["joined_at"]
    autocomplete_fields = ["academy"]


class InvitationInline(admin.TabularInline):
    model = Invitation
    fk_name = "invited_by"
    extra = 0
    fields = ["academy", "email", "role", "accepted", "created_at", "expires_at"]
    readonly_fields = ["created_at"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "username",
        "first_name",
        "last_name",
        "current_academy",
        "email_verified",
        "is_staff",
        "is_active",
    ]
    list_filter = [
        "is_staff",
        "is_active",
        "is_superuser",
        "email_verified",
        "is_parent",
        "current_academy",
    ]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["email"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Music Academy",
            {
                "fields": (
                    "avatar",
                    "email_verified",
                    "timezone",
                    "email_preferences",
                    "is_parent",
                    "parent",
                    "current_academy",
                    "stripe_customer_id",
                    "google_calendar_token",
                    "ical_feed_token",
                ),
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Music Academy",
            {
                "fields": ("email", "current_academy"),
            },
        ),
    )

    readonly_fields = ["google_calendar_token", "ical_feed_token"]
    autocomplete_fields = ["current_academy", "parent"]
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "academy",
        "role",
        "skill_level",
        "is_active",
        "joined_at",
    ]
    list_filter = ["role", "is_active", "skill_level", "academy"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "academy__name",
    ]
    readonly_fields = ["joined_at"]
    autocomplete_fields = ["user", "academy"]
    list_select_related = ["user", "academy"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "academy",
        "role",
        "invited_by",
        "accepted",
        "created_at",
        "expires_at",
    ]
    list_filter = ["accepted", "role", "academy"]
    search_fields = ["email", "academy__name", "invited_by__email"]
    readonly_fields = ["token", "created_at"]
    autocomplete_fields = ["academy", "invited_by"]
    list_select_related = ["academy", "invited_by"]
