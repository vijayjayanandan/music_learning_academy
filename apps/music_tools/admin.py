from django.contrib import admin
from .models import (
    EarTrainingExercise,
    EarTrainingScore,
    RecitalEvent,
    RecitalPerformer,
    PracticeAnalysis,
    RecordingArchive,
)


class EarTrainingScoreInline(admin.TabularInline):
    model = EarTrainingScore
    extra = 0
    fields = ["student", "score", "total_questions", "time_taken_seconds", "created_at"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["student"]


class RecitalPerformerInline(admin.TabularInline):
    model = RecitalPerformer
    extra = 0
    fields = ["student", "piece_title", "composer", "performance_order"]
    autocomplete_fields = ["student"]


@admin.register(EarTrainingExercise)
class EarTrainingExerciseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "academy",
        "exercise_type",
        "difficulty",
        "is_active",
        "created_at",
    ]
    list_filter = ["exercise_type", "difficulty", "is_active", "academy"]
    search_fields = ["title", "academy__name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["academy"]
    list_select_related = ["academy"]
    inlines = [EarTrainingScoreInline]


@admin.register(EarTrainingScore)
class EarTrainingScoreAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "exercise",
        "academy",
        "score",
        "total_questions",
        "percentage_display",
        "time_taken_seconds",
        "created_at",
    ]
    list_filter = ["academy", "exercise__exercise_type"]
    search_fields = ["student__email", "exercise__title"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["student", "exercise", "academy"]
    list_select_related = ["student", "exercise", "academy"]

    @admin.display(description="Score %")
    def percentage_display(self, obj):
        return f"{obj.percentage}%"


@admin.register(RecitalEvent)
class RecitalEventAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "academy",
        "status",
        "scheduled_start",
        "scheduled_end",
        "is_public",
        "created_at",
    ]
    list_filter = ["status", "is_public", "academy"]
    search_fields = ["title", "description", "academy__name"]
    readonly_fields = ["room_name", "created_at", "updated_at"]
    autocomplete_fields = ["academy"]
    list_select_related = ["academy"]
    inlines = [RecitalPerformerInline]
    date_hierarchy = "scheduled_start"

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "description", "academy"),
            },
        ),
        (
            "Schedule",
            {
                "fields": ("scheduled_start", "scheduled_end", "status"),
            },
        ),
        (
            "Video",
            {
                "fields": ("room_name", "recording_url", "is_public"),
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


@admin.register(RecitalPerformer)
class RecitalPerformerAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "recital",
        "academy",
        "piece_title",
        "composer",
        "performance_order",
    ]
    list_filter = ["academy"]
    search_fields = [
        "student__email",
        "piece_title",
        "composer",
        "recital__title",
    ]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["recital", "student", "academy"]
    list_select_related = ["recital", "student", "academy"]


@admin.register(PracticeAnalysis)
class PracticeAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "academy",
        "has_recording",
        "analyzed_at",
        "created_at",
    ]
    list_filter = ["academy"]
    search_fields = ["student__email", "feedback"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["student", "academy"]
    list_select_related = ["student", "academy"]

    @admin.display(description="Has Recording", boolean=True)
    def has_recording(self, obj):
        return bool(obj.recording or obj.recording_url)


@admin.register(RecordingArchive)
class RecordingArchiveAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "student",
        "academy",
        "instrument",
        "duration_display",
        "course",
        "created_at",
    ]
    list_filter = ["instrument", "academy"]
    search_fields = ["title", "student__email", "instrument", "notes"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["student", "academy", "course"]
    list_select_related = ["student", "academy", "course"]

    @admin.display(description="Duration")
    def duration_display(self, obj):
        if obj.duration_seconds == 0:
            return "-"
        minutes, seconds = divmod(obj.duration_seconds, 60)
        return f"{minutes}m {seconds}s"
