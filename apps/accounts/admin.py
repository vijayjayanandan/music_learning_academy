from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Membership, Invitation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "first_name", "last_name", "current_academy", "is_staff"]
    list_filter = ["is_staff", "is_active"]
    search_fields = ["email", "username", "first_name", "last_name"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "academy", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__email", "academy__name"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "academy", "role", "accepted", "created_at"]
    list_filter = ["accepted", "role"]
