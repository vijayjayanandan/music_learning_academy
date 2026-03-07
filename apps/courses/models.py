from django.db import models
from apps.common.models import TenantScopedModel
from apps.common.storage import (
    get_public_storage,
    get_private_storage,
    upload_to_course_thumbnails,
    upload_to_lesson_attachments,
)


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

    thumbnail = models.ImageField(
        upload_to=upload_to_course_thumbnails, storage=get_public_storage, blank=True, null=True
    )

    price_cents = models.PositiveIntegerField(
        default=0, help_text="Price in cents. 0 = free course."
    )
    currency = models.CharField(max_length=3, default="USD")

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    max_students = models.PositiveIntegerField(default=30)
    is_template = models.BooleanField(
        default=False,
        help_text="Template courses can be cloned by any academy as a starting point.",
    )
    source_template = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cloned_courses",
        help_text="The template course this was cloned from, if any.",
    )
    prerequisite_courses = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="dependent_courses"
    )

    class Meta:
        unique_together = ("academy", "slug")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["academy", "is_published"]),
            models.Index(fields=["instructor", "academy"]),
        ]

    def __str__(self):
        return self.title

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status="active").count()

    @property
    def lesson_count(self):
        return self.lessons.count()

    @property
    def is_free(self):
        return self.price_cents == 0

    @property
    def price_display(self):
        if self.is_free:
            return "Free"
        return f"${self.price_cents / 100:.2f}"


class Lesson(TenantScopedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    content = models.TextField(blank=True, help_text="Lesson content in HTML (edited via TinyMCE rich text editor)")
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
        indexes = [
            models.Index(fields=["course", "order"]),
        ]

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


class LessonAttachment(TenantScopedModel):
    class FileType(models.TextChoices):
        SHEET_MUSIC = "sheet_music", "Sheet Music"
        AUDIO = "audio", "Audio"
        VIDEO = "video", "Video"
        IMAGE = "image", "Image"
        OTHER = "other", "Other"

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=upload_to_lesson_attachments, storage=get_private_storage)
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.lesson.title})"

    @property
    def file_size_display(self):
        """Return human-readable file size."""
        try:
            size = self.file.size
        except (FileNotFoundError, ValueError):
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def file_extension(self):
        import os
        return os.path.splitext(self.file.name)[1].lower()
