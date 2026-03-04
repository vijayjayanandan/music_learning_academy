from django.contrib import admin
from .models import PracticeLog, PracticeGoal


@admin.register(PracticeLog)
class PracticeLogAdmin(admin.ModelAdmin):
    list_display = [
        "student", "academy", "date", "instrument",
        "duration_minutes", "course", "created_at",
    ]
    list_filter = ["instrument", "academy", "date"]
    search_fields = [
        "student__email", "student__first_name",
        "instrument", "pieces_worked_on", "notes",
    ]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["student", "academy", "course"]
    list_select_related = ["student", "academy", "course"]
    date_hierarchy = "date"


@admin.register(PracticeGoal)
class PracticeGoalAdmin(admin.ModelAdmin):
    list_display = [
        "student", "academy", "weekly_minutes_target",
        "is_active", "created_at",
    ]
    list_filter = ["is_active", "academy"]
    search_fields = ["student__email", "student__first_name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["student", "academy"]
    list_select_related = ["student", "academy"]
