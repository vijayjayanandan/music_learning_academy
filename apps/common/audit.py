import logging

from django.db import models

from apps.common.models import TimeStampedModel

logger = logging.getLogger(__name__)


class AuditEvent(TimeStampedModel):
    """Immutable audit log entry for sensitive actions."""

    class Action(models.TextChoices):
        MEMBER_INVITED = "member_invited", "Member Invited"
        MEMBER_ACCEPTED = "member_accepted", "Member Accepted"
        MEMBER_REMOVED = "member_removed", "Member Removed"
        ROLE_CHANGED = "role_changed", "Role Changed"
        COURSE_PUBLISHED = "course_published", "Course Published"
        COURSE_UNPUBLISHED = "course_unpublished", "Course Unpublished"
        SESSION_CANCELLED = "session_cancelled", "Session Cancelled"
        SESSION_RESCHEDULED = "session_rescheduled", "Session Rescheduled"
        REFUND_REQUESTED = "refund_requested", "Refund Requested"
        REFUND_PROCESSED = "refund_processed", "Refund Processed"
        SETTINGS_UPDATED = "settings_updated", "Settings Updated"
        PRICE_CHANGED = "price_changed", "Price Changed"
        SEAT_LIMIT_HIT = "seat_limit_hit", "Seat Limit Reached"

    academy = models.ForeignKey(
        "academies.Academy",
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
        help_text="Null for platform-level events",
    )
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
        help_text="Null for system-triggered actions",
    )
    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    entity_type = models.CharField(
        max_length=50,
        help_text="Model name, e.g. 'membership', 'course', 'session'",
    )
    entity_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="PK of the affected entity",
    )
    description = models.TextField(help_text="Human-readable summary of what happened")
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=36, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["academy", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        actor_str = self.actor.email if self.actor else "System"
        return f"[{self.get_action_display()}] {self.description} (by {actor_str})"


def log_audit_event(
    *,
    action,
    entity_type,
    description,
    academy=None,
    actor=None,
    entity_id=None,
    before_state=None,
    after_state=None,
    request=None,
):
    """Create an audit event. Pass `request` to auto-extract IP and request_id."""
    ip_address = None
    request_id = ""

    if request:
        # Extract IP from X-Forwarded-For or REMOTE_ADDR
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            ip_address = x_forwarded.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        # Extract request_id set by RequestIDMiddleware
        request_id = getattr(request, "request_id", "") or ""

        # Auto-detect academy and actor from request if not provided
        if actor is None and hasattr(request, "user") and request.user.is_authenticated:
            actor = request.user
        if academy is None and hasattr(request, "academy"):
            academy = request.academy

    event = AuditEvent.objects.create(
        academy=academy,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        request_id=request_id,
    )

    logger.info(
        "Audit: %s | %s | %s (id=%s) | %s",
        action,
        actor.email if actor else "system",
        entity_type,
        entity_id,
        description,
    )
    return event
