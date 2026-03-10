from django.db import models
from apps.common.models import TenantScopedModel


class PracticeLog(TenantScopedModel):
    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="practice_logs"
    )
    date = models.DateField()
    duration_minutes = models.PositiveIntegerField()
    instrument = models.CharField(max_length=50)
    pieces_worked_on = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="practice_logs",
    )

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["student", "date"]),
        ]

    def __str__(self):
        return f"{self.student.email} - {self.date} - {self.instrument} ({self.duration_minutes}min)"


class PracticeGoal(TenantScopedModel):
    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="practice_goals"
    )
    weekly_minutes_target = models.PositiveIntegerField(default=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
