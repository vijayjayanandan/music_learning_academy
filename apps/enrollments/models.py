from django.db import models
from apps.common.models import TenantScopedModel


class Enrollment(TenantScopedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        DROPPED = "dropped", "Dropped"
        PAUSED = "paused", "Paused"

    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="enrollments"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-enrolled_at"]
        indexes = [
            models.Index(fields=["academy", "student", "status"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"

    @property
    def progress_percent(self):
        total = self.course.lessons.count()
        if total == 0:
            return 0
        completed = self.lesson_progress.filter(is_completed=True).count()
        return int((completed / total) * 100)


class LessonProgress(TenantScopedModel):
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        "courses.Lesson", on_delete=models.CASCADE, related_name="progress_records"
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    practice_time_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("enrollment", "lesson")
        ordering = ["lesson__order"]


class AssignmentSubmission(TenantScopedModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        NEEDS_REVISION = "needs_revision", "Needs Revision"
        APPROVED = "approved", "Approved"

    assignment = models.ForeignKey(
        "courses.PracticeAssignment",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="assignment_submissions"
    )

    text_response = models.TextField(blank=True)
    recording_url = models.URLField(blank=True)
    recording = models.FileField(upload_to="recordings/%Y/%m/", blank=True, null=True)
    file_upload = models.FileField(upload_to="submissions/", blank=True, null=True)
    practice_time_minutes = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED
    )
    instructor_feedback = models.TextField(blank=True)
    grade = models.CharField(max_length=20, blank=True)
    rubric_scores = models.JSONField(default=dict, blank=True, help_text="e.g. {\"tone\": 8, \"rhythm\": 7, \"technique\": 9, \"expression\": 8}")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_submissions",
    )

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_audio_recording(self):
        if not self.recording:
            return False
        import os
        ext = os.path.splitext(self.recording.name)[1].lower()
        return ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]

    @property
    def is_video_recording(self):
        if not self.recording:
            return False
        import os
        ext = os.path.splitext(self.recording.name)[1].lower()
        return ext in [".mp4", ".webm", ".mov"]

    @property
    def recording_size_display(self):
        if not self.recording:
            return ""
        try:
            size = self.recording.size
        except (FileNotFoundError, ValueError):
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
