from django.db import models
from apps.common.models import TenantScopedModel
from apps.common.storage import (
    get_private_storage,
    upload_to_analysis,
    upload_to_student_recordings,
)


class EarTrainingExercise(TenantScopedModel):
    """FEAT-036: Ear training exercises."""

    class ExerciseType(models.TextChoices):
        INTERVAL = "interval", "Interval Recognition"
        CHORD = "chord", "Chord Identification"
        RHYTHM = "rhythm", "Rhythm Dictation"
        MELODY = "melody", "Melody Dictation"
        SCALE = "scale", "Scale Identification"

    title = models.CharField(max_length=200)
    exercise_type = models.CharField(max_length=20, choices=ExerciseType.choices)
    difficulty = models.PositiveIntegerField(default=1, help_text="1-5")
    questions = models.JSONField(
        default=list,
        help_text="List of question objects with answer/options",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["exercise_type", "difficulty"]

    def __str__(self):
        return f"{self.title} ({self.get_exercise_type_display()})"


class EarTrainingScore(TenantScopedModel):
    """Track student's ear training performance."""

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="ear_training_scores",
    )
    exercise = models.ForeignKey(
        EarTrainingExercise,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    time_taken_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return int((self.score / self.total_questions) * 100)


class RecitalEvent(TenantScopedModel):
    """FEAT-037: Virtual recital events."""

    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPCOMING
    )
    room_name = models.CharField(max_length=255, unique=True)
    recording_url = models.URLField(blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ["-scheduled_start"]

    def __str__(self):
        return self.title


class RecitalPerformer(TenantScopedModel):
    """A performer in a recital."""

    recital = models.ForeignKey(
        RecitalEvent,
        on_delete=models.CASCADE,
        related_name="performers",
    )
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="recital_performances",
    )
    piece_title = models.CharField(max_length=300)
    composer = models.CharField(max_length=200, blank=True)
    performance_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["performance_order"]


class PracticeAnalysis(TenantScopedModel):
    """FEAT-038: AI practice feedback (metadata, actual analysis is frontend)."""

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="practice_analyses",
    )
    recording = models.FileField(
        upload_to=upload_to_analysis, storage=get_private_storage, blank=True, null=True
    )
    recording_url = models.URLField(blank=True)
    analysis_result = models.JSONField(
        default=dict,
        help_text='e.g. {"pitch_accuracy": 85, "rhythm_accuracy": 90, "tempo_stability": 78}',
    )
    feedback = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class RecordingArchive(TenantScopedModel):
    """FEAT-039: Recording archive per student."""

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="recordings",
    )
    title = models.CharField(max_length=300)
    recording = models.FileField(
        upload_to=upload_to_student_recordings, storage=get_private_storage
    )
    instrument = models.CharField(max_length=50, blank=True)
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    duration_seconds = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.student.email}"

    @property
    def is_audio(self):
        import os

        ext = os.path.splitext(self.recording.name)[1].lower()
        return ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]

    @property
    def is_video(self):
        import os

        ext = os.path.splitext(self.recording.name)[1].lower()
        return ext in [".mp4", ".webm", ".mov"]
