from django.contrib import admin
from .models import Enrollment, LessonProgress, AssignmentSubmission


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "status", "enrolled_at"]
    list_filter = ["status"]
    search_fields = ["student__email", "course__title"]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ["enrollment", "lesson", "is_completed", "practice_time_minutes"]
    list_filter = ["is_completed"]


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ["assignment", "student", "status", "created_at"]
    list_filter = ["status"]
