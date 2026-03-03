from django.contrib import admin
from .models import Course, Lesson, PracticeAssignment, LessonAttachment


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ["title", "order", "estimated_duration_minutes", "is_published"]
    show_change_link = True


class PracticeAssignmentInline(admin.TabularInline):
    model = PracticeAssignment
    extra = 0
    fields = ["title", "assignment_type", "practice_minutes_target", "due_date"]
    show_change_link = True


class LessonAttachmentInline(admin.TabularInline):
    model = LessonAttachment
    extra = 0
    fields = ["title", "file", "file_type", "order"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title", "academy", "instructor", "instrument", "genre",
        "difficulty_level", "is_published", "price_display_column", "created_at",
    ]
    list_filter = [
        "is_published", "difficulty_level", "instrument", "genre",
        "currency", "academy",
    ]
    search_fields = ["title", "description", "instructor__email", "instrument", "genre"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "published_at"]
    autocomplete_fields = ["academy", "instructor"]
    list_select_related = ["academy", "instructor"]
    filter_horizontal = ["prerequisite_courses"]
    inlines = [LessonInline]

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "description", "thumbnail"),
        }),
        ("Assignment", {
            "fields": ("academy", "instructor"),
        }),
        ("Music Details", {
            "fields": ("instrument", "genre", "difficulty_level"),
        }),
        ("Course Structure", {
            "fields": (
                "prerequisites", "learning_outcomes",
                "estimated_duration_weeks", "max_students",
                "prerequisite_courses",
            ),
        }),
        ("Pricing", {
            "fields": ("price_cents", "currency"),
        }),
        ("Publishing", {
            "fields": ("is_published", "published_at"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Price")
    def price_display_column(self, obj):
        return obj.price_display


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "title", "course", "order", "estimated_duration_minutes",
        "is_published", "academy",
    ]
    list_filter = ["is_published", "academy", "course"]
    search_fields = ["title", "description", "course__title"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["academy", "course"]
    list_select_related = ["course", "academy"]
    inlines = [PracticeAssignmentInline, LessonAttachmentInline]

    fieldsets = (
        (None, {
            "fields": ("course", "academy", "title", "description", "order"),
        }),
        ("Content", {
            "fields": ("content", "video_url", "sheet_music_url", "audio_example_url"),
        }),
        ("Metadata", {
            "fields": ("topics", "estimated_duration_minutes", "is_published"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(PracticeAssignment)
class PracticeAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "title", "lesson", "assignment_type", "piece_title",
        "practice_minutes_target", "due_date", "academy",
    ]
    list_filter = ["assignment_type", "academy"]
    search_fields = ["title", "description", "piece_title", "composer", "lesson__title"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["academy", "lesson"]
    list_select_related = ["lesson", "academy"]

    fieldsets = (
        (None, {
            "fields": ("lesson", "academy", "title", "description", "assignment_type"),
        }),
        ("Music Details", {
            "fields": (
                "piece_title", "composer", "tempo_bpm",
                "practice_minutes_target", "due_date",
            ),
        }),
        ("Resources", {
            "fields": ("reference_audio_url", "sheet_music_url", "instructions"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(LessonAttachment)
class LessonAttachmentAdmin(admin.ModelAdmin):
    list_display = ["title", "lesson", "file_type", "order", "academy", "created_at"]
    list_filter = ["file_type", "academy"]
    search_fields = ["title", "description", "lesson__title"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["academy", "lesson"]
    list_select_related = ["lesson", "academy"]
