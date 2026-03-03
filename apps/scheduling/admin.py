from django.contrib import admin
from .models import LiveSession, SessionAttendance


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ["title", "academy", "instructor", "session_type", "scheduled_start", "status"]
    list_filter = ["status", "session_type"]
    search_fields = ["title"]


@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = ["session", "student", "status", "joined_at"]
    list_filter = ["status"]
