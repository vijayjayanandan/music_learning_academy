from django.contrib import admin
from .models import (
    LiveSession, SessionAttendance, InstructorAvailability, SessionNote,
)


class SessionAttendanceInline(admin.TabularInline):
    model = SessionAttendance
    extra = 0
    fields = ["student", "status", "joined_at", "left_at"]
    readonly_fields = ["joined_at", "left_at"]
    autocomplete_fields = ["student"]


class SessionNoteInline(admin.StackedInline):
    model = SessionNote
    extra = 0
    fields = ["instructor", "student", "content"]
    autocomplete_fields = ["instructor", "student"]


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = [
        "title", "academy", "instructor", "session_type",
        "video_platform", "scheduled_start", "duration_minutes", "status",
    ]
    list_filter = [
        "status", "session_type", "video_platform",
        "is_recurring", "academy",
    ]
    search_fields = ["title", "description", "instructor__email", "instrument_focus"]
    readonly_fields = [
        "room_name", "created_at", "updated_at",
        "reminder_24h_sent", "reminder_1h_sent",
    ]
    autocomplete_fields = ["academy", "instructor", "course", "recurrence_parent"]
    list_select_related = ["academy", "instructor", "course"]
    inlines = [SessionAttendanceInline, SessionNoteInline]
    date_hierarchy = "scheduled_start"

    fieldsets = (
        (None, {
            "fields": ("title", "description", "academy", "course"),
        }),
        ("Schedule", {
            "fields": (
                "instructor", "scheduled_start", "scheduled_end",
                "duration_minutes", "session_type", "max_participants",
            ),
        }),
        ("Video", {
            "fields": (
                "video_platform", "room_name",
                "external_meeting_url", "recording_url",
            ),
        }),
        ("Recurrence", {
            "fields": ("is_recurring", "recurrence_rule", "recurrence_parent"),
            "classes": ("collapse",),
        }),
        ("Session Details", {
            "fields": (
                "status", "session_notes", "instrument_focus", "topics_covered",
            ),
        }),
        ("Reminders", {
            "fields": ("reminder_24h_sent", "reminder_1h_sent"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        "session", "student", "academy", "status", "joined_at", "left_at",
    ]
    list_filter = ["status", "academy"]
    search_fields = ["student__email", "session__title"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["session", "student", "academy"]
    list_select_related = ["session", "student", "academy"]


@admin.register(InstructorAvailability)
class InstructorAvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        "instructor", "academy", "day_of_week",
        "start_time", "end_time", "is_active",
    ]
    list_filter = ["day_of_week", "is_active", "academy"]
    search_fields = ["instructor__email", "instructor__first_name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["instructor", "academy"]
    list_select_related = ["instructor", "academy"]


@admin.register(SessionNote)
class SessionNoteAdmin(admin.ModelAdmin):
    list_display = ["session", "instructor", "student", "academy", "created_at"]
    list_filter = ["academy"]
    search_fields = [
        "content", "instructor__email", "student__email", "session__title",
    ]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["session", "instructor", "student", "academy"]
    list_select_related = ["session", "instructor", "student", "academy"]
