from django.db import models
from apps.common.models import TenantScopedModel


class LiveSession(TenantScopedModel):
    class SessionStatus(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class SessionType(models.TextChoices):
        ONE_ON_ONE = "one_on_one", "One-on-One Lesson"
        GROUP = "group", "Group Lesson"
        MASTERCLASS = "masterclass", "Masterclass"
        RECITAL = "recital", "Student Recital / Performance"

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="live_sessions",
    )

    instructor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="instructed_sessions",
    )

    scheduled_start = models.DateTimeField(db_index=True)
    scheduled_end = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)

    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        default=SessionType.ONE_ON_ONE,
    )
    max_participants = models.PositiveIntegerField(default=1)

    jitsi_room_name = models.CharField(max_length=255, unique=True)

    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED,
    )

    reminder_24h_sent = models.BooleanField(default=False)
    reminder_1h_sent = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(
        max_length=20, blank=True,
        choices=[("weekly", "Weekly"), ("biweekly", "Bi-weekly"), ("monthly", "Monthly")],
    )
    recurrence_parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recurrence_instances"
    )
    recording_url = models.URLField(blank=True)
    session_notes = models.TextField(blank=True)

    instrument_focus = models.CharField(max_length=50, blank=True)
    topics_covered = models.JSONField(default=list)

    class Meta:
        ordering = ["scheduled_start"]
        indexes = [
            models.Index(fields=["academy", "scheduled_start"]),
            models.Index(fields=["instructor", "scheduled_start"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.scheduled_start.strftime('%Y-%m-%d %H:%M')})"


class SessionAttendance(TenantScopedModel):
    class AttendanceStatus(models.TextChoices):
        REGISTERED = "registered", "Registered"
        ATTENDED = "attended", "Attended"
        ABSENT = "absent", "Absent"

    session = models.ForeignKey(
        LiveSession, on_delete=models.CASCADE, related_name="attendances"
    )
    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="session_attendances"
    )
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.REGISTERED,
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("session", "student")


class SessionNote(TenantScopedModel):
    """Private instructor notes about a student for a session."""

    session = models.ForeignKey(
        LiveSession, on_delete=models.CASCADE, related_name="instructor_notes"
    )
    instructor = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="session_notes_written"
    )
    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="session_notes_about",
        null=True, blank=True,
    )
    content = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note by {self.instructor.email} for session {self.session.title}"
