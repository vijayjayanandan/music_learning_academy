from django.contrib import admin
from .models import Enrollment, LessonProgress, AssignmentSubmission


class LessonProgressInline(admin.TabularInline):
    model = LessonProgress
    extra = 0
    fields = ["lesson", "is_completed", "completed_at", "practice_time_minutes"]
    readonly_fields = ["completed_at"]
    autocomplete_fields = ["lesson"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "student", "course", "academy", "status",
        "progress_display", "enrolled_at", "completed_at",
    ]
    list_filter = ["status", "academy", "course"]
    search_fields = ["student__email", "student__first_name", "course__title"]
    readonly_fields = ["enrolled_at", "created_at", "updated_at"]
    autocomplete_fields = ["student", "course", "academy"]
    list_select_related = ["student", "course", "academy"]
    inlines = [LessonProgressInline]
    date_hierarchy = "enrolled_at"

    @admin.display(description="Progress")
    def progress_display(self, obj):
        return f"{obj.progress_percent}%"


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        "enrollment", "lesson", "is_completed",
        "practice_time_minutes", "completed_at", "academy",
    ]
    list_filter = ["is_completed", "academy"]
    search_fields = [
        "enrollment__student__email", "lesson__title",
        "enrollment__course__title",
    ]
    readonly_fields = ["completed_at", "created_at", "updated_at"]
    autocomplete_fields = ["enrollment", "lesson", "academy"]
    list_select_related = ["enrollment", "enrollment__student", "lesson", "academy"]


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "assignment", "student", "academy", "status",
        "grade", "practice_time_minutes", "reviewed_by", "created_at",
    ]
    list_filter = ["status", "academy"]
    search_fields = [
        "student__email", "assignment__title",
        "instructor_feedback", "grade",
    ]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
    autocomplete_fields = ["assignment", "student", "reviewed_by", "academy"]
    list_select_related = ["assignment", "student", "reviewed_by", "academy"]

    fieldsets = (
        (None, {
            "fields": ("assignment", "student", "academy"),
        }),
        ("Submission", {
            "fields": (
                "text_response", "recording_url", "recording",
                "file_upload", "practice_time_minutes",
            ),
        }),
        ("Review", {
            "fields": (
                "status", "instructor_feedback", "grade",
                "rubric_scores", "reviewed_by", "reviewed_at",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
