from django.contrib import admin
from .models import Academy, Announcement


@admin.register(Academy)
class AcademyAdmin(admin.ModelAdmin):
    list_display = [
        "name", "slug", "email", "timezone", "is_active",
        "max_students", "max_instructors", "created_at",
    ]
    list_filter = ["is_active", "timezone"]
    search_fields = ["name", "slug", "email", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("name", "slug", "description", "logo"),
        }),
        ("Contact Information", {
            "fields": ("website", "email", "phone", "address", "timezone"),
        }),
        ("Limits", {
            "fields": ("is_active", "max_students", "max_instructors"),
        }),
        ("Music Details", {
            "fields": ("primary_instruments", "genres"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "academy", "author", "is_pinned", "created_at"]
    list_filter = ["is_pinned", "academy"]
    search_fields = ["title", "body", "author__email", "academy__name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["academy", "author"]
    list_select_related = ["academy", "author"]
