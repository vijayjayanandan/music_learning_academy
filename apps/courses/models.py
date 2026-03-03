from django.db import models
from apps.common.models import TenantScopedModel


class Course(TenantScopedModel):
    class DifficultyLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        ELEMENTARY = "elementary", "Elementary"
        INTERMEDIATE = "intermediate", "Intermediate"
        UPPER_INTERMEDIATE = "upper_intermediate", "Upper Intermediate"
        ADVANCED = "advanced", "Advanced"

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300)
    description = models.TextField()
    instructor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="taught_courses",
    )

    instrument = models.CharField(max_length=50, help_text="e.g. Piano, Guitar, Vocals")
    genre = models.CharField(max_length=50, blank=True, help_text="e.g. Classical, Jazz")
    difficulty_level = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER,
    )

    prerequisites = models.TextField(blank=True)
    learning_outcomes = models.JSONField(default=list)
    estimated_duration_weeks = models.PositiveIntegerField(default=8)

    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    max_students = models.PositiveIntegerField(default=30)

    class Meta:
        unique_together = ("academy", "slug")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status="active").count()

    @property
    def lesson_count(self):
        return self.lessons.count()


class Lesson(TenantScopedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    content = models.TextField(blank=True, help_text="Lesson content in Markdown")
    video_url = models.URLField(blank=True, help_text="Link to pre-recorded video")

    sheet_music_url = models.URLField(blank=True)
    audio_example_url = models.URLField(blank=True)

    topics = models.JSONField(
        default=list,
        help_text='e.g. ["Major Scales","Sight Reading"]',
    )

    estimated_duration_minutes = models.PositiveIntegerField(default=30)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["course", "order"]

    def __str__(self):
        return f"{self.course.title} - Lesson {self.order}: {self.title}"


class PracticeAssignment(TenantScopedModel):
    class AssignmentType(models.TextChoices):
        PRACTICE = "practice", "Practice Piece"
        THEORY = "theory", "Music Theory Exercise"
        EAR_TRAINING = "ear_training", "Ear Training"
        COMPOSITION = "composition", "Composition / Arrangement"
        PERFORMANCE = "performance", "Performance Recording"
        TECHNIQUE = "technique", "Technique Drill"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=300)
    description = models.TextField()
    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentType.choices,
        default=AssignmentType.PRACTICE,
    )

    piece_title = models.CharField(max_length=200, blank=True)
    composer = models.CharField(max_length=200, blank=True)
    tempo_bpm = models.PositiveIntegerField(null=True, blank=True)
    practice_minutes_target = models.PositiveIntegerField(default=30)

    reference_audio_url = models.URLField(blank=True)
    sheet_music_url = models.URLField(blank=True)
    instructions = models.TextField(blank=True)

    due_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["lesson", "created_at"]
