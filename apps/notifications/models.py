from django.db import models
from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        ENROLLMENT = "enrollment", "New Enrollment"
        SESSION_REMINDER = "session_reminder", "Session Reminder"
        SESSION_CANCELLED = "session_cancelled", "Session Cancelled"
        ASSIGNMENT_DUE = "assignment_due", "Assignment Due"
        ASSIGNMENT_GRADED = "assignment_graded", "Assignment Graded"
        INVITATION = "invitation", "Academy Invitation"
        GENERAL = "general", "General"

    recipient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications"
    )
    academy = models.ForeignKey(
        "academies.Academy", on_delete=models.CASCADE, null=True, blank=True
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )
    title = models.CharField(max_length=300)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]


class Message(TimeStampedModel):
    """Direct messaging between academy members."""

    sender = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="messages_sent"
    )
    recipient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="messages_received"
    )
    academy = models.ForeignKey(
        "academies.Academy", on_delete=models.CASCADE, related_name="messages"
    )
    subject = models.CharField(max_length=300)
    body = models.TextField()
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender.email} → {self.recipient.email}: {self.subject}"

    @property
    def thread_root(self):
        msg = self
        while msg.parent:
            msg = msg.parent
        return msg


class ChatMessage(TimeStampedModel):
    academy = models.ForeignKey(
        "academies.Academy", on_delete=models.CASCADE, related_name="chat_messages"
    )
    sender = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="sent_messages"
    )
    message = models.TextField()

    class Meta:
        ordering = ["created_at"]
