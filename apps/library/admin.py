from django.contrib import admin
from .models import LibraryResource


@admin.register(LibraryResource)
class LibraryResourceAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "academy",
        "resource_type",
        "uploaded_by",
        "instrument",
        "genre",
        "difficulty_level",
        "download_count",
        "created_at",
    ]
    list_filter = [
        "resource_type",
        "difficulty_level",
        "instrument",
        "genre",
        "academy",
    ]
    search_fields = [
        "title",
        "description",
        "uploaded_by__email",
        "instrument",
        "genre",
    ]
    readonly_fields = ["download_count", "created_at", "updated_at"]
    autocomplete_fields = ["uploaded_by", "academy"]
    list_select_related = ["uploaded_by", "academy"]

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "description", "academy", "uploaded_by"),
            },
        ),
        (
            "File",
            {
                "fields": ("file", "resource_type"),
            },
        ),
        (
            "Categorization",
            {
                "fields": ("instrument", "genre", "difficulty_level", "tags"),
            },
        ),
        (
            "Statistics",
            {
                "fields": ("download_count",),
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
