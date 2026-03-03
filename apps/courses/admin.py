from django.contrib import admin
from .models import Course, Lesson, PracticeAssignment


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ["title", "order", "estimated_duration_minutes", "is_published"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "academy", "instructor", "instrument", "difficulty_level", "is_published"]
    list_filter = ["is_published", "difficulty_level", "instrument"]
    search_fields = ["title", "description"]
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order", "is_published"]
    list_filter = ["is_published"]


@admin.register(PracticeAssignment)
class PracticeAssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "lesson", "assignment_type", "due_date"]
    list_filter = ["assignment_type"]
